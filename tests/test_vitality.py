import math
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore
from config import Config


class TestVitalityConfig(unittest.TestCase):
    def test_decay_rate_default(self):
        self.assertEqual(Config.DECAY_RATE, 0.001)

    def test_access_boost_default(self):
        self.assertEqual(Config.ACCESS_BOOST, 0.2)

    def test_causal_boost_default(self):
        self.assertEqual(Config.CAUSAL_BOOST, 0.1)

    def test_max_ttl_hours_default(self):
        self.assertEqual(Config.MAX_TTL_HOURS, 8760)

    def test_archive_threshold_default(self):
        self.assertEqual(Config.ARCHIVE_THRESHOLD, 0.05)

    def test_maintenance_interval_hours_default(self):
        self.assertEqual(Config.MAINTENANCE_INTERVAL_HOURS, 6)


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmp_path = self.tmp.name
        self.tmp.close()
        os.unlink(self.tmp_path)
        mock_llm = Mock()
        mock_embedder = Mock()
        mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        self.core = CausalMemoryCore(
            db_path=self.tmp_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
        )

    def tearDown(self):
        self.core.close()
        if os.path.exists(self.tmp_path):
            os.unlink(self.tmp_path)

    def test_events_table_has_vitality_column(self):
        cols = [r[0] for r in self.core.conn.execute(
            "SELECT column_name FROM duckdb_columns() WHERE table_name='events'"
        ).fetchall()]
        self.assertIn('vitality', cols)
        self.assertIn('access_count', cols)
        self.assertIn('last_accessed', cols)
        self.assertIn('expires_at', cols)

    def test_events_archive_table_exists(self):
        result = self.core.conn.execute(
            "SELECT table_name FROM duckdb_tables() WHERE table_name='events_archive'"
        ).fetchone()
        self.assertIsNotNone(result)

    def test_events_archive_has_archive_columns(self):
        cols = [r[0] for r in self.core.conn.execute(
            "SELECT column_name FROM duckdb_columns() WHERE table_name='events_archive'"
        ).fetchall()]
        self.assertIn('archived_at', cols)
        self.assertIn('archive_reason', cols)


if __name__ == '__main__':
    unittest.main()
