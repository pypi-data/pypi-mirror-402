import dataclasses

from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import TableFunctionProtocol


@dataclasses.dataclass(slots=True)
class BaseTableFunction(TableFunctionProtocol):
    @property
    def name(self) -> str:
        raise NotImplementedError()

    def _get_fn_args(self) -> tuple:
        return ()

    def get_sql(self, dialect: DialectProtocol) -> str:
        return f'{self.name}({", ".join(a for a in self._get_fn_args() if a)})'


@dataclasses.dataclass(slots=True)
class UrlTableFunction(BaseTableFunction):
    url_: str
    data_format: str = ''
    structure: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    headers: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def name(self) -> str:
        return 'url'

    def _get_fn_args(self) -> tuple:
        structure = ', '.join(' '.join(s) for s in self.structure)
        structure = f"'{structure}'" if structure else ''

        if self.headers:
            parts = (f"'{k}'='{v}'" for k, v in self.headers.items())
            headers = f"headers=({', '.join(parts)})"
        else:
            headers = ''

        return (
            f"'{self.url_}'",
            f"'{self.data_format}'" if self.data_format else "",
            structure,
            headers,
        )

