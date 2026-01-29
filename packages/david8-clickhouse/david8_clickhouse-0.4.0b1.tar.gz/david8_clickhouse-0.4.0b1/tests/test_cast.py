from david8.expressions import val
from david8.functions import cast
from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_clickhouse.cast_types import (
    bfloat16,
    float32,
    float64,
    int8,
    int16,
    int32,
    int64,
    int128,
    int256,
    string,
    uint8,
    uint16,
    uint32,
    uint64,
    uint128,
    uint256,
)
from tests.base_test import BaseTest


class TestCast(BaseTest):

    @parameterized.expand([
        (
            cast(val('7'), string),
            "SELECT CAST('7' AS String)",
        ),
        (
            cast('col_name', int8),
            'SELECT CAST(col_name AS Int8)',
        ),
        (
            cast('col_name', int16),
            'SELECT CAST(col_name AS Int16)',
        ),
        (
            cast('col_name', int32),
            'SELECT CAST(col_name AS Int32)',
        ),
        (
            cast('col_name', int64),
            'SELECT CAST(col_name AS Int64)',
        ),
        (
            cast('col_name', int128),
            'SELECT CAST(col_name AS Int128)',
        ),
        (
            cast('col_name', int256),
            'SELECT CAST(col_name AS Int256)',
        ),
        (
            cast('col_name', uint8),
            'SELECT CAST(col_name AS UInt8)',
        ),
        (
            cast('col_name', uint16),
            'SELECT CAST(col_name AS UInt16)',
        ),
        (
            cast('col_name', uint32),
            'SELECT CAST(col_name AS UInt32)',
        ),
        (
            cast('col_name', uint64),
            'SELECT CAST(col_name AS UInt64)',
        ),
        (
            cast('col_name', uint128),
            'SELECT CAST(col_name AS UInt128)',
        ),
        (
            cast('col_name', uint256),
            'SELECT CAST(col_name AS UInt256)',
        ),
        (
            cast('col_name', float32),
            'SELECT CAST(col_name AS Float32)',
        ),
        (
            cast('col_name', float64),
            'SELECT CAST(col_name AS Float64)',
        ),
        (
            cast(val('1'), bfloat16).as_('bfloat16_val'),
            "SELECT CAST('1' AS BFloat16) AS bfloat16_val",
        ),
    ])
    def test_cast(self, fn: FunctionProtocol, sql_exp: str):
        self.assertEqual(self.qb.select(fn).get_sql(), sql_exp)
