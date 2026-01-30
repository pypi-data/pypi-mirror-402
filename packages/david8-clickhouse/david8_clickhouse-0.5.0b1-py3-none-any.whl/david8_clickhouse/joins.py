from david8.protocols.sql import AliasedProtocol, JoinProtocol

from .core.array_join import ArrayJoin as _ArrayJoin


def array_join(*args: str | AliasedProtocol) -> JoinProtocol:
    """
    https://clickhouse.com/docs/sql-reference/statements/select/array-join
    """
    return _ArrayJoin('ARRAY JOIN', args)

def left_array_join(*args: str | AliasedProtocol) -> JoinProtocol:
    """
    https://clickhouse.com/docs/sql-reference/statements/select/array-join
    """
    return _ArrayJoin('LEFT ARRAY JOIN', args)
