from parameterized import parameterized

from david8_clickhouse.protocols.sql import SelectProtocol
from tests.base_test import BaseTest


class TestSelect(BaseTest):
    @parameterized.expand([
        (
            BaseTest.qb.select('name').from_table('events', final=True),
            'SELECT name FROM events FINAL',
        ),
        (
            BaseTest.qb_w.select('name').from_table('events', final=True),
            'SELECT "name" FROM "events" FINAL',
        ),
        (
            BaseTest.qb.select('name').from_table('events', db_name='legacy', final=True),
            'SELECT name FROM legacy.events FINAL',
        ),
        (
            BaseTest.qb_w.select('name').from_table('events', db_name='legacy', final=True),
            'SELECT "name" FROM "legacy"."events" FINAL',
        ),
    ])
    def test_final(self, query: SelectProtocol, exp_sql):
        self.assertEqual(query.get_sql(), exp_sql)
