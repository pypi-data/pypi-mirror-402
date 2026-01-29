from david8.protocols.sql import FunctionProtocol, QueryProtocol
from david8.protocols.sql import SelectProtocol as _SelectProtocol


class SelectProtocol(_SelectProtocol):
    def from_table(self, table_name: str, alias: str = '', db_name: str = '', final: bool = False) -> 'SelectProtocol':
        """
        final flag: https://clickhouse.com/docs/sql-reference/statements/select/from#final-modifier
        """

class CreateTableProtocol(QueryProtocol):
    def engine(self, value: str) -> 'CreateTableProtocol':
        pass

    def partition_by(self, *args: str | FunctionProtocol) -> 'CreateTableProtocol':
        pass

    def order_by(self, *args: str | FunctionProtocol) -> 'CreateTableProtocol':
        pass

    def if_not_exists(self) -> 'CreateTableProtocol':
        pass

    def on_cluster(self, name: str) -> 'CreateTableProtocol':
        pass
