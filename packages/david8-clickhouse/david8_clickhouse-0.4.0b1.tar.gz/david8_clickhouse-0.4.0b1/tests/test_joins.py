from david8.expressions import col
from david8.protocols.sql import JoinProtocol
from parameterized import parameterized

from david8_clickhouse.joins import array_join
from tests.base_test import BaseTest


class TestJoins(BaseTest):
    @parameterized.expand([
        (
            array_join('col1', 'col2', col('col3').as_('alias1'), col('col4').as_('alias2')),
            'SELECT * ARRAY JOIN col1, col2, col3 AS alias1, col4 AS alias2',
            'SELECT "*" ARRAY JOIN "col1", "col2", "col3" AS "alias1", "col4" AS "alias2"'
        ),
    ])
    def test_array_join(self, join: JoinProtocol, exp_sql: str, exp_w_sql: str):
        self.assertEqual(self.qb.select('*').join(join).get_sql(), exp_sql)
        self.assertEqual(self.qb_w.select('*').join(join).get_sql(), exp_w_sql)
