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


if __name__ == '__main__':
    unittest.main()
