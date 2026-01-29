from collections.abc import Iterable

from david8.protocols.query_builder import QueryBuilderProtocol as _QueryBuilderProtocol
from david8.protocols.sql import AliasedProtocol, ExprProtocol, FunctionProtocol, QueryProtocol

from ..protocols.sql import CreateTableProtocol, SelectProtocol


class QueryBuilderProtocol(_QueryBuilderProtocol):
    def select(self, *args: str | AliasedProtocol | ExprProtocol | FunctionProtocol) -> SelectProtocol:
        pass

    def drop_partitions(
        self,
        table: str,
        partitions: Iterable[str | int | tuple[int | str, ...]],
        db: str = None,
        on_cluster: str = None,
    ) -> QueryProtocol:
        pass

    def create_table_as(self, query: SelectProtocol, table: str, db: str = '') -> CreateTableProtocol:
        pass
