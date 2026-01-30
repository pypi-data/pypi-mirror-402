import dataclasses

from david8.core.base_dml import BaseInsert
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import InsertProtocol, TableFunctionProtocol


@dataclasses.dataclass(slots=True)
class Insert(BaseInsert, InsertProtocol):
    table_fn: TableFunctionProtocol | None = None

    def into_table_fn(self, fn: TableFunctionProtocol) -> 'InsertProtocol':
        self.target_table.set_names('', '')
        self.table_fn = fn
        return self

    def _get_sql(self, dialect: DialectProtocol) -> str:
        if self.table_fn is None:
            return super()._get_sql(dialect)

        sql = f'INSERT INTO FUNCTION {self.table_fn.get_sql(dialect)}'
        if self.from_query_expr:
            sql = f'{sql} {self.from_query_expr.get_sql(dialect)}'
        else:
            placeholders = ()
            for value in self.values:
                _, placeholder = dialect.get_paramstyle().add_param(value)
                placeholders += (placeholder,)

            sql = f'{sql} VALUES ({", ".join(placeholders)})'

        return sql
