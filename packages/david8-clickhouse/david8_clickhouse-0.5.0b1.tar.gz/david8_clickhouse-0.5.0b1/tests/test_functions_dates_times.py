from david8.expressions import val
from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_clickhouse.functions_dates_times import (
    parse_datetime_best_effort,
    to_date,
    to_date_or_null,
    to_datetime_or_null,
    to_datetime_or_zero,
    yyyymmdd_to_date,
    yyyymmdd_to_date32,
)
from tests.base_test import BaseTest


class TestFunctionsDatesTimes(BaseTest):

    @parameterized.expand([
        (
            yyyymmdd_to_date('year_month_dd').as_('date'),
            'SELECT YYYYMMDDToDate(year_month_dd) AS date',
            'SELECT YYYYMMDDToDate("year_month_dd") AS "date"',
        ),
        (
            yyyymmdd_to_date(20260101).as_('date'),
            'SELECT YYYYMMDDToDate(20260101) AS date',
            'SELECT YYYYMMDDToDate(20260101) AS "date"',
        ),
        (
            yyyymmdd_to_date32('year_month_dd').as_('date'),
            'SELECT YYYYMMDDToDate32(year_month_dd) AS date',
            'SELECT YYYYMMDDToDate32("year_month_dd") AS "date"',
        ),
        (
            to_date('created_dt').as_('date'),
            'SELECT toDate(created_dt) AS date',
            'SELECT toDate("created_dt") AS "date"',
        ),
        (
            to_date(val('2026-01-01')).as_('date'),
            "SELECT toDate('2026-01-01') AS date",
            'SELECT toDate(\'2026-01-01\') AS "date"',
        ),
        (
            to_date_or_null('created_dt').as_('date'),
            'SELECT toDateOrNull(created_dt) AS date',
            'SELECT toDateOrNull("created_dt") AS "date"',
        ),
        (
            to_date_or_null(val('2026-01-01')).as_('date'),
            "SELECT toDateOrNull('2026-01-01') AS date",
            'SELECT toDateOrNull(\'2026-01-01\') AS "date"',
        ),
        (
            to_datetime_or_zero('created_dt').as_('date'),
            'SELECT toDateTimeOrZero(created_dt) AS date',
            'SELECT toDateTimeOrZero("created_dt") AS "date"',
        ),
        (
            to_datetime_or_zero(val('2026-01-01')).as_('date'),
            "SELECT toDateTimeOrZero('2026-01-01') AS date",
            'SELECT toDateTimeOrZero(\'2026-01-01\') AS "date"',
        ),
        (
            to_datetime_or_null('created_dt').as_('date'),
            'SELECT toDateTimeOrNull(created_dt) AS date',
            'SELECT toDateTimeOrNull("created_dt") AS "date"',
        ),
        (
            to_datetime_or_null(val('2026-01-01')).as_('date'),
            "SELECT toDateTimeOrNull('2026-01-01') AS date",
            'SELECT toDateTimeOrNull(\'2026-01-01\') AS "date"',
        ),
        (
            parse_datetime_best_effort('created_dt').as_('date'),
            'SELECT parseDateTimeBestEffort(created_dt) AS date',
            'SELECT parseDateTimeBestEffort("created_dt") AS "date"',
        ),
        (
            parse_datetime_best_effort(val('2026-01-01')).as_('date'),
            "SELECT parseDateTimeBestEffort('2026-01-01') AS date",
            'SELECT parseDateTimeBestEffort(\'2026-01-01\') AS "date"',
        ),
    ])
    def test_1arg_functions(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)
