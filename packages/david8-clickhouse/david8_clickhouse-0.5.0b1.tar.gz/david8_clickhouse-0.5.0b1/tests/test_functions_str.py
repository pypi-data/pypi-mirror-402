from david8.expressions import param
from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_clickhouse.functions_str import concat_with_separator
from tests.base_test import BaseTest


class TestFunctionsStr(BaseTest):

    @parameterized.expand([
        (
            concat_with_separator('col1', 1, 'col2', 0.5, param(2)).as_('new_field'),
            "SELECT concatWithSeparator(col1, '1', col2, '0.5', %(p1)s) AS new_field",
            'SELECT concatWithSeparator("col1", \'1\', "col2", \'0.5\', %(p1)s) AS "new_field"',
            {'p1': 2}
        ),
    ])
    def test_concat_with_separator(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str, exp_params: dict):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)
        self.assertEqual(query.get_parameters(), exp_params)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)
        self.assertEqual(query.get_parameters(), exp_params)
