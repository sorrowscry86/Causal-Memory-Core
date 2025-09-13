"""
End-to-End Tests for Causal Memory Core MCP Server
Tests complete user workflows through the MCP (Model Context Protocol) server interface
"""

import pytest
import asyncio
import tempfile
import os
import json
import sys
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import mcp.types as types


class TestCausalMemoryCoreMCPServerE2E:
    """End-to-End tests for the MCP Server interface"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db.name
        temp_db.close()
        os.unlink(temp_db_path)  # Let DuckDB create the file
        yield temp_db_path
        # Cleanup
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    @pytest.fixture
    def mock_memory_core(self):
        """Mock memory core for MCP server testing"""
        mock_core = Mock()
        mock_core.add_event.return_value = None
        mock_core.get_context.return_value = "Mock context response"
        return mock_core
    
    @pytest.fixture
    def mcp_server_module(self):
        """Import MCP server module with mocked dependencies"""
        with patch.dict(sys.modules, {
            'causal_memory_core': Mock(),
            'config': Mock()
        }):
            import mcp_server
            return mcp_server
    
    @pytest.mark.asyncio
    async def test_e2e_list_tools(self, mcp_server_module):
        """Test listing available MCP tools"""
        # Import the handler function
        from mcp_server import handle_list_tools
        
        # Call the list tools handler
        tools = await handle_list_tools()
        
        # Verify tools are returned
        assert isinstance(tools, list)
        assert len(tools) == 2  # add_event and query
        
        # Verify add_event tool
        add_event_tool = next((tool for tool in tools if tool.name == "add_event"), None)
        assert add_event_tool is not None
        assert add_event_tool.description is not None
        assert "effect" in add_event_tool.inputSchema["properties"]
        
        # Verify query tool
        query_tool = next((tool for tool in tools if tool.name == "query"), None)
        assert query_tool is not None
        assert query_tool.description is not None
        assert "query" in query_tool.inputSchema["properties"]
    
    @pytest.mark.asyncio
    async def test_e2e_add_event_tool(self, mock_memory_core, mcp_server_module):
        """Test add_event tool end-to-end workflow"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Call add_event tool
            result = await handle_call_tool("add_event", {
                "effect": "User clicked the submit button"
            })
            
            # Verify response
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert "Successfully added event" in result[0].text
            assert "User clicked the submit button" in result[0].text
            
            # Verify memory core was called
            mock_memory_core.add_event.assert_called_once_with("User clicked the submit button")
    
    @pytest.mark.asyncio
    async def test_e2e_query_tool(self, mock_memory_core, mcp_server_module):
        """Test query tool end-to-end workflow"""
        mock_memory_core.get_context.return_value = "Initially, User opened the application."
        
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Call query tool
            result = await handle_call_tool("query", {
                "query": "application startup sequence"
            })
            
            # Verify response
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert "Initially," in result[0].text
            
            # Verify memory core was called
            mock_memory_core.get_context.assert_called_once_with("application startup sequence")
    
    @pytest.mark.asyncio
    async def test_e2e_tool_workflow_sequence(self, mock_memory_core, mcp_server_module):
        """Test complete workflow: add events -> query -> verify results"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Step 1: Add first event
            result1 = await handle_call_tool("add_event", {
                "effect": "User opened file browser"
            })
            assert "Successfully added event" in result1[0].text
            
            # Step 2: Add second related event  
            result2 = await handle_call_tool("add_event", {
                "effect": "User selected a document file"
            })
            assert "Successfully added event" in result2[0].text
            
            # Step 3: Query for context about the workflow
            mock_memory_core.get_context.return_value = "Initially: User opened file browser\\nThis led to: User selected a document file"
            
            result3 = await handle_call_tool("query", {
                "query": "file selection workflow"
            })
            assert "Initially:" in result3[0].text
            assert "This led to:" in result3[0].text
            
            # Verify all calls were made
            assert mock_memory_core.add_event.call_count == 2
            mock_memory_core.get_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_e2e_error_handling_missing_parameters(self, mock_memory_core, mcp_server_module):
        """Test error handling when required parameters are missing"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Test add_event without effect parameter
            result1 = await handle_call_tool("add_event", {})
            assert "Error: 'effect' parameter is required" in result1[0].text
            
            # Test query without query parameter
            result2 = await handle_call_tool("query", {})
            assert "Error: 'query' parameter is required" in result2[0].text
            
            # Verify memory core was not called
            mock_memory_core.add_event.assert_not_called()
            mock_memory_core.get_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_e2e_error_handling_unknown_tool(self, mock_memory_core, mcp_server_module):
        """Test error handling for unknown tool calls"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            result = await handle_call_tool("unknown_tool", {
                "some_param": "some_value"
            })
            
            assert "Unknown tool: unknown_tool" in result[0].text
            
            # Verify memory core was not called
            mock_memory_core.add_event.assert_not_called()
            mock_memory_core.get_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_e2e_memory_core_initialization_error(self, mcp_server_module):
        """Test error handling when memory core fails to initialize"""
        with patch('mcp_server.memory_core', None):
            with patch('mcp_server.CausalMemoryCore') as mock_constructor:
                mock_constructor.side_effect = Exception("Database connection failed")
                
                from mcp_server import handle_call_tool
                
                result = await handle_call_tool("add_event", {
                    "effect": "Some event"
                })
                
                assert "Error initializing Causal Memory Core" in result[0].text
                assert "Database connection failed" in result[0].text
    
    @pytest.mark.asyncio
    async def test_e2e_memory_core_operation_error(self, mock_memory_core, mcp_server_module):
        """Test error handling when memory core operations fail"""
        # Mock memory core to raise exception
        mock_memory_core.add_event.side_effect = Exception("Memory storage failed")
        
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            result = await handle_call_tool("add_event", {
                "effect": "Some event"
            })
            
            assert "Error executing add_event" in result[0].text
            assert "Memory storage failed" in result[0].text
    
    @pytest.mark.asyncio
    async def test_e2e_special_characters_in_tools(self, mock_memory_core, mcp_server_module):
        """Test MCP tools with special characters and unicode"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Test with special characters
            special_events = [
                "User typed: Hello, World! (with punctuation)",
                "Error: Cannot access file '/path/to/file'", 
                "User entered: αβγδε (Greek letters)",
                "Success! ✅ Task completed",
                "Data: {\"key\": \"value\", \"number\": 42}"
            ]
            
            for event in special_events:
                result = await handle_call_tool("add_event", {"effect": event})
                assert "Successfully added event" in result[0].text
                assert event in result[0].text
            
            # Test query with special characters
            mock_memory_core.get_context.return_value = "Context with émojis: 🎉 and symbols: @#$%"
            
            result = await handle_call_tool("query", {
                "query": "special characters and symbols"
            })
            
            assert "émojis: 🎉" in result[0].text
            assert "@#$%" in result[0].text
    
    @pytest.mark.asyncio
    async def test_e2e_long_content_handling(self, mock_memory_core, mcp_server_module):
        """Test MCP tools with very long content"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Create very long event description
            long_event = "User performed a complex workflow involving " + "many detailed steps " * 100
            
            result = await handle_call_tool("add_event", {"effect": long_event})
            
            assert "Successfully added event" in result[0].text
            # Verify the long content is handled properly
            mock_memory_core.add_event.assert_called_with(long_event)
            
            # Test long query response
            long_context = "This is a very detailed context response that includes " + "extensive information " * 50
            mock_memory_core.get_context.return_value = long_context
            
            result = await handle_call_tool("query", {"query": "detailed information"})
            
            assert long_context in result[0].text
    
    @pytest.mark.asyncio
    async def test_e2e_concurrent_tool_calls(self, mock_memory_core, mcp_server_module):
        """Test handling of concurrent MCP tool calls"""
        with patch('mcp_server.memory_core', mock_memory_core):
            from mcp_server import handle_call_tool
            
            # Create multiple concurrent tool calls
            tasks = []
            for i in range(5):
                task = handle_call_tool("add_event", {
                    "effect": f"Concurrent event {i}"
                })
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all calls succeeded
            assert len(results) == 5
            for i, result in enumerate(results):
                assert "Successfully added event" in result[0].text
                assert f"Concurrent event {i}" in result[0].text
            
            # Verify all events were added to memory core
            assert mock_memory_core.add_event.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])