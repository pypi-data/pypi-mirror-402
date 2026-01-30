# https://clickhouse.com/docs/sql-reference/table-functions

from .core.table_functions import UrlTableFunction as _UrlTableFunction
from .protocols.sql import TableFunctionProtocol


def url_(
    url_value: str,
    data_format: str = '',
    structure: list[tuple[str, str]] = None,
    headers: dict[str, str] = None,
) -> TableFunctionProtocol:
    return _UrlTableFunction(url_=url_value, data_format=data_format, structure=structure or [], headers=headers or {})

