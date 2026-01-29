import dataclasses
from collections.abc import Iterable

from david8.core.base_expressions import FullTableName
from david8.core.base_query import BaseQuery
from david8.protocols.dialect import DialectProtocol

from ..core.expressions import on_cluster


@dataclasses.dataclass(slots=True)
class DropPartitions(BaseQuery):
    partitions: Iterable[str | int | tuple[int | str, ...]]
    table: FullTableName = dataclasses.field(default_factory=FullTableName)
    on_cluster: str = None

    def _render_sql_prefix(self, dialect: DialectProtocol) -> str:
        return f'ALTER TABLE {self.table.get_sql(dialect)} '

    def _render_sql(self, dialect: DialectProtocol) -> str:
        cluster = on_cluster(self.on_cluster)
        if cluster:
            return f'{cluster} '
        return ''

    def _render_sql_postfix(self, dialect: DialectProtocol) -> str:
        partitions = ()
        for partition in self.partitions:
            if isinstance(partition, (int, tuple)):
                partitions += (f'DROP PARTITION {partition}',)
                continue

            partitions += (f"DROP PARTITION '{partition}'",)

        return f'{", ".join(partitions)}'
