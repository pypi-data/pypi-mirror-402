import dataclasses

from david8.core.arg_convertors import to_col_or_expr
from david8.core.fn_generator import FnCallableFactory as _FnCallableFactory
from david8.core.fn_generator import Function as _Fn
from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import ExprProtocol, FunctionProtocol


@dataclasses.dataclass(slots=True)
class _AttrNamesFn(_Fn):
    dict_name: str
    attr_names: tuple[str, ...] | str
    id_expr: str | ExprProtocol
    default_value_expr: int | str | float | ExprProtocol = None

    def _get_sql(self, dialect: DialectProtocol) -> str:
        if isinstance(self.attr_names, str):
            attr_names = f"'{self.attr_names}'"
        else:
            attr_names = ','.join(f"'{v}'" for v in self.attr_names)
            attr_names = f'({attr_names})'

        args = (f"'{self.dict_name}'", attr_names, to_col_or_expr(self.id_expr, dialect))
        if self.default_value_expr is not None:
            if isinstance(self.default_value_expr, (int, float)):
                args += (f'{self.default_value_expr}',)
            elif isinstance(self.default_value_expr, ExprProtocol):
                args += (self.default_value_expr.get_sql(dialect),)
            else:
                args += (f"'{self.default_value_expr}'",)

        return f"{self.name}({', '.join(args)})"


@dataclasses.dataclass(slots=True)
class _AttrNamesFactory(_FnCallableFactory):
    def __call__(
        self,
        dict_name: str,
        attr_names: str | tuple[str, ...],
        id_expr: str | ExprProtocol
    ) -> FunctionProtocol:
        return _AttrNamesFn(self.name, dict_name=dict_name, attr_names=attr_names, id_expr=id_expr)


@dataclasses.dataclass(slots=True)
class _AttrNamesDefaultFactory(_FnCallableFactory):
    def __call__(
        self,
        dict_name: str,
        attr_names: str | tuple[str, ...],
        id_expr: str | ExprProtocol,
        default_value_expr: int | str | float | ExprProtocol
    ) -> FunctionProtocol:
        return _AttrNamesFn(self.name, dict_name=dict_name, attr_names=attr_names, id_expr=id_expr,
                            default_value_expr=default_value_expr)


dict_get = _AttrNamesFactory(name='dictGet')
dict_get_date = _AttrNamesFactory(name='dictGetDate')
dict_get_datetime = _AttrNamesFactory(name='dictGetDateTime')
dict_get_float32 = _AttrNamesFactory(name='dictGetFloat32')
dict_get_float64 = _AttrNamesFactory(name='dictGetFloat64')
dict_get_ipv4 = _AttrNamesFactory(name='dictGetIPv4')
dict_get_ipv6 = _AttrNamesFactory(name='dictGetIPv6')
dict_get_int16 = _AttrNamesFactory(name='dictGetInt16')
dict_get_int32 = _AttrNamesFactory(name='dictGetInt32')
dict_get_int64 = _AttrNamesFactory(name='dictGetInt64')
dict_get_int8 = _AttrNamesFactory(name='dictGetInt8')
dict_get_string = _AttrNamesFactory(name='dictGetString')
dict_get_uint16 = _AttrNamesFactory(name='dictGetUInt16')
dict_get_uint32 = _AttrNamesFactory(name='dictGetUInt32')
dict_get_uint64 = _AttrNamesFactory(name='dictGetUInt64')
dict_get_uint8 = _AttrNamesFactory(name='dictGetUInt8')
dict_get_uuid = _AttrNamesFactory(name='dictGetUUID')
# default
dict_get_uuid_or_default = _AttrNamesDefaultFactory(name='dictGetUUID')
dict_get_uint8_or_default = _AttrNamesDefaultFactory(name='dictGetUInt8OrDefault')
dict_get_uint64_or_default = _AttrNamesDefaultFactory(name='dictGetUInt64OrDefault')
dict_get_uint16_or_default = _AttrNamesDefaultFactory(name='dictGetUInt16OrDefault')
dict_get_uint32_or_default = _AttrNamesDefaultFactory(name='dictGetUInt32OrDefault')
dict_get_string_or_default = _AttrNamesDefaultFactory(name='dictGetStringOrDefault')
dict_get_int16_or_default = _AttrNamesDefaultFactory(name='dictGetInt16OrDefault')
dict_get_int8_or_default = _AttrNamesDefaultFactory(name='dictGetInt8OrDefault')
dict_get_int32_or_default = _AttrNamesDefaultFactory(name='dictGetInt32OrDefault')
dict_get_int64_or_default = _AttrNamesDefaultFactory(name='dictGetInt64OrDefault')
dict_get_ipv4_or_default = _AttrNamesDefaultFactory(name='dictGetIPv4OrDefault')
dict_get_ipv6_or_default = _AttrNamesDefaultFactory(name='dictGetIPv6OrDefault')
dict_get_float32_or_default = _AttrNamesDefaultFactory(name='dictGetFloat32OrDefault')
dict_get_float64_or_default = _AttrNamesDefaultFactory(name='dictGetFloat64OrDefault')
dict_get_datetime_or_default = _AttrNamesDefaultFactory(name='dictGetDateTimeOrDefault')
dict_get_or_default = _AttrNamesDefaultFactory(name='dictGetOrDefault')
dict_get_date_or_default = _AttrNamesDefaultFactory(name='dictGetDateOrDefault')
