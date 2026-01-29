from collections.abc import Iterable

from david8.core.base_expressions import FullTableName
from david8.core.base_query_builder import BaseQueryBuilder as _BaseQueryBuilder
from david8.protocols.sql import AliasedProtocol, ExprProtocol, FunctionProtocol, QueryProtocol

from ..protocols.query_builder import QueryBuilderProtocol
from ..protocols.sql import CreateTableProtocol, SelectProtocol
from .ddl import CreateTable
from .drop_partitions import DropPartitions
from .select_query import ClickHouseSelect


class ClickHouseQueryBuilder(QueryBuilderProtocol, _BaseQueryBuilder):
    def select(self, *args: str | AliasedProtocol | ExprProtocol | FunctionProtocol) -> SelectProtocol:
        return ClickHouseSelect(select_columns=args, dialect=self._dialect)

    def drop_partitions(
        self,
        table: str,
        partitions: Iterable[str | int | tuple[int | str, ...]],
        db: str = None,
        on_cluster: str = None,
    ) -> QueryProtocol:
        return DropPartitions(dialect=self._dialect, on_cluster=on_cluster,
                              table=FullTableName(table, db), partitions=partitions)

    def create_table_as(self, query: SelectProtocol, table: str, db: str = '') -> CreateTableProtocol:
        return CreateTable(dialect=self._dialect, query=query, table=FullTableName(table, db))
