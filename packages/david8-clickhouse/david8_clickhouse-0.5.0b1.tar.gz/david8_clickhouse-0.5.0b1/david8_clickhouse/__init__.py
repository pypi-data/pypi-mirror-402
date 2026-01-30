from david8.core.base_dialect import BaseDialect as _BaseDialect
from david8.param_styles import PyFormatParamStyle

from .core.query_builder import ClickHouseQueryBuilder as _QueryBuilder
from .protocols.query_builder import QueryBuilderProtocol


def get_qb(is_quote_mode: bool = False) -> QueryBuilderProtocol:
    dialect = _BaseDialect(PyFormatParamStyle(), is_quote_mode)
    return _QueryBuilder(dialect)
