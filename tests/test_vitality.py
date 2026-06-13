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


class TestInsertEvent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmp_path = self.tmp.name
        self.tmp.close()
        os.unlink(self.tmp_path)
        self.mock_llm = Mock()
        self.mock_llm.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="No."))]
        )
        mock_embedder = Mock()
        mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        self.core = CausalMemoryCore(
            db_path=self.tmp_path,
            llm_client=self.mock_llm,
            embedding_model=mock_embedder,
        )

    def tearDown(self):
        self.core.close()
        if os.path.exists(self.tmp_path):
            os.unlink(self.tmp_path)

    def test_new_event_starts_at_full_vitality(self):
        self.core.add_event("test event")
        row = self.core.conn.execute("SELECT vitality FROM events").fetchone()
        self.assertEqual(row[0], 1.0)

    def test_new_event_access_count_is_zero(self):
        self.core.add_event("test event")
        row = self.core.conn.execute("SELECT access_count FROM events").fetchone()
        self.assertEqual(row[0], 0)

    def test_new_event_expires_at_is_set(self):
        self.core.add_event("test event")
        row = self.core.conn.execute("SELECT expires_at FROM events").fetchone()
        self.assertIsNotNone(row[0])

    def test_new_event_last_accessed_is_set(self):
        self.core.add_event("test event")
        row = self.core.conn.execute("SELECT last_accessed FROM events").fetchone()
        self.assertIsNotNone(row[0])


class TestCausalBoost(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmp_path = self.tmp.name
        self.tmp.close()
        os.unlink(self.tmp_path)
        self.mock_llm = Mock()
        mock_embedder = Mock()
        mock_embedder.encode.return_value = np.array([0.9, 0.1, 0.0, 0.0])
        self.core = CausalMemoryCore(
            db_path=self.tmp_path,
            llm_client=self.mock_llm,
            embedding_model=mock_embedder,
        )

    def tearDown(self):
        self.core.close()
        if os.path.exists(self.tmp_path):
            os.unlink(self.tmp_path)

    def test_apply_causal_boost_increases_vitality(self):
        self.mock_llm.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="No."))]
        )
        self.core.add_event("parent event")
        parent_id = self.core.conn.execute("SELECT event_id FROM events").fetchone()[0]
        self.core.conn.execute("UPDATE events SET vitality = 0.5 WHERE event_id = ?", [parent_id])

        self.core._apply_causal_boost(parent_id)

        new_vitality = self.core.conn.execute(
            "SELECT vitality FROM events WHERE event_id = ?", [parent_id]
        ).fetchone()[0]
        self.assertAlmostEqual(new_vitality, 0.6, places=5)

    def test_causal_boost_capped_at_one(self):
        self.mock_llm.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="No."))]
        )
        self.core.add_event("parent event")
        parent_id = self.core.conn.execute("SELECT event_id FROM events").fetchone()[0]
        self.core._apply_causal_boost(parent_id)
        vitality = self.core.conn.execute(
            "SELECT vitality FROM events WHERE event_id = ?", [parent_id]
        ).fetchone()[0]
        self.assertLessEqual(vitality, 1.0)

    def test_causal_boost_noop_for_missing_event(self):
        self.core._apply_causal_boost(99999)


if __name__ == '__main__':
    unittest.main()
