from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_clickhouse.functions_dict import (
    dict_get,
    dict_get_date,
    dict_get_datetime,
    dict_get_float32,
    dict_get_float32_or_default,
    dict_get_float64,
    dict_get_float64_or_default,
    dict_get_int8,
    dict_get_int8_or_default,
    dict_get_int16,
    dict_get_int16_or_default,
    dict_get_int32,
    dict_get_int32_or_default,
    dict_get_int64,
    dict_get_int64_or_default,
    dict_get_ipv4,
    dict_get_ipv6,
    dict_get_or_default,
    dict_get_string,
    dict_get_string_or_default,
    dict_get_uint8,
    dict_get_uint8_or_default,
    dict_get_uint16,
    dict_get_uint16_or_default,
    dict_get_uint32,
    dict_get_uint32_or_default,
    dict_get_uint64,
    dict_get_uint64_or_default,
    dict_get_uuid,
)
from tests.base_test import BaseTest


class TestFunctionsDict(BaseTest):
    @parameterized.expand([
        (
            dict_get('dicts.currencies', 'full_name', 'currency_char').as_('currency'),
            "SELECT dictGet('dicts.currencies', 'full_name', currency_char) AS currency",
            "SELECT dictGet('dicts.currencies', 'full_name', \"currency_char\") AS \"currency\"",
        ),
        (
            dict_get_string('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetString('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetString('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_uuid('dicts.currencies', 'id', 'currency_char').as_('currency_id'),
            "SELECT dictGetUUID('dicts.currencies', 'id', currency_char) AS currency_id",
            "SELECT dictGetUUID('dicts.currencies', 'id', \"currency_char\") AS \"currency_id\"",
        ),
        (
            dict_get_date('dicts.currencies', 'created_dt', 'currency_char').as_('currency'),
            "SELECT dictGetDate('dicts.currencies', 'created_dt', currency_char) AS currency",
            "SELECT dictGetDate('dicts.currencies', 'created_dt', \"currency_char\") AS \"currency\"",
        ),
        (
            dict_get_datetime('dicts.currencies', 'created_dt', 'currency_char').as_('currency'),
            "SELECT dictGetDateTime('dicts.currencies', 'created_dt', currency_char) AS currency",
            "SELECT dictGetDateTime('dicts.currencies', 'created_dt', \"currency_char\") AS \"currency\"",
        ),
        (
            dict_get_float32('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetFloat32('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetFloat32('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_float64('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetFloat64('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetFloat64('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_uint8('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetUInt8('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetUInt8('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_uint16('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetUInt16('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetUInt16('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_uint32('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetUInt32('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetUInt32('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_uint64('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetUInt64('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetUInt64('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_int8('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetInt8('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetInt8('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_int16('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetInt16('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetInt16('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_int32('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetInt32('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetInt32('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_int64('dicts.currencies', 'price', 'currency_char').as_('price'),
            "SELECT dictGetInt64('dicts.currencies', 'price', currency_char) AS price",
            "SELECT dictGetInt64('dicts.currencies', 'price', \"currency_char\") AS \"price\"",
        ),
        (
            dict_get_ipv4('dicts.currencies', 'created_ip', 'currency_char').as_('ip'),
            "SELECT dictGetIPv4('dicts.currencies', 'created_ip', currency_char) AS ip",
            "SELECT dictGetIPv4('dicts.currencies', 'created_ip', \"currency_char\") AS \"ip\"",
        ),
        (
            dict_get_ipv6('dicts.currencies', 'created_ip', 'currency_char').as_('ip'),
            "SELECT dictGetIPv6('dicts.currencies', 'created_ip', currency_char) AS ip",
            "SELECT dictGetIPv6('dicts.currencies', 'created_ip', \"currency_char\") AS \"ip\"",
        ),
    ])
    def test_dict_get(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)

    @parameterized.expand([
        (
            dict_get_or_default('dicts.currencies', 'full_name', 'currency_char', 'EURO').as_('currency'),
            "SELECT dictGetOrDefault('dicts.currencies', 'full_name', currency_char, 'EURO') AS currency",
            "SELECT dictGetOrDefault('dicts.currencies', 'full_name', \"currency_char\", 'EURO') AS \"currency\"",
        ),
        (
            dict_get_string_or_default('dicts.currencies', 'price', 'currency_char', 'EURO').as_('price'),
            "SELECT dictGetStringOrDefault('dicts.currencies', 'price', currency_char, 'EURO') AS price",
            "SELECT dictGetStringOrDefault('dicts.currencies', 'price', \"currency_char\", 'EURO') AS \"price\"",
        ),
        (
            dict_get_float32_or_default('dicts.currencies', 'price', 'currency_char', 1.9).as_('price'),
            "SELECT dictGetFloat32OrDefault('dicts.currencies', 'price', currency_char, 1.9) AS price",
            "SELECT dictGetFloat32OrDefault('dicts.currencies', 'price', \"currency_char\", 1.9) AS \"price\"",
        ),
        (
            dict_get_float64_or_default('dicts.currencies', 'price', 'currency_char', 7.65).as_('price'),
            "SELECT dictGetFloat64OrDefault('dicts.currencies', 'price', currency_char, 7.65) AS price",
            "SELECT dictGetFloat64OrDefault('dicts.currencies', 'price', \"currency_char\", 7.65) AS \"price\"",
        ),
        (
            dict_get_uint8_or_default('dicts.currencies', 'price', 'currency_char', 8).as_('price'),
            "SELECT dictGetUInt8OrDefault('dicts.currencies', 'price', currency_char, 8) AS price",
            "SELECT dictGetUInt8OrDefault('dicts.currencies', 'price', \"currency_char\", 8) AS \"price\"",
        ),
        (
            dict_get_uint16_or_default('dicts.currencies', 'price', 'currency_char', 10).as_('price'),
            "SELECT dictGetUInt16OrDefault('dicts.currencies', 'price', currency_char, 10) AS price",
            "SELECT dictGetUInt16OrDefault('dicts.currencies', 'price', \"currency_char\", 10) AS \"price\"",
        ),
        (
            dict_get_uint32_or_default('dicts.currencies', 'price', 'currency_char', 16).as_('price'),
            "SELECT dictGetUInt32OrDefault('dicts.currencies', 'price', currency_char, 16) AS price",
            "SELECT dictGetUInt32OrDefault('dicts.currencies', 'price', \"currency_char\", 16) AS \"price\"",
        ),
        (
            dict_get_uint64_or_default('dicts.currencies', 'price', 'currency_char', 27).as_('price'),
            "SELECT dictGetUInt64OrDefault('dicts.currencies', 'price', currency_char, 27) AS price",
            "SELECT dictGetUInt64OrDefault('dicts.currencies', 'price', \"currency_char\", 27) AS \"price\"",
        ),
        (
            dict_get_int8_or_default('dicts.currencies', 'price', 'currency_char', 3).as_('price'),
            "SELECT dictGetInt8OrDefault('dicts.currencies', 'price', currency_char, 3) AS price",
            "SELECT dictGetInt8OrDefault('dicts.currencies', 'price', \"currency_char\", 3) AS \"price\"",
        ),
        (
            dict_get_int16_or_default('dicts.currencies', 'price', 'currency_char', 36).as_('price'),
            "SELECT dictGetInt16OrDefault('dicts.currencies', 'price', currency_char, 36) AS price",
            "SELECT dictGetInt16OrDefault('dicts.currencies', 'price', \"currency_char\", 36) AS \"price\"",
        ),
        (
            dict_get_int32_or_default('dicts.currencies', 'price', 'currency_char', 33).as_('price'),
            "SELECT dictGetInt32OrDefault('dicts.currencies', 'price', currency_char, 33) AS price",
            "SELECT dictGetInt32OrDefault('dicts.currencies', 'price', \"currency_char\", 33) AS \"price\"",
        ),
        (
            dict_get_int64_or_default('dicts.currencies', 'price', 'currency_char', 101).as_('price'),
            "SELECT dictGetInt64OrDefault('dicts.currencies', 'price', currency_char, 101) AS price",
            "SELECT dictGetInt64OrDefault('dicts.currencies', 'price', \"currency_char\", 101) AS \"price\"",
        ),
    ])
    def test_dict_get_or_default(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)
