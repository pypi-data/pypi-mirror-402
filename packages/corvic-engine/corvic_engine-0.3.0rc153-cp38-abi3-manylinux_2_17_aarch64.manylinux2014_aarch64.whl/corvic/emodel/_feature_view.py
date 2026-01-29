"""Feature views."""

from __future__ import annotations

import copy
import dataclasses
import datetime
import functools
import uuid
from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from typing import Any, Final, TypeAlias

import pyarrow as pa
from google.protobuf import struct_pb2
from more_itertools import flatten
from sqlalchemy import orm as sa_orm
from sqlalchemy.orm.interfaces import LoaderOption

from corvic import eorm, op_graph, result, system, transfer
from corvic.emodel._base_model import StandardModel
from corvic.emodel._proto_orm_convert import (
    feature_view_delete_orms,
    feature_view_orm_to_proto,
    feature_view_proto_to_orm,
)
from corvic.emodel._source import Source, SourceID
from corvic.table import (
    DataclassAsTypedMetadataMixin,
    RowFilter,
    Schema,
    Table,
    feature_type,
    row_filter,
)
from corvic_generated.model.v1alpha import models_pb2
from corvic_generated.orm.v1 import feature_view_pb2

FeatureViewID: TypeAlias = eorm.FeatureViewID
FeatureViewSourceID: TypeAlias = eorm.FeatureViewSourceID
RoomID: TypeAlias = eorm.RoomID


