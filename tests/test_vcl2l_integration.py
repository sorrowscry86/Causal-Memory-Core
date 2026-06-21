"""Tests for vcL2L integration — query_as_ref and add_event_chain methods."""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _make_memory_core(db_path: str) -> CausalMemoryCore:
    """Return a CausalMemoryCore wired to mock LLM + embedder."""
    mock_llm = Mock()
    mock_embedder = Mock()
    mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
    return CausalMemoryCore(
        db_path=db_path,
        llm_client=mock_llm,
        embedding_model=mock_embedder,
    )


def _make_test_chain(
    goal_id: str = "GV-AAAA1111-0001",
    with_learning: bool = True,
    output_text: str = "Fixed the deployment issue at logs/deploy.log",
) -> dict:
    """Build a minimal schema-conformant vcL2L wire chain for testing.

    Uses the actual schema field names: ``op`` and ``output``.
    ``ts_trace`` is required by the REASONING_TRACE schema.
    """
    flags = ["learning"] if with_learning else []
    return {
        "_chain_id": "CHN-TEST0001-0001",
        "_emitter": "test-spirit",
        "_frame_count": 1,
        "frames": [
            {
                "opcode": "REASONING_TRACE",
                "ref_goal_id": goal_id,
                "ts_trace": _now_iso(),
                "steps": [
                    {
                        "step_id": "ST-001",
                        "op": "observe",
                        "output": output_text,
                        "step_confidence": 0.9,
                        "flags": flags,
                    }
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# query_as_ref tests
# ---------------------------------------------------------------------------

class TestQueryAsRef(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        os.unlink(self.temp_db_path)
        self.memory_core = _make_memory_core(self.temp_db_path)

    def tearDown(self):
        self.memory_core.close()
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_query_as_ref_returns_ref_dict(self):
        """Populated memory returns a ref dict with the expected keys."""
        self.memory_core.add_event("The deployment succeeded on the staging cluster.")
        self.memory_core._embedding_cache.clear()

        result = self.memory_core.query_as_ref("deployment", ref_id="CR-042")

        self.assertNotIn("error", result, f"Got error: {result}")
        # make_ref() returns ref_type, not source_type
        for key in ("ref_id", "ref_type", "locator", "resolved", "staleness"):
            self.assertIn(key, result, f"Missing key '{key}' in ref dict")
        self.assertEqual(result["ref_id"], "CR-042")
        self.assertTrue(result["resolved"])
        self.assertEqual(result["staleness"], "fresh")

    def test_query_as_ref_empty_result(self):
        """Empty DB produces an error dict with 'no_context' error key."""
        with patch.object(self.memory_core, '_find_most_relevant_event', return_value=None):
            result = self.memory_core.query_as_ref("anything")

        self.assertEqual(result.get("error"), "no_context")
        self.assertIn("message", result)

    def test_query_as_ref_truncates_long_locator(self):
        """The locator in the returned ref dict is at most 256 characters."""
        long_narrative = "X" * 500

        with patch.object(self.memory_core, 'query', return_value=long_narrative):
            result = self.memory_core.query_as_ref("test", ref_id="CR-001")

        self.assertNotIn("error", result, f"Got error: {result}")
        self.assertLessEqual(len(result["locator"]), 256)

    def test_query_as_ref_default_ref_id(self):
        """Default ref_id is 'CR-001' when not supplied."""
        with patch.object(self.memory_core, 'query', return_value="Some context narrative text."):
            result = self.memory_core.query_as_ref("test")

        self.assertEqual(result.get("ref_id"), "CR-001")


# ---------------------------------------------------------------------------
# add_event_chain tests
# ---------------------------------------------------------------------------

class TestAddEventChain(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        os.unlink(self.temp_db_path)
        self.memory_core = _make_memory_core(self.temp_db_path)

    def tearDown(self):
        self.memory_core.close()
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_add_event_chain_extracts_learning_step(self):
        """Chain with a learning-flagged step uses that step's output text."""
        chain = _make_test_chain(with_learning=True, output_text="Learned: cache invalidation fix")
        # Prepend a non-learning step so learning step is NOT first
        chain["frames"][0]["steps"].insert(0, {
            "step_id": "ST-000",
            "op": "infer",
            "output": "Initial inference about the problem",
            "step_confidence": 0.5,
            "flags": [],
        })
        # Update terminal_step_id is not needed but the two-step chain is valid

        result = self.memory_core.add_event_chain(chain)

        self.assertNotIn("error", result, f"Got error: {result}")
        self.assertEqual(result["extracted_text"], "Learned: cache invalidation fix")

    def test_add_event_chain_falls_back_to_first_step(self):
        """Chain without a learning flag uses the first step's output text."""
        chain = _make_test_chain(
            with_learning=False,
            output_text="Fixed the deployment issue at logs/deploy.log",
        )

        result = self.memory_core.add_event_chain(chain)

        self.assertNotIn("error", result, f"Got error: {result}")
        self.assertEqual(
            result["extracted_text"],
            "Fixed the deployment issue at logs/deploy.log",
        )

    def test_add_event_chain_missing_reasoning_trace(self):
        """Chain without a REASONING_TRACE frame returns the expected error.

        We bypass schema validation by patching _validate_chain so the chain
        reaches the REASONING_TRACE presence check cleanly.
        """
        chain = {
            "_chain_id": "CHN-NORT0001-0001",
            "_emitter": "test",
            "_frame_count": 1,
            "frames": [
                {
                    "opcode": "GOAL_VECTOR",
                    "goal_id": "GV-AAAA1111-0001",
                }
            ],
        }

        import causal_memory_core as _cmc_mod
        with patch.object(_cmc_mod, '_validate_chain', return_value=(True, [])):
            result = self.memory_core.add_event_chain(chain)

        self.assertEqual(result.get("error"), "missing_reasoning_trace")

    def test_add_event_chain_invalid_chain_structure(self):
        """Dict without 'frames' key returns an error dict."""
        result = self.memory_core.add_event_chain({"not_frames": []})

        self.assertEqual(result.get("error"), "invalid_chain")

    def test_add_event_chain_not_a_dict(self):
        """Non-dict input returns an error dict."""
        result = self.memory_core.add_event_chain("not a dict")  # type: ignore[arg-type]

        self.assertEqual(result.get("error"), "invalid_chain")

    def test_add_event_chain_returns_chain_id(self):
        """Result chain_id matches the chain's _chain_id field."""
        chain = _make_test_chain()

        result = self.memory_core.add_event_chain(chain)

        self.assertNotIn("error", result, f"Got error: {result}")
        self.assertEqual(result["chain_id"], "CHN-TEST0001-0001")

    def test_add_event_chain_event_id_is_none(self):
        """event_id in result is None (add_event does not surface an id)."""
        chain = _make_test_chain()

        result = self.memory_core.add_event_chain(chain)

        self.assertNotIn("error", result, f"Got error: {result}")
        self.assertIsNone(result["event_id"])

    def test_add_event_chain_stores_event_in_db(self):
        """The extracted event text is persisted to the database."""
        output_text = "Fixed the deployment issue at logs/deploy.log"
        chain = _make_test_chain(with_learning=True, output_text=output_text)

        self.memory_core.add_event_chain(chain)

        rows = self.memory_core.conn.execute(
            "SELECT effect_text FROM events"
        ).fetchall()
        texts = [r[0] for r in rows]
        self.assertIn(output_text, texts)


if __name__ == "__main__":
    unittest.main()
