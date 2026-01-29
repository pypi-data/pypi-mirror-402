import dataclasses

from david8.core.base_ddl import BaseQuery
from david8.core.base_expressions import FullTableName
from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import FunctionProtocol

from ..protocols.sql import CreateTableProtocol, SelectProtocol
from .expressions import on_cluster


@dataclasses.dataclass(slots=True)
class CreateTable(BaseQuery, CreateTableProtocol):
    query: SelectProtocol | None = None
    if_not_exists_: bool = False
    table: FullTableName = dataclasses.field(default_factory=FullTableName)
    partition_by_: tuple = dataclasses.field(default_factory=tuple)
    order_by_: tuple = dataclasses.field(default_factory=tuple)
    engine_: str = ''
    on_cluster_: str = None

    def _render_sql_prefix(self, dialect: DialectProtocol) -> str:
        if self.if_not_exists_:
            return 'CREATE TABLE IF NOT EXISTS'
        return 'CREATE TABLE '

    def _to_str_order_parts(self, items: tuple[str | FunctionProtocol, ...], dialect: DialectProtocol) -> str:
        parts = []
        for item in items:
            if isinstance(item, FunctionProtocol):
                parts.append(item.get_sql(dialect))
            else:
                parts.append(item)

        return ', '.join(parts)

    def _render_sql(self, dialect: DialectProtocol) -> str:
        if self.query:
            cluster = on_cluster(self.on_cluster_)
            cluster = f' {cluster}' if cluster else ''
            engine = f' ENGINE = {self.engine_}'
            order = f' ORDER BY ({self._to_str_order_parts(self.order_by_, dialect)}) '
            if self.partition_by_:
                partition = f' PARTITION BY ({self._to_str_order_parts(self.partition_by_, dialect)})'
            else:
                partition = ''

            return f'{self.table.get_sql(dialect)}{cluster}{engine}{partition}{order}AS {self.query.get_sql(dialect)}'

        return ''

    def set_table(self, table: str, db: str = '') -> None:
        self.table.set_names(table, db)

    def if_not_exists(self) -> 'CreateTableProtocol':
        self.if_not_exists_ = True
        return self

    def engine(self, value: str) -> 'CreateTableProtocol':
        self.engine_ = value
        return self

    def partition_by(self, *args: str | FunctionProtocol) -> 'CreateTableProtocol':
        self.partition_by_ = args
        return self

    def order_by(self, *args: str | FunctionProtocol) -> 'CreateTableProtocol':
        self.order_by_ = args
        return self

    def on_cluster(self, name: str) -> 'CreateTableProtocol':
        self.on_cluster_ = name
        return self
