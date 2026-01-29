"""Sources."""

from __future__ import annotations

import copy
import datetime
import functools
from collections.abc import Iterable, Mapping, Sequence
from typing import Self, TypeAlias

import polars as pl
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from sqlalchemy.orm.interfaces import LoaderOption

from corvic import eorm, op_graph, result, system
from corvic.emodel._base_model import StandardModel
from corvic.emodel._proto_orm_convert import (
    source_delete_orms,
    source_orm_to_proto,
    source_proto_to_orm,
)
from corvic.emodel._resource import Resource, ResourceID
from corvic.table import Table
from corvic_generated.model.v1alpha import models_pb2

SourceID: TypeAlias = eorm.SourceID
RoomID: TypeAlias = eorm.RoomID
PipelineID: TypeAlias = eorm.PipelineID


def foreign_key(
    referenced_source: SourceID | Source, *, is_excluded: bool = False
) -> op_graph.feature_type.ForeignKey:
    match referenced_source:
        case SourceID():
            return op_graph.feature_type.foreign_key(
                referenced_source, is_excluded=is_excluded
            )
        case Source():
            return op_graph.feature_type.foreign_key(
                referenced_source.id, is_excluded=is_excluded
            )


NonDataOp = (
    op_graph.op.UpdateMetadata
    | op_graph.op.SetMetadata
    | op_graph.op.RemoveFromMetadata
    | op_graph.op.UpdateFeatureTypes
)


