import dataclasses

from david8.core.arg_convertors import to_col_or_expr
from david8.core.fn_generator import FnCallableFactory as _Factory
from david8.core.fn_generator import Function as _Fn
from david8.protocols.sql import DialectProtocol, ExprProtocol, FunctionProtocol, PredicateProtocol


@dataclasses.dataclass(slots=True)
class _MultiIfFn(_Fn):
    args: tuple[tuple[PredicateProtocol, str | ExprProtocol], ...]
    else_: str | ExprProtocol

    def _get_sql(self, dialect: DialectProtocol) -> str:
        items = ()
        for predicate, value in self.args:
            items += (predicate.get_sql(dialect), to_col_or_expr(value, dialect), )

        items += (to_col_or_expr(self.else_, dialect), )
        return f'{self.name}({", ".join(items)})'


@dataclasses.dataclass(slots=True)
class _MultiIfFactory(_Factory):
    def __call__(
        self,
        *args: tuple[PredicateProtocol, str | ExprProtocol],
        else_: str | ExprProtocol,
    ) -> FunctionProtocol:
        return _MultiIfFn('multiIf', args, else_)


multi_if = _MultiIfFactory()
