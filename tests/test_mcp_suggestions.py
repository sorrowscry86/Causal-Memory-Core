"""
Unit tests for Week 3 suggestion skeleton in MCP server.
Validates tool exposure via flag, parameter validation, and ranking output.
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


class TestMCPSuggestions(unittest.TestCase):
    def test_suggestions_tool_visibility(self):
        async def run_case(enabled: bool):
            with patch('config.Config.PREPROCESSOR_SUGGESTIONS_ENABLED', enabled):
                tools = await mcp_server.handle_list_tools()
                return [t.name for t in tools]

        names = asyncio.run(run_case(False))
        self.assertNotIn('preprocessor_suggestions', names)

        names = asyncio.run(run_case(True))
        self.assertIn('preprocessor_suggestions', names)

    def test_suggestions_requires_text(self):
        async def run_case(args):
            with patch('config.Config.PREPROCESSOR_SUGGESTIONS_ENABLED', True):
                return await mcp_server.handle_call_tool('preprocessor_suggestions', args)

        result = asyncio.run(run_case({}))
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], types.TextContent)
        self.assertIn("'text' parameter is required", result[0].text)

    def test_suggestions_basic_output(self):
        async def run_case(text: str, top_k=None):
            with patch('config.Config.PREPROCESSOR_SUGGESTIONS_ENABLED', True), \
                 patch('config.Config.PREPROCESSOR_SUGGESTION_TOP_K', 2):
                args = {"text": text}
                if top_k is not None:
                    args["top_k"] = top_k
                return await mcp_server.handle_call_tool('preprocessor_suggestions', args)

        # Use a text that should match known phrases e.g. "open file"
        result = asyncio.run(run_case("please open file and run tests"))
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], types.TextContent)
        # Should be a JSON-like list string; just check it contains expected category keys
        self.assertIn("category", result[0].text)
        self.assertIn("phrase", result[0].text)
        self.assertIn("score", result[0].text)


if __name__ == '__main__':
    unittest.main()