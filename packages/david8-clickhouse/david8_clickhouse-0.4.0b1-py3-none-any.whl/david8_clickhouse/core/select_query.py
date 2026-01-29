from david8.core.base_dql import BaseSelect as _BaseSelect
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import SelectProtocol


class ClickHouseSelect(_BaseSelect, SelectProtocol):
    final: bool = False

    def from_table(self, table_name: str, alias: str = '', db_name: str = '', final: bool = False) -> SelectProtocol:
        super().from_table(table_name, alias, db_name)
        self.final = final
        return self

    def _from_to_sql(self, dialect: DialectProtocol) -> str:
        sql = super()._from_to_sql(dialect)
        if self.final and self.from_table_cnstr.table:
            return f'{sql} FINAL'
        return sql
