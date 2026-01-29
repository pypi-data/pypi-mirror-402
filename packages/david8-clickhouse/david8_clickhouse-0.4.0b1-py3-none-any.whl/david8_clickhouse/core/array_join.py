import dataclasses

from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import AliasedProtocol, JoinProtocol


@dataclasses.dataclass(slots=True)
class ArrayJoin(JoinProtocol):
    join_type: str
    values: tuple[str | AliasedProtocol, ...]

    def get_sql(self, dialect: DialectProtocol) -> str:
        join_items = ()

        for value in self.values:
            if isinstance(value, str):
                join_items += (dialect.quote_ident(value),)
            else:
                join_items += (value.get_sql(dialect),)

        return f'{self.join_type} {", ".join(join_items)}'
