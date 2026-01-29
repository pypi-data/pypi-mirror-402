from __future__ import annotations

import abc
import contextlib
import dataclasses
import datetime
import functools
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Self, TypeAlias

import pyarrow as pa
import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.orm.interfaces import LoaderOption

from corvic import eorm, op_graph, result, system
from corvic.emodel._base_model import StandardModel
from corvic.emodel._proto_orm_convert import (
    pipeline_delete_orms,
    pipeline_orm_to_proto,
    pipeline_proto_to_orm,
)
from corvic.emodel._source import Source
from corvic.system import Blob
from corvic_generated.model.v1alpha import models_pb2
from corvic_generated.orm.v1 import pipeline_pb2

PipelineID: TypeAlias = eorm.PipelineID
RoomID: TypeAlias = eorm.RoomID


@dataclasses.dataclass(frozen=True)
class PipelineResourceMetrics:
    total_files: int
    total_size: int


class Pipeline(StandardModel[PipelineID, models_pb2.Pipeline, eorm.Pipeline]):
    """Pipelines map resources to sources."""

    @classmethod
    def orm_class(cls):
        return eorm.Pipeline

    @classmethod
    def id_class(cls):
        return PipelineID

    @classmethod
    async def _orm_to_proto(
        cls, orm_obj: eorm.Pipeline, client: system.Client
    ) -> models_pb2.Pipeline:
        return await pipeline_orm_to_proto(orm_obj, client)

    @classmethod
    async def _proto_to_orm(
        cls, proto_obj: models_pb2.Pipeline, session: eorm.Session
    ) -> result.Ok[eorm.Pipeline] | result.InvalidArgumentError:
        return await pipeline_proto_to_orm(proto_obj, session)

    @classmethod
    async def delete_by_ids(
        cls, ids: Sequence[PipelineID], session: eorm.Session
    ) -> result.Ok[None] | result.InvalidArgumentError:
        return await pipeline_delete_orms(ids, session)

    @classmethod
    def _create(
        cls,
        *,
        pipeline_name: str,
        description: str,
        room_id: RoomID,
        source_outputs: dict[str, Source],
        transformation: pipeline_pb2.PipelineTransformation,
        client: system.Client,
    ) -> Self:
        proto_pipeline = models_pb2.Pipeline(
            name=pipeline_name,
            room_id=str(room_id),
            source_outputs={
                output_name: source.proto_self
                for output_name, source in source_outputs.items()
            },
            pipeline_transformation=transformation,
            description=description,
        )
        return cls(proto_self=proto_pipeline, client=client)

    @classmethod
    def from_proto(
        cls, *, proto: models_pb2.Pipeline, client: system.Client
    ) -> SpecificPipeline:
        if proto.pipeline_transformation.HasField("ocr_pdf"):
            return OcrPdfsPipeline(proto_self=proto, client=client)

        if proto.pipeline_transformation.HasField("chunk_pdf"):
            return ChunkPdfsPipeline(proto_self=proto, client=client)

        if proto.pipeline_transformation.HasField("sanitize_parquet"):
            return SanitizeParquetPipeline(proto_self=proto, client=client)

        if proto.pipeline_transformation.HasField("table_function_passthrough"):
            return TableFunctionPassthroughPipeline(proto_self=proto, client=client)

        if proto.pipeline_transformation.HasField(
            "table_function_structured_passthrough"
        ):
            return TableFunctionStructuredPassthroughPipeline(
                proto_self=proto, client=client
            )

        if proto.pipeline_transformation.HasField("table_function_ingestion"):
            return TableFunctionIngestionPipeline(proto_self=proto, client=client)

        return UnknownTransformationPipeline(proto_self=proto, client=client)

    @classmethod
    async def from_id(
        cls,
        *,
        pipeline_id: PipelineID,
        session: eorm.Session | None = None,
        client: system.Client,
    ) -> result.Ok[SpecificPipeline] | result.NotFoundError:
        match await cls.list_as_proto(
            limit=1, ids=[pipeline_id], client=client, existing_session=session
        ):
            case result.Ok(proto_list):
                return (
                    result.Ok(
                        cls.from_proto(
                            proto=proto_list[0],
                            client=client,
                        )
                    )
                    if proto_list
                    else result.NotFoundError(
                        "object with given id does not exist", id=pipeline_id
                    )
                )
            case result.NotFoundError() as err:
                return err
            case result.InvalidArgumentError() as err:
                return result.NotFoundError.from_(err)

    @classmethod
    def orm_load_options(cls) -> list[LoaderOption]:
        return [
            sa_orm.selectinload(eorm.Pipeline.outputs)
            .selectinload(eorm.PipelineOutput.source)
            .selectinload(eorm.Source.pipeline_ref),
        ]

    @classmethod
    async def list(
        cls,
        *,
        limit: int | None = None,
        room_id: RoomID | None = None,
        created_before: datetime.datetime | None = None,
        ids: Iterable[PipelineID] | None = None,
        existing_session: eorm.Session | None = None,
        client: system.Client,
    ) -> (
        result.Ok[list[SpecificPipeline]]
        | result.InvalidArgumentError
        | result.NotFoundError
    ):
        match await cls.list_as_proto(
            client=client,
            limit=limit,
            room_id=room_id,
            created_before=created_before,
            ids=ids,
            existing_session=existing_session,
        ):
            case result.NotFoundError() | result.InvalidArgumentError() as err:
                return err
            case result.Ok(protos):
                return result.Ok(
                    [
                        cls.from_proto(
                            proto=proto,
                            client=client,
                        )
                        for proto in protos
                    ]
                )

    @classmethod
    async def get_resource_metrics(
        cls,
        pipeline_id: PipelineID,
        client: system.Client,
        existing_session: eorm.Session | None = None,
    ) -> PipelineResourceMetrics:
        query = (
            sa.select(
                sa.func.count(eorm.Resource.id).label("total_files"),
                sa.func.coalesce(sa.func.sum(eorm.Resource.size), 0).label(
                    "total_size"
                ),
            )
            .select_from(
                sa.join(
                    eorm.Resource,
                    eorm.PipelineInput,
                    eorm.Resource.id == eorm.PipelineInput.resource_id,
                )
            )
            .where(eorm.PipelineInput.pipeline_id == pipeline_id)
        )
        async with (
            contextlib.nullcontext(existing_session)
            if existing_session
            else eorm.Session(client.sa_engine) as session
        ):
            query_result = await session.execute(query)
            row = query_result.first()
            if row is None:
                return PipelineResourceMetrics(total_files=0, total_size=0)
            total_files = int(row.total_files) if row.total_files is not None else 0
            total_size = int(row.total_size) if row.total_size is not None else 0
            return PipelineResourceMetrics(
                total_files=total_files, total_size=total_size
            )

    @property
    def name(self):
        return self.proto_self.name

    @property
    def description(self):
        return self.proto_self.description

    @functools.cached_property
    def outputs(self) -> Mapping[str, Source]:
        return {
            name: Source(
                proto_self=proto_source,
                client=self.client,
            )
            for name, proto_source in self.proto_self.source_outputs.items()
        }

    @abc.abstractmethod
    def choose_blob_for_upload(self) -> Blob:
        """Choose a blob to store a new resource at for this pipeline type."""


