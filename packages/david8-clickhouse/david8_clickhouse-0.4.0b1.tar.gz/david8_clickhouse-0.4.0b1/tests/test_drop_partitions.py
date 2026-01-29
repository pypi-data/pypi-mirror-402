from parameterized import parameterized

from david8_clickhouse.protocols.sql import SelectProtocol
from tests.base_test import BaseTest


class TestDropPartitions(BaseTest):
    @parameterized.expand([
        (
            BaseTest.qb.drop_partitions('events', [20260101]),
            'ALTER TABLE events DROP PARTITION 20260101',
        ),
        (
            BaseTest.qb_w.drop_partitions('events', ["2026-01-01"]),
            'ALTER TABLE "events" DROP PARTITION \'2026-01-01\'',
        ),
        (
            BaseTest.qb.drop_partitions('events', [20260101], on_cluster='games'),
            'ALTER TABLE events ON CLUSTER games DROP PARTITION 20260101',
        ),
        (
            BaseTest.qb_w.drop_partitions('events', ['2026-01-01', '2026-01-02'], 'raw', on_cluster='{cluster}'),
            "ALTER TABLE \"raw\".\"events\" ON CLUSTER {cluster} DROP PARTITION '2026-01-01', "
            "DROP PARTITION '2026-01-02'",
        ),
        (
            BaseTest.qb.drop_partitions('events', [(202601, 'PL'), (202601, 'BY')], 'raw', on_cluster='{cluster}'),
            "ALTER TABLE raw.events ON CLUSTER {cluster} DROP PARTITION (202601, 'PL'), "
            "DROP PARTITION (202601, 'BY')",
        ),
    ])
    def test_drop_partitions(self, query: SelectProtocol, exp_sql):
        self.assertEqual(query.get_sql(), exp_sql)