class Source(StandardModel[SourceID, models_pb2.Source, eorm.Source]):
    """Sources describe how resources should be treated.

    Example:
    >>> Source.from_polars(order_data)
    >>>    .as_dimension_table()
    >>> )
    """

    @classmethod
    def orm_class(cls):
        return eorm.Source

    @classmethod
    def id_class(cls):
        return SourceID

    @classmethod
    async def _orm_to_proto(
        cls, orm_obj: eorm.Source, client: system.Client
    ) -> models_pb2.Source:
        return await source_orm_to_proto(orm_obj, client)

    @classmethod
    async def _proto_to_orm(
        cls, proto_obj: models_pb2.Source, session: eorm.Session
    ) -> result.Ok[eorm.Source] | result.InvalidArgumentError:
        return await source_proto_to_orm(proto_obj, session)

    @classmethod
    async def delete_by_ids(
        cls, ids: Sequence[SourceID], session: eorm.Session
    ) -> result.Ok[None] | result.InvalidArgumentError:
        return await source_delete_orms(ids, session)

    @classmethod
    async def from_id(
        cls,
        *,
        source_id: SourceID,
        session: eorm.Session | None = None,
        client: system.Client,
    ) -> result.Ok[Self] | result.NotFoundError:
        return (
            await cls.load_proto_for(
                obj_id=source_id,
                client=client,
                existing_session=session,
            )
        ).map(
            lambda proto_self: cls.from_proto(
                proto=proto_self,
                client=client,
            )
        )

    @classmethod
    def from_proto(
        cls,
        *,
        proto: models_pb2.Source,
        client: system.Client,
    ) -> Self:
        return cls(
            proto_self=proto,
            client=client,
        )

    @classmethod
    def create(
        cls,
        *,
        name: str,
        room_id: RoomID,
        client: system.Client,
        expected_schema: op_graph.Schema | None = None,
        table_urls: list[str] | None = None,
        num_rows: int | None = None,
    ) -> result.Ok[Self] | result.InvalidArgumentError:
        """Create a new source to be populated later."""
        schema = None
        if expected_schema is not None:
            schema = expected_schema.to_proto()
        proto_source = models_pb2.Source(
            name=name,
            room_id=str(room_id),
            schema=schema,
            table_urls=table_urls,
            num_rows=num_rows,
        )
        return result.Ok(cls(proto_self=proto_source, client=client))

    @classmethod
    def from_resource(
        cls,
        *,
        resource: Resource,
        name: str | None = None,
        room_id: RoomID | None = None,
        client: system.Client,
    ) -> result.Ok[Self] | result.InvalidArgumentError:
        blob = client.storage_manager.blob_from_url(resource.url)
        try:
            with blob.open("rb") as stream:
                lf = pl.scan_parquet(stream)
                pl_schema = lf.collect_schema()
                num_rows = lf.select(pl.len()).collect().item()
        except pl.exceptions.PolarsError as exc:
            return result.InvalidArgumentError.from_(exc)

        return cls.create(
            name=name or resource.name,
            room_id=room_id or resource.room_id,
            client=client,
            expected_schema=op_graph.Schema.from_arrow(
                pl_schema.to_frame().to_arrow().schema
            ),
            table_urls=[resource.url],
            num_rows=num_rows,
        )

    # TODO(Patrick): move this into corvic_test
    @classmethod
    async def from_polars(
        cls,
        *,
        name: str,
        dataframe: pl.DataFrame,
        room_id: RoomID,
        client: system.Client,
    ) -> Self:
        """Create a source from a pl.DataFrame.

        Args:
            name: a unique name for this source
            dataframe: a polars DataFrame
            client: use a particular system.Client instead of the default
            room_id: room to associate this source with. Use the default room if None.
        """
        resource = (
            await Resource.from_polars(
                dataframe=dataframe, client=client, room_id=room_id
            ).commit()
        ).unwrap_or_raise()
        return cls.from_resource(
            resource=resource, name=name, client=client, room_id=room_id
        ).unwrap_or_raise()

    def with_blobs(self, blobs: list[system.Blob], num_rows: int) -> Self:
        proto_self = copy.deepcopy(self.proto_self)
        del proto_self.table_urls[:]
        proto_self.table_urls.extend(blob.url for blob in blobs)
        proto_self.num_rows = num_rows
        return type(self)(proto_self=proto_self, client=self.client)

    def with_schema(self, schema: op_graph.Schema) -> Self:
        proto_self = copy.deepcopy(self.proto_self)
        proto_self.schema.CopyFrom(schema.to_proto())
        return type(self)(proto_self=proto_self, client=self.client)

    def get_source_blobs(self) -> list[system.Blob]:
        return [
            self.client.storage_manager.blob_from_url(blob_url)
            for blob_url in self.proto_self.table_urls
        ]

    def get_source_urls(self) -> list[str]:
        return list(self.proto_self.table_urls)

    def get_schema(self):
        return op_graph.Schema.from_proto(self.proto_self.schema)

    @property
    def num_rows(self):
        return self.proto_self.num_rows

    @classmethod
    def orm_load_options(cls) -> list[LoaderOption]:
        return [
            sa_orm.selectinload(eorm.Source.pipeline_ref).selectinload(
                eorm.PipelineOutput.source
            ),
        ]

    @classmethod
    async def list(
        cls,
        *,
        room_id: RoomID | None = None,
        limit: int | None = None,
        resource_id: ResourceID | None = None,
        created_before: datetime.datetime | None = None,
        ids: Iterable[SourceID] | None = None,
        existing_session: eorm.Session | None = None,
        client: system.Client,
    ) -> result.Ok[list[Self]] | result.NotFoundError | result.InvalidArgumentError:
        """List sources that exist in storage."""
        additional_query_transform = None

        if resource_id is not None:
            match await Resource.from_id(
                resource_id=resource_id,
                client=client,
            ):
                case result.NotFoundError():
                    return result.NotFoundError(
                        "resource not found", resource_id=resource_id
                    )
                case result.Ok(resource):

                    def resource_filter(query: sa.Select[tuple[eorm.Source]]):
                        return query.where(
                            eorm.Source.id.in_(
                                sa.select(eorm.PipelineOutput.source_id)
                                .join(eorm.Pipeline)
                                .join(eorm.PipelineInput)
                                .where(eorm.PipelineInput.resource_id == resource.id)
                            )
                        )

                    additional_query_transform = resource_filter

        match await cls.list_as_proto(
            client=client,
            limit=limit,
            room_id=room_id,
            created_before=created_before,
            ids=ids,
            additional_query_transform=additional_query_transform,
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

    def with_feature_types(
        self, feature_types: Mapping[str, op_graph.FeatureType]
    ) -> result.Ok[Self] | result.InvalidArgumentError:
        """Assign a Feature Type to each column in source.

        Args:
            feature_types: Mapping between column name and feature type

        Example:
        >>> with_feature_types(
        >>>        {
        >>>            "id": corvic.emodel.feature_type.primary_key(),
        >>>            "customer_id": corvic.emodel.feature_type.foreign_key(
        >>>                customer_source.id
        >>>            ),
        >>>        },
        >>>    )
        """
        match self.get_schema().with_feature_types(feature_types):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(new_schema):
                pass
        proto_self = copy.copy(self.proto_self)
        proto_self.schema.CopyFrom(new_schema.to_proto())
        return result.Ok(type(self)(proto_self=proto_self, client=self.client))

    @functools.cached_property
    def table(self):
        schema = self.get_schema()
        return Table.from_ops(
            self.client,
            op_graph.from_staging(
                [
                    blob.name.removeprefix(
                        self.client.storage_manager.tabular_prefix
                    ).removeprefix("/")
                    for blob in self.get_source_blobs()
                ],
                schema.to_arrow(),
                [field.ftype for field in schema],
                self.num_rows,
            ).unwrap_or_raise(),
        )

    @property
    def name(self) -> str:
        return self.proto_self.name

    @property
    def pipeline_id(self) -> PipelineID | None:
        return PipelineID(self.proto_self.pipeline_id) or None
