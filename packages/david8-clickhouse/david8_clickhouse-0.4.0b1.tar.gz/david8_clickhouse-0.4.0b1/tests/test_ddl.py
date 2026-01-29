from david8.protocols.sql import QueryProtocol
from parameterized import parameterized

from david8_clickhouse.functions_dates_times import to_date
from tests.base_test import BaseTest


class TestDLL(BaseTest):

    @parameterized.expand([
        (
            BaseTest.qb
            .create_table_as(
                BaseTest.qb.select('name', 'created_at').from_table('events'),
                'events_copy'
            )
            .order_by('created_at', 'name')
            .engine('Memory'),
            'CREATE TABLE events_copy ENGINE = Memory ORDER BY (created_at, name) AS '
            'SELECT name, created_at FROM events',
        ),
        (
            BaseTest.qb
            .create_table_as(
                BaseTest.qb.select('name', 'created_at').from_table('events'),
                'events_copy',
                'maintenance'
            )
            .order_by('created_at', 'name')
            .engine('Memory'),
            'CREATE TABLE maintenance.events_copy ENGINE = Memory ORDER BY (created_at, name) AS '
            'SELECT name, created_at FROM events',
        ),
        # cluster + partition
        (
            BaseTest.qb
            .create_table_as(
                BaseTest.qb.select('name', 'created_at').from_table('events'),
                'events_copy'
            )
            .order_by('created_at', 'name')
            .partition_by(to_date('created_at'), 'name')
            .on_cluster('events')
            .engine('MergeTree'),
            'CREATE TABLE events_copy ON CLUSTER events ENGINE = MergeTree PARTITION BY (toDate(created_at), name) '
            'ORDER BY (created_at, name) AS SELECT name, created_at FROM events'
        ),
        (
            BaseTest.qb
            .create_table_as(
                BaseTest.qb.select('name', 'created_at').from_table('events'),
                'events_copy',
                'maintenance'
            )
            .order_by('created_at', 'name')
            .partition_by(to_date('created_at'), 'name')
            .on_cluster('{cluster}')
            .engine('MergeTree'),
            'CREATE TABLE maintenance.events_copy ON CLUSTER {cluster} ENGINE = MergeTree '
            'PARTITION BY (toDate(created_at), name) '
            'ORDER BY (created_at, name) AS SELECT name, created_at FROM events',
        ),
    ])
    def test_create_table(self, query: QueryProtocol, sql_exp: str):
        self.assertEqual(query.get_sql(), sql_exp)
