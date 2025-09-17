"""
Unit tests for MCP preprocessor (Week 2) behavior.
Covers: classification, semantic mapping thresholding, metrics, recent bounding,
fail-open behavior, and debug tool visibility. These tests only affect behavior
when PREPROCESSOR flags are enabled.
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import patch

# Ensure repo src is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mcp_server  # noqa: E402
import mcp.types as types  # noqa: E402


class TestMCPPreprocessor(unittest.TestCase):
    def setUp(self):
        # Reset metrics for clean state
        mcp_server._metrics = {
            "total_calls": 0,
            "total_query_calls": 0,
            "total_event_calls": 0,
            "classifications": {qt.value: 0 for qt in mcp_server.QueryType},
            "translations_applied": 0,
            "translations_rejected": 0,
            "errors": 0,
            "recent": [],
        }

    # ----- Classification paths -----
    def test_classifier_paths(self):
        clf = mcp_server._classifier
        self.assertEqual(clf.classify_query("add event now"), mcp_server.QueryType.DIRECT_KEYWORD)
        self.assertEqual(clf.classify_query("why did this happen?"), mcp_server.QueryType.CONCEPTUAL)
        self.assertEqual(clf.classify_query("This led to that"), mcp_server.QueryType.CAUSAL)
        self.assertEqual(clf.classify_query("random unrelated"), mcp_server.QueryType.UNKNOWN)

    # ----- add_event path is pass-through even when enabled -----
    @patch('config.Config.PREPROCESSOR_ENABLED', True)
    def test_add_event_pass_through(self):
        input_text = "Create new record"
        out = mcp_server.preprocess_input(input_text, mode="add_event")
        self.assertEqual(out, input_text)

    # ----- Mapping application vs rejection by threshold -----
    @patch('config.Config.PREPROCESSOR_ENABLED', True)
    @patch('config.Config.PREPROCESSOR_CONFIDENCE_THRESHOLD', 0.9)
    def test_mapping_applied_when_above_threshold(self):
        # Use a phrase that has an exact mapping for deterministic confidence=1.0
        # "retrieve context" exists in SEMANTIC_MAPPINGS["memory systems"]
        text = "retrieve context"
        out = mcp_server.preprocess_input(text, mode="query")
        # When translated, output equals the best match phrase (same string here)
        self.assertEqual(out, "retrieve context")
        self.assertEqual(mcp_server._metrics["translations_applied"], 1)
        self.assertEqual(mcp_server._metrics["translations_rejected"], 0)

    @patch('config.Config.PREPROCESSOR_ENABLED', True)
    @patch('config.Config.PREPROCESSOR_CONFIDENCE_THRESHOLD', 0.95)
    def test_mapping_rejected_when_below_threshold(self):
        # Similar but not exact to ensure confidence < 0.95
        # Input tokens: {open, file, now}; mapping "open file" => 2/3 ~= 0.666
        text = "open file now"
        out = mcp_server.preprocess_input(text, mode="query")
        self.assertEqual(out, text)  # Kept original
        self.assertEqual(mcp_server._metrics["translations_applied"], 0)
        self.assertEqual(mcp_server._metrics["translations_rejected"], 1)

    # ----- Metrics increments and recent list bounding -----
    @patch('config.Config.PREPROCESSOR_ENABLED', True)
    @patch('config.Config.PREPROCESSOR_CONFIDENCE_THRESHOLD', 0.0)
    @patch('config.Config.PREPROCESSOR_METRICS_RECENT_LIMIT', 3)
    def test_metrics_and_recent_bounding(self):
        # Force all to apply translation by using very low threshold
        for i in range(5):
            mcp_server.preprocess_input(f"unit tests {i}", mode="query")
        self.assertEqual(mcp_server._metrics["total_calls"], 5)
        self.assertEqual(mcp_server._metrics["total_query_calls"], 5)
        self.assertEqual(mcp_server._metrics["translations_applied"], 5)
        self.assertEqual(len(mcp_server._metrics["recent"]), 3)  # bounded

    # ----- Fail-open on classifier exception -----
    @patch('config.Config.PREPROCESSOR_ENABLED', True)
    @patch('config.Config.PREPROCESSOR_FAIL_OPEN', True)
    def test_fail_open_on_exception(self):
        original = mcp_server._classifier.classify_query
        try:
            def boom(_):
                raise RuntimeError("boom")
            mcp_server._classifier.classify_query = boom
            text = "some query"
            out = mcp_server.preprocess_input(text, mode="query")
            self.assertEqual(out, text)  # fail-open returns original
        finally:
            mcp_server._classifier.classify_query = original

    # ----- Debug tool visibility only when both flags enabled -----
    def test_debug_tool_visibility(self):
        async def run_case(enable_preproc: bool, enable_debug: bool):
            with patch('config.Config.PREPROCESSOR_ENABLED', enable_preproc), \
                 patch('config.Config.PREPROCESSOR_DEBUG_ENABLED', enable_debug):
                tools = await mcp_server.handle_list_tools()
                names = [t.name for t in tools]
                return names

        # Off -> no debug tool
        names = asyncio.run(run_case(False, False))
        self.assertNotIn('preprocessor_debug_metrics', names)

        # On but debug off -> no debug tool
        names = asyncio.run(run_case(True, False))
        self.assertNotIn('preprocessor_debug_metrics', names)

        # Both on -> debug tool present
        names = asyncio.run(run_case(True, True))
        self.assertIn('preprocessor_debug_metrics', names)


if __name__ == '__main__':
    unittest.main()