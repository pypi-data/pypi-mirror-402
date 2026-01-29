from david8.expressions import param, val
from david8.predicates import eq, ne_c
from david8.protocols.sql import FunctionProtocol
from parameterized import parameterized

from david8_clickhouse.functions_conditional import multi_if
from tests.base_test import BaseTest


class TestConditionalFunctions(BaseTest):

    @parameterized.expand([
        (
            multi_if(
                (eq('status', 'unknown'), 'new_status'),
                (eq('status', 'old_status'), val('legacy')),
                else_='status',
            ).as_('fixed_status'),
            "SELECT multiIf(status = %(p1)s, new_status, status = %(p2)s, 'legacy', status) AS fixed_status",
            'SELECT multiIf("status" = %(p1)s, "new_status", "status" = %(p2)s, \'legacy\', "status") AS '
            '"fixed_status"',
            {'p1': 'unknown', 'p2': 'old_status'}
        ),
        (
            multi_if(
                (eq('new_status', 'unknown'), 'old_status'),
                (ne_c('new_status', 'old_status'), 'new_status'),
                else_=param('active'),
            ).as_('fixed_status'),
            "SELECT multiIf(new_status = %(p1)s, old_status, new_status != old_status, new_status, %(p2)s) AS "
            "fixed_status",
            'SELECT multiIf("new_status" = %(p1)s, "old_status", "new_status" != "old_status", "new_status", %(p2)s)'
            ' AS "fixed_status"',
            {'p1': 'unknown', 'p2': 'active'},
        ),
    ])
    def test_multi_if(self, fn: FunctionProtocol, exp_sql: str, exp_w_sql: str, exp_params: dict):
        query = self.qb.select(fn)
        self.assertEqual(query.get_sql(), exp_sql)
        self.assertEqual(query.get_parameters(), exp_params)

        query = self.qb_w.select(fn)
        self.assertEqual(query.get_sql(), exp_w_sql)
        self.assertEqual(query.get_parameters(), exp_params)