class Column:
    """A logical representation of a column to use in filter predicates.

    Columns are identified by name.
    """

    _column_name: Final[str]
    _dtype: Final[pa.DataType]

    def __init__(self, column_name: str, dtype: pa.DataType):
        """Creates a new instance of Column.

        Args:
            column_name: Name of the column
            dtype: Data type of the column
        """
        self._column_name = column_name
        self._dtype = dtype

    def eq(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is equal to a value."""
        return row_filter.eq(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def ne(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is not equal to a value."""
        return row_filter.ne(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def gt(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is greater than a value."""
        return row_filter.gt(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def lt(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is less than a value."""
        return row_filter.lt(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def ge(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is greater than or equal to a value."""
        return row_filter.ge(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def le(self, value: struct_pb2.Value | float | str | bool) -> RowFilter:  # noqa: FBT001
        """Return rows where column is less than or equal to a value."""
        return row_filter.le(
            column_name=self._column_name, literal=value, dtype=self._dtype
        )

    def in_(self, value: list[struct_pb2.Value | float | str | bool]) -> RowFilter:
        """Return rows where column matches any in a list of values."""
        return row_filter.in_(
            column_name=self._column_name, literals=value, dtype=self._dtype
        )

    def not_in(self, value: list[struct_pb2.Value | float | str | bool]) -> RowFilter:
        """Return rows where column does not match any in a list of values."""
        return row_filter.not_in(
            column_name=self._column_name, literals=value, dtype=self._dtype
        )


@dataclasses.dataclass(frozen=True)
class FkeyRelationship:
    """A foreign key relationship between sources."""

    proto_self: feature_view_pb2.ForeignKeyRelationship

    @property
    def source_with_fkey(self) -> SourceID:
        return SourceID(self.proto_self.foreign_key_having_source_id)

    @property
    def fkey_column_name(self) -> str:
        return self.proto_self.foreign_key_column_name

    @property
    def referenced_source(self) -> SourceID:
        return SourceID(self.proto_self.referenced_source_id)

    @property
    def pkey_column_name(self) -> str:
        return self.proto_self.primary_key_column_name


@dataclasses.dataclass(frozen=True)
class Relationship:
    """A connection between two sources within a FeatureView."""

    proto_self: feature_view_pb2.FeatureViewRelationship
    feature_view: FeatureView

    @property
    def start_source_id(self) -> SourceID:
        return SourceID(self.proto_self.start_source_id)

    @property
    def end_source_id(self) -> SourceID:
        return SourceID(self.proto_self.end_source_id)

    @property
    def start_fv_source(self) -> FeatureViewSource:
        return self.feature_view.source_id_to_feature_view_source[self.start_source_id]

    @property
    def end_fv_source(self) -> FeatureViewSource:
        return self.feature_view.source_id_to_feature_view_source[self.end_source_id]

    @property
    def fkey_relationship(self) -> FkeyRelationship:
        return FkeyRelationship(proto_self=self.proto_self.foreign_key_relationship)

    @property
    def start_source(self) -> Source:
        return self.start_fv_source.source

    @property
    def end_source(self) -> Source:
        return self.end_fv_source.source

    @property
    def from_column_name(self) -> str:
        if self.start_source_id == self.fkey_relationship.source_with_fkey:
            return self.fkey_relationship.fkey_column_name
        return self.fkey_relationship.pkey_column_name

    @property
    def to_column_name(self) -> str:
        if (
            self.end_source_id == self.fkey_relationship.source_with_fkey
            and self.fkey_relationship.source_with_fkey
            != self.fkey_relationship.referenced_source
        ):
            return self.fkey_relationship.fkey_column_name
        return self.fkey_relationship.pkey_column_name

    @functools.cached_property
    def new_column_name(self) -> str:
        return f"join-{uuid.uuid4()}"

    @functools.cached_property
    def end_surrogate_column_name(self) -> str | None:
        return (
            f"end-surrogate-{uuid.uuid4()}"
            if self.end_fv_source.table.schema.get_surrogate_key()
            else None
        )

    def joined_table(self) -> Table:
        end_renames = {self.to_column_name: self.new_column_name}
        if self.end_surrogate_column_name is not None:
            end_surrogate_key = self.end_fv_source.table.schema.get_surrogate_key()
            if not end_surrogate_key:
                raise result.InternalError("end surrogate key not set")
            end_renames[end_surrogate_key.name] = self.end_surrogate_column_name
        start_table = self.start_fv_source.table.rename_columns(
            {self.from_column_name: self.new_column_name}
        )
        end_table = self.end_fv_source.table.rename_columns(end_renames)

        return start_table.join(
            end_table,
            left_on=self.new_column_name,
            right_on=self.new_column_name,
            how="inner",
        )

    async def edge_list(self) -> AsyncIterable[tuple[Any, Any]]:
        """Test function not updated for surrogate key use."""
        start_pk = self.start_fv_source.table.schema.get_primary_key()
        end_pk = self.end_fv_source.table.schema.get_primary_key()
        if not start_pk or not end_pk:
            raise result.InvalidArgumentError(
                "both sources must have a primary key to render edge list"
            )
        if self.from_column_name == start_pk.name:
            result_columns = (self.new_column_name, end_pk.name)
        else:
            result_columns = (start_pk.name, self.new_column_name)
        res = self.joined_table().select(result_columns)
        for batch in (
            await res.to_polars(room_id=self.start_source.room_id)
        ).unwrap_or_raise():
            for row in batch.rows(named=True):
                yield (row[result_columns[0]], row[result_columns[1]])


@dataclasses.dataclass(frozen=True)
class ColumnRename:
    """A mapping from old column name to new column name."""

    initial_column_name: str
    final_column_name: str


@dataclasses.dataclass
class EndColumn:
    initial_primary_key_end: str
    initial_surrogate_key_end: str | None


class RelationshipPath:
    """A path between two sources within a FeatureView.

    Provides datastructures and helper functions for manipulating paths.
    """

    def __init__(self, path: list[Relationship]):
        self.path = path
        self._column_renames = dict[str, str]()

    def generate_join_table(self) -> Table:
        self._column_renames = dict[str, str]()
        table = self._start_table()
        for i, rel in enumerate(self.path[1:]):
            latest_from_name = self._find_latest_name(rel.from_column_name)
            end_renames = {rel.to_column_name: rel.new_column_name}
            if i == len(self.path[1:]) - 1 and self.has_surrogate_keys:
                end_surrogate_key = rel.end_fv_source.table.schema.get_surrogate_key()
                if not end_surrogate_key:
                    raise result.InternalError("end surrogate key not set")
                end_renames[end_surrogate_key.name] = self.surrogate_end_column
            table = table.rename_columns({latest_from_name: rel.new_column_name}).join(
                rel.end_fv_source.table.rename_columns(end_renames),
                left_on=rel.new_column_name,
                right_on=rel.new_column_name,
                suffix=f"_{rel.end_fv_source.source.name}",
            )
            self._update_renames(rel)
        return self._end_table(table)

    def _start_table(self) -> Table:
        table = self.path[0].joined_table()
        self._column_renames[self.initial_start_column] = self.final_start_column
        self._update_renames(self.path[0])
        start_renames = {self.initial_start_column: self.final_start_column}
        if self.has_surrogate_keys:
            start_surrogate_key = self.path[
                0
            ].start_fv_source.table.schema.get_surrogate_key()
            if not start_surrogate_key:
                raise result.InternalError("start surrogate key not set")
            start_renames[start_surrogate_key.name] = self.surrogate_start_column
        return table.rename_columns(start_renames)

    def _end_table(self, table: Table) -> Table:
        column_names: list[str] = [column.name for column in table.schema]

        if (
            self.initial_end_column.initial_primary_key_end not in column_names
            and f"{self.initial_end_column.initial_primary_key_end}_right"
            in column_names
        ):
            self._column_renames[
                f"{self.initial_end_column.initial_primary_key_end}_right"
            ] = self.final_end_column
            table = table.rename_columns(
                {
                    f"{self.initial_end_column.initial_primary_key_end}_right": self.final_end_column  # noqa: E501
                }
            )
        else:
            self._column_renames[self.initial_end_column.initial_primary_key_end] = (
                self.final_end_column
            )
            table = table.rename_columns(
                {self.initial_end_column.initial_primary_key_end: self.final_end_column}
            )

        if (
            self.initial_end_column.initial_surrogate_key_end
            and self.surrogate_end_column not in column_names
        ):
            table = table.rename_columns(
                {
                    self.initial_end_column.initial_surrogate_key_end: self.surrogate_end_column  # noqa: E501
                }
            )
        return table

    def _update_renames(self, new_rel: Relationship):
        self._column_renames[new_rel.from_column_name] = new_rel.new_column_name
        self._column_renames[new_rel.to_column_name] = new_rel.new_column_name

    def _find_latest_name(self, name: str):
        while name in self._column_renames:
            new_name = self._column_renames[name]
            if new_name == name:
                break
            name = new_name
        return name

    @functools.cached_property
    def relationship_path(self) -> list[str]:
        return [
            self.path[0].start_source.name,
            *(p.end_source.name for p in self.path),
        ]

    @property
    def has_surrogate_keys(self):
        return (
            self.path[0].start_fv_source.table.schema.get_surrogate_key() is not None
            and self.path[-1].end_fv_source.table.schema.get_surrogate_key() is not None
        )

    @property
    def start_source_name(self):
        return self.path[0].start_fv_source.source.name

    @property
    def end_source_name(self):
        return self.path[-1].end_fv_source.source.name

    @functools.cached_property
    def initial_start_column(self) -> str:
        if not self.path:
            raise result.InvalidArgumentError("must provide at least one relationship")
        if (
            self.path[0].fkey_relationship.source_with_fkey
            == self.path[0].start_source.id
        ):
            start_field = self.path[0].start_fv_source.table.schema.get_primary_key()
            if not start_field:
                raise result.InvalidArgumentError(
                    "configuration requires column to have a primary key",
                    source_name=self.path[0].start_fv_source.source.name,
                )
            start_col = start_field.name
        else:
            start_col = self.path[0].new_column_name
        return start_col

    @functools.cached_property
    def initial_end_column(self) -> EndColumn:
        if not self.path:
            raise result.InvalidArgumentError("must provide at least one relationship")
        if (
            self.path[-1].fkey_relationship.source_with_fkey
            == self.path[-1].end_source.id
            and self.path[-1].fkey_relationship.source_with_fkey
            != self.path[-1].fkey_relationship.referenced_source
        ):
            end_field = self.path[-1].end_fv_source.table.schema.get_primary_key()
            if not end_field:
                raise result.InvalidArgumentError(
                    "configuration requires source to have primary key",
                    source_name=self.path[-1].end_fv_source.source.name,
                )
            end_col = end_field.name
        else:
            end_col = self.path[-1].new_column_name
        return EndColumn(
            initial_primary_key_end=end_col,
            initial_surrogate_key_end=self.path[-1].end_surrogate_column_name,
        )

    @functools.cached_property
    def final_start_column(self) -> str:
        return f"start-{uuid.uuid4()}"

    @functools.cached_property
    def final_end_column(self) -> str:
        return f"end-{uuid.uuid4()}"

    @functools.cached_property
    def surrogate_start_column(self) -> str:
        return (
            f"surrogate-start-{uuid.uuid4()}"
            if self.has_surrogate_keys
            else self.final_start_column
        )

    @functools.cached_property
    def surrogate_end_column(self) -> str:
        return (
            f"surrogate-end-{uuid.uuid4()}"
            if self.has_surrogate_keys
            else self.final_end_column
        )


class FeatureViewSource(
    transfer.UsesOrmID[FeatureViewSourceID, models_pb2.FeatureViewSource]
):
    """A table from a source with some extra operations defined by a feature view."""

    @classmethod
    def id_class(cls):
        return FeatureViewSourceID

    @classmethod
    def create(
        cls,
        table: Table,
        source: Source,
        *,
        drop_disconnected: bool,
        room_id: eorm.RoomID,
    ):
        return cls(
            proto_self=models_pb2.FeatureViewSource(
                source=source.proto_self,
                table_op_graph=table.op_graph.to_proto(),
                drop_disconnected=drop_disconnected,
                room_id=str(room_id),
            ),
            client=source.client,
        )

    def with_table(self, table: Table | op_graph.Op) -> FeatureViewSource:
        if isinstance(table, Table):
            table = table.op_graph
        proto_self = copy.deepcopy(self.proto_self)
        proto_self.table_op_graph.CopyFrom(table.to_proto())
        return FeatureViewSource(
            proto_self=proto_self,
            client=self.client,
        )

    @functools.cached_property
    def source(self):
        return Source(
            proto_self=self.proto_self.source,
            client=self.client,
        )

    @functools.cached_property
    def table(self):
        return Table.from_ops(
            op=op_graph.op.from_proto(self.proto_self.table_op_graph),
            client=self.client,
        )


@dataclasses.dataclass(kw_only=True)
class FeatureViewEdgeTableMetadata(DataclassAsTypedMetadataMixin):
    """Metadata attached to edge tables; notes important columns and provenance."""

    @classmethod
    def metadata_key(cls):
        return "space-edge_table-metadata"

    start_source_name: str
    end_source_name: str
    start_source_column_name: str
    end_source_column_name: str


@dataclasses.dataclass(kw_only=True)
class FeatureViewRelationshipsMetadata(DataclassAsTypedMetadataMixin):
    """Metadata attached to relationship path for feature view edge tables."""

    @classmethod
    def metadata_key(cls):
        return "space-relationships-metadata"

    relationship_path: list[str]


@dataclasses.dataclass(kw_only=True)
class FeatureViewSourceColumnRenames(DataclassAsTypedMetadataMixin):
    """Metadata attached to feature space source tables to remember renamed columns."""

    @classmethod
    def metadata_key(cls):
        return "space_source-column_renames-metadata"

    column_renames: dict[str, str]


@dataclasses.dataclass(kw_only=True)
class FeatureViewSourceRowIDs(DataclassAsTypedMetadataMixin):
    """Metadata attached to feature space source tables to remember a row id column."""

    @classmethod
    def metadata_key(cls):
        return "space_source-column_row_id-metadata"

    row_id_column: str


class FeatureView(
    StandardModel[FeatureViewID, models_pb2.FeatureView, eorm.FeatureView]
):
    """FeatureViews describe how Sources should be modeled to create a feature space.

    Example:
    >>> FeatureView.create()
    >>>    .with_source(
    >>>        customer_source,
    >>>        row_filter=Column("customer_name").eq("Denis").or_(Column("id").lt(3)),
    >>>        drop_disconnected=True,
    >>>    )
    >>>    .with_source(
    >>>        order_source,
    >>>        include_columns=["id", "ordered_item"],
    >>>    )
    >>>    .wth_relationship(customer_source, order_source, directional=False)
    """

    @classmethod
    def orm_class(cls):
        return eorm.FeatureView

    @classmethod
    def id_class(cls):
        return FeatureViewID

    @classmethod
    async def _orm_to_proto(
        cls, orm_obj: eorm.FeatureView, client: system.Client
    ) -> models_pb2.FeatureView:
        return await feature_view_orm_to_proto(orm_obj, client)

    @classmethod
    async def _proto_to_orm(
        cls, proto_obj: models_pb2.FeatureView, session: eorm.Session
    ) -> result.Ok[eorm.FeatureView] | result.InvalidArgumentError:
        return await feature_view_proto_to_orm(proto_obj, session)

    @classmethod
    async def delete_by_ids(
        cls, ids: Sequence[FeatureViewID], session: eorm.Session
    ) -> result.Ok[None] | result.InvalidArgumentError:
        return await feature_view_delete_orms(ids, session)

    @classmethod
    async def from_id(
        cls,
        *,
        feature_view_id: FeatureViewID,
        session: eorm.Session | None = None,
        client: system.Client,
    ) -> result.Ok[FeatureView] | result.NotFoundError:
        return (
            await cls.load_proto_for(
                obj_id=feature_view_id,
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
        proto: models_pb2.FeatureView,
        client: system.Client,
    ) -> FeatureView:
        return cls(
            proto_self=proto,
            client=client,
        )

    @classmethod
    def orm_load_options(cls) -> list[LoaderOption]:
        return [
            sa_orm.selectinload(eorm.FeatureView.feature_view_sources)
            .selectinload(eorm.FeatureViewSource.source)
            .selectinload(eorm.Source.pipeline_ref)
            .selectinload(eorm.PipelineOutput.source)
        ]

    @classmethod
    async def list(
        cls,
        *,
        room_id: RoomID | None = None,
        limit: int | None = None,
        created_before: datetime.datetime | None = None,
        ids: Iterable[FeatureViewID] | None = None,
        existing_session: eorm.Session | None = None,
        client: system.Client,
    ) -> (
        result.Ok[list[FeatureView]]
        | result.NotFoundError
        | result.InvalidArgumentError
    ):
        """List resources."""
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
                pass
        return result.Ok(
            [cls.from_proto(proto=proto, client=client) for proto in protos]
        )

    @property
    def source_ids(self):
        return [fv_source.source.id for fv_source in self.feature_view_sources]

    @property
    def description(self):
        return self.proto_self.description

    @functools.cached_property
    def relationships(self) -> Sequence[Relationship]:
        return [
            Relationship(proto_rel, self)
            for proto_rel in self.proto_self.feature_view_output.relationships
        ]

    @functools.cached_property
    def feature_view_sources(self) -> Sequence[FeatureViewSource]:
        return [
            FeatureViewSource(proto_self=fvs, client=self.client)
            for fvs in self.proto_self.feature_view_sources
        ]

    @functools.cached_property
    def output_source_ids(self) -> set[SourceID]:
        return {
            SourceID(output_source.source_id)
            for output_source in self.proto_self.feature_view_output.output_sources
        }

    @functools.cached_property
    def output_sources(self) -> Sequence[Source]:
        return [
            self.source_id_to_feature_view_source[source_id].source
            for source_id in self.output_source_ids
        ]

    @functools.cached_property
    def source_id_to_feature_view_source(self) -> Mapping[SourceID, FeatureViewSource]:
        return {fvs.source.id: fvs for fvs in self.feature_view_sources}

    @property
    def name(self) -> str:
        return self.proto_self.name

    def _get_feature_view_source(
        self, source: Source
    ) -> (
        result.Ok[FeatureViewSource]
        | result.NotFoundError
        | result.InvalidArgumentError
    ):
        val = self.source_id_to_feature_view_source.get(source.id)
        if not val:
            return result.InvalidArgumentError(
                "feature view does not reference source with given id",
                given_id=source.id,
            )
        return result.Ok(val)

    @functools.cached_property
    def sources(self) -> list[Source]:
        return [
            feature_view_source.source
            for feature_view_source in self.source_id_to_feature_view_source.values()
        ]

    @functools.cached_property
    def paths_between_outputs(self) -> list[RelationshipPath]:
        paths_between_outputs = list(
            flatten(
                self._calculate_paths_to_outputs(output, self.relationships)
                for output in self.output_source_ids
            )
        )
        return [RelationshipPath(path) for path in paths_between_outputs]

    def _calculate_paths_to_outputs(
        self, output: SourceID, rels: Sequence[Relationship]
    ):
        paths: list[list[Relationship]] = []
        for rel in rels:
            if rel.start_source.id == output:
                if rel.end_source.id in self.output_source_ids:
                    paths.append([rel])
                else:
                    child_paths = self._calculate_paths_to_outputs(
                        rel.end_source.id,
                        [  # we only want to use a fkey relationship once per path
                            next_rel
                            for next_rel in rels
                            if next_rel.fkey_relationship != rel.fkey_relationship
                        ],
                    )
                    paths.extend([rel, *child_path] for child_path in child_paths)
        return paths

    def output_edge_tables(self) -> list[Table]:
        paths_between_outputs = self.paths_between_outputs
        edge_tables = list[Table]()
        for path in paths_between_outputs:
            table = path.generate_join_table()

            table = table.update_typed_metadata(
                FeatureViewEdgeTableMetadata(
                    start_source_name=path.start_source_name,
                    end_source_name=path.end_source_name,
                    start_source_column_name=path.surrogate_start_column,
                    end_source_column_name=path.surrogate_end_column,
                ),
                FeatureViewRelationshipsMetadata(
                    relationship_path=list(path.relationship_path)
                ),
            )
            table = table.select(
                [path.surrogate_start_column, path.surrogate_end_column]
            )
            edge_tables.append(table)
        return edge_tables

    @classmethod
    def create(cls, *, room_id: eorm.RoomID, client: system.Client) -> FeatureView:
        """Create a FeatureView."""
        proto_feature_view = models_pb2.FeatureView(room_id=str(room_id))
        return FeatureView(
            proto_self=proto_feature_view,
            client=client,
        )

    @staticmethod
    def _unique_name_for_key_column(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    def _sanitize_keys(self, new_schema: Schema):
        renames = dict[str, str]()
        for field in new_schema:
            match field.ftype:
                case feature_type.PrimaryKey():
                    renames[field.name] = self._unique_name_for_key_column(
                        f"{field.name}_pk"
                    )
                case feature_type.ForeignKey():
                    renames[field.name] = self._unique_name_for_key_column(
                        f"{field.name}_fk"
                    )
                case _:
                    pass
        return renames

    def with_name(self, name: str) -> FeatureView:
        proto_self = copy.deepcopy(self.proto_self)
        proto_self.name = name
        return FeatureView(
            proto_self=proto_self,
            client=self.client,
        )

    def with_description(self, description: str) -> FeatureView:
        proto_self = copy.deepcopy(self.proto_self)
        proto_self.description = description
        return FeatureView(
            proto_self=proto_self,
            client=self.client,
        )

    def with_source(
        self,
        source: Source,
        *,
        row_filter: RowFilter | None = None,
        drop_disconnected: bool = False,
        include_columns: list[str] | None = None,
        output: bool = False,
    ) -> FeatureView:
        """Add a source to to this FeatureView.

        Args:
            source: The source to be added
            row_filter: Row level filters to be applied on source
            drop_disconnected: Filter orphan nodes in source
            include_columns: Column level filters to be applied on source
            output: Set to True if this should should be an entity in the ourput

        Example:
        >>> with_source(
        >>>     customer_source_id,
        >>>     row_filter=Column("customer_name").eq("Denis"),
        >>>     drop_disconnected=True,
        >>>     include_columns=["id", "customer_name"],
        >>> )
        """
        new_table = source.table
        if row_filter:
            new_table = new_table.filter_rows(row_filter)
        if include_columns:
            new_table = new_table.select(include_columns)

        renames = self._sanitize_keys(new_table.schema)

        if renames:
            new_table = new_table.rename_columns(renames).update_typed_metadata(
                FeatureViewSourceColumnRenames(column_renames=renames)
            )

        fvs = FeatureViewSource.create(
            room_id=source.room_id,
            table=new_table,
            drop_disconnected=drop_disconnected,
            source=source,
        )

        proto_self = copy.deepcopy(self.proto_self)
        proto_self.feature_view_sources.append(fvs.proto_self)

        if output:
            surrogate_key = (
                source.table.schema.get_surrogate_key()
                or source.table.schema.get_primary_key()
            )
            if not surrogate_key:
                raise result.InvalidArgumentError(
                    "source must have a surrogate key to part of the output"
                )
            proto_self.feature_view_output.output_sources.append(
                feature_view_pb2.OutputSource(source_id=str(source.id))
            )

        return FeatureView(
            proto_self=proto_self,
            client=self.client,
        )

    async def with_source_id(
        self,
        source_id: SourceID,
        *,
        row_filter: RowFilter | None = None,
        drop_disconnected: bool = False,
        include_columns: list[str] | None = None,
        output: bool = False,
        session: eorm.Session | None = None,
    ) -> FeatureView:
        """Add a source to to this FeatureView.

        Args:
            source_id: The id of the source to be added
            row_filter: Row level filters to be applied on source
            drop_disconnected: Filter orphan nodes in source
            include_columns: Column level filters to be applied on source
            output: Set to True if this should should be an entity in the ourput
            session: Existing session to join to

        Example:
        >>> with_source(
        >>>     customer_source_id,
        >>>     row_filter=Column("customer_name").eq("Denis"),
        >>>     drop_disconnected=True,
        >>>     include_columns=["id", "customer_name"],
        >>> )
        """
        source = (
            await Source.from_id(
                source_id=source_id, client=self.client, session=session
            )
        ).unwrap_or_raise()
        return self.with_source(
            source,
            row_filter=row_filter,
            drop_disconnected=drop_disconnected,
            include_columns=include_columns,
            output=output,
        )

    @staticmethod
    def _verify_fk_reference(
        fv_source: FeatureViewSource,
        foreign_key: str | None,
        expected_refd_source_id: SourceID,
    ) -> result.Ok[str | None] | result.InvalidArgumentError:
        if not foreign_key:
            return result.Ok(None)
        renames = (
            fv_source.table.get_typed_metadata(
                FeatureViewSourceColumnRenames
            ).column_renames
            if fv_source.table.has_typed_metadata(FeatureViewSourceColumnRenames)
            else dict[str, str]()
        )
        renamed_foreign_key = renames.get(foreign_key, foreign_key)
        match fv_source.table.schema[renamed_foreign_key].ftype:
            case feature_type.ForeignKey(referenced_source_id):
                if referenced_source_id != expected_refd_source_id:
                    return result.InvalidArgumentError(
                        "foreign_key does not reference expected source_id",
                        source_with_forien_key=fv_source.source.id,
                        referenced_source_id=expected_refd_source_id,
                    )
            case _:
                return result.InvalidArgumentError(
                    "the provided from_foreign_key is not a ForeignKey feature"
                )
        return result.Ok(renamed_foreign_key)

    def _check_or_infer_foreign_keys(
        self,
        from_fv_source: FeatureViewSource,
        to_fv_source: FeatureViewSource,
        from_foreign_key: str | None,
        to_foreign_key: str | None,
    ) -> result.Ok[tuple[str | None, str | None]] | result.InvalidArgumentError:
        match self._verify_fk_reference(
            from_fv_source, from_foreign_key, to_fv_source.source.id
        ):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(new_fk):
                from_foreign_key = new_fk

        match self._verify_fk_reference(
            to_fv_source, to_foreign_key, from_fv_source.source.id
        ):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok(new_fk):
                to_foreign_key = new_fk

        if not from_foreign_key and not to_foreign_key:
            from_foreign_keys = [
                field.name
                for field in from_fv_source.table.schema.get_foreign_keys(
                    to_fv_source.source.id
                )
            ]
            to_foreign_keys = [
                field.name
                for field in to_fv_source.table.schema.get_foreign_keys(
                    from_fv_source.source.id
                )
            ]

            if (
                (from_foreign_keys and to_foreign_keys)
                or len(from_foreign_keys) > 1
                or len(to_foreign_keys) > 1
            ):
                raise result.InvalidArgumentError(
                    "relationship is ambiguous:"
                    + "provide from_foreign_key or to_foreign_key to disambiguate",
                    from_foreign_keys=from_foreign_keys,
                    to_foreign_keys=to_foreign_keys,
                )
            if from_foreign_keys:
                from_foreign_key = from_foreign_keys[0]
            if to_foreign_keys:
                to_foreign_key = to_foreign_keys[0]

        return result.Ok((from_foreign_key, to_foreign_key))

    def _make_foreign_key_relationship(
        self,
        source_with_fkey: SourceID,
        fkey_column_name: str,
        refd_fv_source: FeatureViewSource,
    ):
        pk = refd_fv_source.table.schema.get_primary_key()
        if not pk:
            return result.InvalidArgumentError(
                "source has no primary key, "
                + "so it cannot be referenced by foreign key",
                source_id=refd_fv_source.source.id,
            )

        return result.Ok(
            FkeyRelationship(
                proto_self=feature_view_pb2.ForeignKeyRelationship(
                    foreign_key_having_source_id=str(source_with_fkey),
                    foreign_key_column_name=fkey_column_name,
                    referenced_source_id=str(refd_fv_source.source.id),
                    primary_key_column_name=pk.name,
                )
            )
        )

    def with_all_implied_relationships(self) -> FeatureView:
        """Automatically define non-directional relationships based on foreign keys."""
        new_feature_view = self
        for feature_view_source in self.feature_view_sources:
            for field in feature_view_source.source.table.schema:
                match field.ftype:
                    case feature_type.ForeignKey(referenced_source_id):
                        referenced_source = self.source_id_to_feature_view_source.get(
                            referenced_source_id
                        )
                        if referenced_source:
                            # We don't know the intended direction, add both directions
                            new_feature_view = new_feature_view.with_relationship(
                                referenced_source.source,
                                feature_view_source.source,
                                to_foreign_key=field.name,
                                directional=False,
                            )
                    case _:
                        pass
        return new_feature_view

    def with_relationship(
        self,
        start_source: Source,
        end_source: Source,
        *,
        from_foreign_key: str | None = None,
        to_foreign_key: str | None = None,
        directional: bool = False,
    ) -> FeatureView:
        """Define relationship between two sources.

        Args:
            start_source: The source on the "from" side (if directional)
            end_source: The source on the "to" side (if directional)
            from_foreign_key: The foreign key to use to match on the "from"
                source. Required if there is more than one foreign key relationship
                linking the sources. Cannot be used with "to_foreign_key".
            to_foreign_key: The foreign key to use to match on the "to"
                source. Required if there is more than one foreign key relationship
                linking the sources. Cannot be used with "from_foreign_key"
            directional: Whether to load graph as directional

        Example:
        >>> with_relationship(customer_source, order_source, directional=False)
        """
        match self._get_feature_view_source(start_source):
            case result.Ok(start_fv_source):
                pass
            case result.InvalidArgumentError() | result.NotFoundError():
                raise result.InvalidArgumentError(
                    "start_source does not match any source in this feature view",
                )

        match self._get_feature_view_source(end_source):
            case result.Ok(end_fv_source):
                pass
            case result.InvalidArgumentError() | result.NotFoundError():
                raise result.InvalidArgumentError(
                    "end_source does not match any source in this feature view",
                )

        if from_foreign_key and to_foreign_key:
            raise result.InvalidArgumentError(
                "only one of from_foreign_key and to_foreign_key may be provided",
            )

        from_foreign_key, to_foreign_key = self._check_or_infer_foreign_keys(
            start_fv_source,
            end_fv_source,
            from_foreign_key,
            to_foreign_key,
        ).unwrap_or_raise()

        if from_foreign_key:
            fkey_relationship = self._make_foreign_key_relationship(
                start_fv_source.source.id,
                from_foreign_key,
                end_fv_source,
            ).unwrap_or_raise()
        elif to_foreign_key:
            fkey_relationship = self._make_foreign_key_relationship(
                end_fv_source.source.id,
                to_foreign_key,
                start_fv_source,
            ).unwrap_or_raise()
        else:
            raise result.InvalidArgumentError(
                "foreign key relationship was not provided and could not be inferred"
            )

        proto_self = copy.deepcopy(self.proto_self)

        proto_self.feature_view_output.relationships.append(
            feature_view_pb2.FeatureViewRelationship(
                start_source_id=str(start_fv_source.source.id),
                end_source_id=str(end_fv_source.source.id),
                foreign_key_relationship=fkey_relationship.proto_self,
            )
        )
        if not directional:
            proto_self.feature_view_output.relationships.append(
                feature_view_pb2.FeatureViewRelationship(
                    start_source_id=str(end_fv_source.source.id),
                    end_source_id=str(start_fv_source.source.id),
                    foreign_key_relationship=fkey_relationship.proto_self,
                )
            )

        return FeatureView(
            proto_self=proto_self,
            client=self.client,
        )

    def with_row_numbers(
        self,
    ) -> FeatureView:
        """Adds row indexes to all output sources.

        Row indices are unique across all output sources.
        """
        offset = 0
        proto_self = copy.deepcopy(self.proto_self)
        del proto_self.feature_view_sources[:]

        for fvs in self.feature_view_sources:
            if fvs.source.id in self.output_source_ids:
                row_id_column = f"row-id-{uuid.uuid4()}"
                # TODO(Patrick): make row ids stable
                new_fvs = fvs.with_table(
                    fvs.table.add_row_index(
                        target=row_id_column, offset=offset
                    ).update_typed_metadata(
                        FeatureViewSourceRowIDs(row_id_column=row_id_column)
                    )
                )
                offset += system.OpGraphPlanner.count_rows_upperbound(
                    new_fvs.table.op_graph
                )
                proto_self.feature_view_sources.append(new_fvs.proto_self)
            else:
                proto_self.feature_view_sources.append(fvs.proto_self)

        return FeatureView(
            proto_self=proto_self,
            client=self.client,
        )