class UnknownTransformationPipeline(Pipeline):
    """A pipeline that this version of the code doesn't know what to do with."""

    def choose_blob_for_upload(self) -> Blob:
        raise result.InvalidArgumentError("unknown pipeline type")


async def _commit_or_add_to_session(source: Source, session: eorm.Session | None):
    if session is None:
        return await source.commit()
    return await source.add_to_session(session, return_result=True)


class ChunkPdfsPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        source_name: str,
        description: str = "",
        room_id: RoomID,
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a pipeline for parsing PDFs into text chunks."""
        match Source.create(
            name=source_name,
            client=client,
            room_id=room_id,
            expected_schema=op_graph.Schema(
                [
                    op_graph.Field(
                        "id", pa.large_string(), op_graph.feature_type.primary_key()
                    ),
                    op_graph.Field(
                        "text", pa.large_string(), op_graph.feature_type.text()
                    ),
                    op_graph.Field(
                        "metadata_json", pa.large_string(), op_graph.feature_type.text()
                    ),
                    op_graph.Field("index", pa.int32(), op_graph.feature_type.text()),
                ]
            ),
        ):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(source):
                pass
        match await _commit_or_add_to_session(source, session):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(source):
                pass

        output_name = f"output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={output_name: source},
                transformation=pipeline_pb2.PipelineTransformation(
                    chunk_pdf=pipeline_pb2.ChunkPdfPipelineTransformation(
                        output_name=output_name
                    )
                ),
                client=client,
            )
        )

    @property
    def output_name(self):
        return self.proto_self.pipeline_transformation.chunk_pdf.output_name

    @property
    def output_source(self):
        return self.outputs[self.output_name]

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_unstructured_blob(self.room_id)


class OcrPdfsPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        text_source_name: str,
        relationship_source_name: str,
        image_source_name: str,
        description: str = "",
        room_id: RoomID,
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a pipeline for using OCR to process PDFs into structured sources."""
        match await create_parse_text_source(
            text_source_name, client, room_id, session=session
        ):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(text_source):
                pass
        match await create_parse_relationship_source(
            relationship_source_name, client, text_source, session=session
        ):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(relationship_source):
                pass
        match await create_parse_image_source(
            image_source_name, client, text_source, session=session
        ):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(image_source):
                pass

        text_output_name = f"text_output-{uuid.uuid4()}"
        relationship_output_name = f"relationship_output-{uuid.uuid4()}"
        image_output_name = f"image_output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={
                    text_output_name: text_source,
                    relationship_output_name: relationship_source,
                    image_output_name: image_source,
                },
                transformation=pipeline_pb2.PipelineTransformation(
                    ocr_pdf=pipeline_pb2.OcrPdfPipelineTransformation(
                        text_output_name=text_output_name,
                        relationship_output_name=relationship_output_name,
                        image_output_name=image_output_name,
                    )
                ),
                client=client,
            )
        )

    @property
    def text_output_name(self):
        return self.proto_self.pipeline_transformation.ocr_pdf.text_output_name

    @property
    def relationship_output_name(self):
        return self.proto_self.pipeline_transformation.ocr_pdf.relationship_output_name

    @property
    def image_output_name(self):
        return self.proto_self.pipeline_transformation.ocr_pdf.image_output_name

    @property
    def text_output_source(self):
        return self.outputs[self.text_output_name]

    @property
    def relationship_output_source(self):
        return self.outputs[self.relationship_output_name]

    @property
    def image_output_source(self):
        return self.outputs[self.image_output_name]

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_unstructured_blob(self.room_id)


class SanitizeParquetPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        source_name: str,
        room_id: RoomID,
        description: str = "",
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a pipeline for parsing PDFs into text chunks."""
        match Source.create(name=source_name, client=client, room_id=room_id):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(source):
                pass
        match await _commit_or_add_to_session(source, session):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(source):
                pass

        output_name = f"output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={output_name: source},
                transformation=pipeline_pb2.PipelineTransformation(
                    sanitize_parquet=pipeline_pb2.SanitizeParquetPipelineTransformation(
                        output_name=output_name
                    )
                ),
                client=client,
            )
        )

    @property
    def output_name(self):
        return self.proto_self.pipeline_transformation.sanitize_parquet.output_name

    @property
    def output_source(self):
        return self.outputs[self.output_name]

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_tabular_blob(self.room_id)


class TableFunctionPassthroughPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        source_name: str,
        room_id: RoomID,
        description: str = "",
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a no-op pipeline that exists to collect resources."""
        match Source.create(name=source_name, client=client, room_id=room_id):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(source):
                pass
        match await _commit_or_add_to_session(source, session):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(source):
                pass

        output_name = f"output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={output_name: source},
                transformation=pipeline_pb2.PipelineTransformation(
                    table_function_passthrough=pipeline_pb2.TableFunctionPassthroughPipelineTransformation()
                ),
                client=client,
            )
        )

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_tabular_blob(self.room_id)


class TableFunctionStructuredPassthroughPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        source_name: str,
        room_id: RoomID,
        description: str = "",
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a no-op pipeline that exists to collect resources."""
        match Source.create(name=source_name, client=client, room_id=room_id):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(source):
                pass
        match await _commit_or_add_to_session(source, session):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(source):
                pass

        output_name = f"output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={output_name: source},
                transformation=pipeline_pb2.PipelineTransformation(
                    table_function_structured_passthrough=pipeline_pb2.TableFunctionStructuredPassthroughPipelineTransformation()
                ),
                client=client,
            )
        )

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_tabular_blob(self.room_id)


class TableFunctionIngestionPipeline(Pipeline):
    @classmethod
    async def create(
        cls,
        *,
        pipeline_name: str,
        source_name: str,
        room_id: RoomID,
        description: str = "",
        client: system.Client,
        session: eorm.Session | None = None,
    ) -> (
        result.Ok[Self]
        | result.InvalidArgumentError
        | result.UnavailableError
        | result.AlreadyExistsError
    ):
        """Create a no-op pipeline that exists to collect resources."""
        match Source.create(name=source_name, client=client, room_id=room_id):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(source):
                pass
        match await _commit_or_add_to_session(source, session):
            case (
                result.UnavailableError()
                | result.InvalidArgumentError()
                | result.AlreadyExistsError() as err
            ):
                return err
            case result.Ok(source):
                pass

        output_name = f"output-{uuid.uuid4()}"
        return result.Ok(
            cls._create(
                pipeline_name=pipeline_name,
                description=description,
                room_id=room_id,
                source_outputs={output_name: source},
                transformation=pipeline_pb2.PipelineTransformation(
                    table_function_ingestion=pipeline_pb2.TableFunctionIngestionPipelineTransformation()
                ),
                client=client,
            )
        )

    def choose_blob_for_upload(self) -> Blob:
        return self.client.storage_manager.make_unstructured_blob(self.room_id)


SpecificPipeline: TypeAlias = (
    ChunkPdfsPipeline
    | OcrPdfsPipeline
    | SanitizeParquetPipeline
    | UnknownTransformationPipeline
    | TableFunctionPassthroughPipeline
    | TableFunctionStructuredPassthroughPipeline
    | TableFunctionIngestionPipeline
)


async def create_parse_text_source(
    text_source_name: str,
    client: system.Client,
    room_id: eorm.RoomID,
    *,
    session: eorm.Session | None,
):
    match Source.create(
        name=text_source_name,
        client=client,
        room_id=room_id,
        expected_schema=op_graph.Schema(
            [
                op_graph.Field(
                    "id", pa.large_string(), op_graph.feature_type.primary_key()
                ),
                op_graph.Field(
                    "content", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "document", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "type", pa.large_string(), op_graph.feature_type.categorical()
                ),
                op_graph.Field(
                    "title", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "resource_id", pa.large_string(), op_graph.feature_type.identifier()
                ),
                op_graph.Field(
                    "page_number", pa.int64(), op_graph.feature_type.numerical()
                ),
                op_graph.Field(
                    "bbox",
                    pa.struct(
                        [
                            pa.field("x1", pa.float64()),
                            pa.field("y1", pa.float64()),
                            pa.field("x2", pa.float64()),
                            pa.field("y2", pa.float64()),
                        ]
                    ),
                    op_graph.feature_type.embedding(),
                ),
                op_graph.Field(
                    "created_at", pa.date32(), op_graph.feature_type.timestamp()
                ),
            ]
        ),
    ):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok(text_source):
            pass
    return await _commit_or_add_to_session(text_source, session)


async def create_parse_relationship_source(
    relationship_source_name: str,
    client: system.Client,
    text_source: Source,
    *,
    session: eorm.Session | None,
):
    match Source.create(
        name=relationship_source_name,
        client=client,
        room_id=text_source.room_id,
        expected_schema=op_graph.Schema(
            [
                op_graph.Field(
                    "from",
                    pa.large_string(),
                    op_graph.feature_type.foreign_key(text_source.id),
                ),
                op_graph.Field(
                    "to",
                    pa.large_string(),
                    op_graph.feature_type.foreign_key(text_source.id),
                ),
                op_graph.Field(
                    "type", pa.large_string(), op_graph.feature_type.categorical()
                ),
            ]
        ),
    ):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok(relationship_source):
            pass
    return await _commit_or_add_to_session(relationship_source, session)


async def create_parse_image_source(
    image_source_name: str,
    client: system.Client,
    text_source: Source,
    *,
    session: eorm.Session | None,
):
    match Source.create(
        name=image_source_name,
        client=client,
        room_id=text_source.room_id,
        expected_schema=op_graph.Schema(
            [
                op_graph.Field(
                    "id", pa.large_string(), op_graph.feature_type.primary_key()
                ),
                op_graph.Field(
                    "content", pa.large_binary(), op_graph.feature_type.image()
                ),
                op_graph.Field(
                    "description", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "document", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "title", pa.large_string(), op_graph.feature_type.text()
                ),
                op_graph.Field(
                    "text_id",
                    pa.large_string(),
                    op_graph.feature_type.foreign_key(text_source.id),
                ),
                op_graph.Field(
                    "resource_id", pa.large_string(), op_graph.feature_type.identifier()
                ),
                op_graph.Field(
                    "page_number", pa.int64(), op_graph.feature_type.numerical()
                ),
                op_graph.Field(
                    "bbox",
                    pa.struct(
                        [
                            pa.field("x1", pa.float64()),
                            pa.field("y1", pa.float64()),
                            pa.field("x2", pa.float64()),
                            pa.field("y2", pa.float64()),
                        ]
                    ),
                    op_graph.feature_type.embedding(),
                ),
                op_graph.Field(
                    "created_at", pa.date32(), op_graph.feature_type.timestamp()
                ),
            ]
        ),
    ):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok(image_source):
            pass
    return await _commit_or_add_to_session(image_source, session)
