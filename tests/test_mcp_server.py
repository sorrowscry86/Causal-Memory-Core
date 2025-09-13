"""
Unit tests for the MCP Server module
"""

import unittest
import asyncio
import tempfile
import os
import sys
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import MCP types and server components
import mcp.types as types
import mcp_server


class TestMCPServer(unittest.TestCase):
    """Test suite for the MCP Server functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary database path
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        # Remove the empty file, let DuckDB create it
        os.unlink(self.temp_db_path)
        
        # Reset the global memory_core to ensure clean state
        mcp_server.memory_core = None

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up the temporary database
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
        # Reset global state
        mcp_server.memory_core = None

    @patch('mcp_server.server')
    def test_server_initialization(self, mock_server):
        """Test that the MCP server is properly initialized"""
        # The server should be created with the correct name from config
        self.assertIsNotNone(mcp_server.server)

    def test_handle_list_tools(self):
        """Test that handle_list_tools returns the correct tool definitions"""
        async def run_test():
            tools = await mcp_server.handle_list_tools()
            
            # Should return exactly 2 tools
            self.assertEqual(len(tools), 2)
            
            # Check add_event tool
            add_event_tool = next((tool for tool in tools 
                                  if tool.name == "add_event"), None)
            self.assertIsNotNone(add_event_tool)
            self.assertEqual(add_event_tool.name, "add_event")
            self.assertIn("Add a new event", add_event_tool.description)
            
            # Check input schema for add_event
            schema = add_event_tool.inputSchema
            self.assertEqual(schema["type"], "object")
            self.assertIn("effect", schema["properties"])
            self.assertEqual(schema["required"], ["effect"])
            
            # Check query tool
            query_tool = next((tool for tool in tools 
                              if tool.name == "query"), None)
            self.assertIsNotNone(query_tool)
            self.assertEqual(query_tool.name, "query")
            self.assertIn("Query the causal memory", query_tool.description)
            
            # Check input schema for query
            schema = query_tool.inputSchema
            self.assertEqual(schema["type"], "object")
            self.assertIn("query", schema["properties"])
            self.assertEqual(schema["required"], ["query"])

        # Run the async test
        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_handle_call_tool_add_event_success(self, mock_memory_core_class):
        """Test successful add_event tool call"""
        async def run_test():
            # Setup mock
            mock_memory_instance = Mock()
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core to ensure clean test
            mcp_server.memory_core = None
            
            # Test add_event
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "The user clicked on a file"}
            )
            
            # Verify memory core was initialized
            mock_memory_core_class.assert_called_once()
            
            # Verify add_event was called
            expected_event = "The user clicked on a file"
            mock_memory_instance.add_event.assert_called_once_with(expected_event)
            
            # Verify response
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertEqual(result[0].type, "text")
            self.assertIn("Successfully added event", result[0].text)
            self.assertIn("The user clicked on a file", result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_handle_call_tool_query_success(self, mock_memory_core_class):
        """Test successful query tool call"""
        async def run_test():
            # Setup mock
            mock_memory_instance = Mock()
            test_context = "Test context result"
            mock_memory_instance.get_context.return_value = test_context
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core to ensure clean test
            mcp_server.memory_core = None
            
            # Test query
            result = await mcp_server.handle_call_tool(
                name="query",
                arguments={"query": "How did the file get opened?"}
            )
            
            # Verify memory core was initialized
            mock_memory_core_class.assert_called_once()
            
            # Verify get_context was called
            expected_query = "How did the file get opened?"
            mock_memory_instance.get_context.assert_called_once_with(expected_query)
            
            # Verify response
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertEqual(result[0].type, "text")
            self.assertEqual(result[0].text, "Test context result")

        asyncio.run(run_test())

    def test_handle_call_tool_missing_arguments(self):
        """Test tool calls with missing required arguments"""
        async def run_test():
            # Test add_event without effect
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("'effect' parameter is required", result[0].text)
            
            # Test query without query parameter
            result = await mcp_server.handle_call_tool(
                name="query",
                arguments={}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("'query' parameter is required", result[0].text)

        asyncio.run(run_test())

    def test_handle_call_tool_none_arguments(self):
        """Test tool calls with None arguments"""
        async def run_test():
            # Test with None arguments
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments=None
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("'effect' parameter is required", result[0].text)

        asyncio.run(run_test())

    def test_handle_call_tool_unknown_tool(self):
        """Test calling an unknown tool"""
        async def run_test():
            result = await mcp_server.handle_call_tool(
                name="unknown_tool",
                arguments={"param": "value"}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("Unknown tool: unknown_tool", result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_memory_core_initialization_error(self, mock_memory_core_class):
        """Test handling of memory core initialization errors"""
        async def run_test():
            # Setup mock to raise exception on initialization
            error_msg = "Database connection failed"
            mock_memory_core_class.side_effect = Exception(error_msg)
            
            # Reset global memory_core
            mcp_server.memory_core = None
            
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "Test event"}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("Error initializing Causal Memory Core", 
                         result[0].text)
            self.assertIn("Database connection failed", result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_tool_execution_error(self, mock_memory_core_class):
        """Test handling of errors during tool execution"""
        async def run_test():
            # Setup mock that raises exception during add_event
            mock_memory_instance = Mock()
            error_msg = "Memory operation failed"
            mock_memory_instance.add_event.side_effect = Exception(error_msg)
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core
            mcp_server.memory_core = None
            
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "Test event"}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("Error executing add_event", result[0].text)
            self.assertIn("Memory operation failed", result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_memory_core_reuse(self, mock_memory_core_class):
        """Test that memory core instance is reused across calls"""
        async def run_test():
            # Setup mock
            mock_memory_instance = Mock()
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core
            mcp_server.memory_core = None
            
            # First call
            await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "First event"}
            )
            
            # Second call
            await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "Second event"}
            )
            
            # Memory core should only be initialized once
            mock_memory_core_class.assert_called_once()
            
            # But add_event should be called twice
            self.assertEqual(mock_memory_instance.add_event.call_count, 2)

        asyncio.run(run_test())

    def test_add_event_with_empty_effect(self):
        """Test add_event tool with empty effect string"""
        async def run_test():
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": ""}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("'effect' parameter is required", result[0].text)

        asyncio.run(run_test())

    def test_query_with_empty_query(self):
        """Test query tool with empty query string"""
        async def run_test():
            result = await mcp_server.handle_call_tool(
                name="query",
                arguments={"query": ""}
            )
            
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], types.TextContent)
            self.assertIn("'query' parameter is required", result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.CausalMemoryCore')
    def test_add_event_with_special_characters(self, mock_memory_core_class):
        """Test add_event with special characters and unicode"""
        async def run_test():
            # Setup mock
            mock_memory_instance = Mock()
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core
            mcp_server.memory_core = None
            
            # Test with special characters
            special_text = "User clicked 'Submit' → Action completed! 🎉"
            result = await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": special_text}
            )
            
            # Verify the special characters were passed through correctly
            mock_memory_instance.add_event.assert_called_once_with(
                special_text)
            
            # Verify success response
            self.assertEqual(len(result), 1)
            self.assertIn("Successfully added event", result[0].text)
            self.assertIn(special_text, result[0].text)

        asyncio.run(run_test())

    @patch('mcp_server.logger')
    @patch('mcp_server.CausalMemoryCore')
    def test_logging_behavior(self, mock_memory_core_class, mock_logger):
        """Test that appropriate logging occurs during operations"""
        async def run_test():
            # Setup mock
            mock_memory_instance = Mock()
            mock_memory_core_class.return_value = mock_memory_instance
            
            # Reset global memory_core
            mcp_server.memory_core = None
            
            # Test add_event logging
            await mcp_server.handle_call_tool(
                name="add_event",
                arguments={"effect": "Test event"}
            )
            
            # Verify initialization logging
            init_msg = "Causal Memory Core initialized successfully"
            mock_logger.info.assert_any_call(init_msg)
            
            # Verify event addition logging
            event_msg = "Added event to memory: Test event"
            mock_logger.info.assert_any_call(event_msg)

        asyncio.run(run_test())


if __name__ == '__main__':
    # Set up test environment
    os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
    unittest.main()