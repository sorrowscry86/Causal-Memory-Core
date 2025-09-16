#!/usr/bin/env python3
"""
MCP Server for the Causal Memory Core
Exposes memory.add_event and memory.query tools via the Model Context Protocol
"""

import asyncio
import logging
from typing import Any, Sequence

# MCP SDK imports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from causal_memory_core import CausalMemoryCore
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("causal-memory-mcp")

# Create server instance
server = Server(Config.MCP_SERVER_NAME)

# Global memory core instance
memory_core = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="add_event",
            description="Add a new event to the causal memory system. The system will automatically determine causal relationships with previous events using semantic similarity and LLM reasoning, creating links that enable narrative chain reconstruction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "effect": {
                        "type": "string",
                        "description": "Description of the event that occurred (the effect). Should be a clear, concise statement from the agent's perspective. The system will analyze this against recent events to detect causal relationships."
                    }
                },
                "required": ["effect"]
            }
        ),
        types.Tool(
            name="query",
            description="Queries the memory and returns a full, narrative chain of causally-linked events related to the query. Performs semantic search to find the most relevant event, then traces backward through causal links to reconstruct the complete story from root cause to final effect.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for in memory. Can be a question, topic, or description of an event. The system will return the complete causal narrative leading to the most relevant event."
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool calls"""
    global memory_core
    
    # Initialize memory core if not already done
    if memory_core is None:
        try:
            memory_core = CausalMemoryCore()
            logger.info("Causal Memory Core initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Causal Memory Core: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error initializing Causal Memory Core: {str(e)}"
            )]
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "add_event":
            effect = arguments.get("effect")
            if not effect:
                return [types.TextContent(
                    type="text",
                    text="Error: 'effect' parameter is required"
                )]
            
            memory_core.add_event(effect)
            logger.info(f"Added event to memory: {effect}")
            return [types.TextContent(
                type="text",
                text=f"Successfully added event to memory: {effect}"
            )]
            
        elif name == "query":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            context = memory_core.get_context(query)
            logger.info(f"Retrieved context for query: {query}")
            return [types.TextContent(
                type="text",
                text=context
            )]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main entry point for the MCP server"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=Config.MCP_SERVER_NAME,
                server_version=Config.MCP_SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
