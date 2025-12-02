#!/usr/bin/env python3
"""
MCP Client for Causal Memory Core Railway Deployment
Proxies MCP tool calls to the Railway-hosted REST API server
Allows MCP clients to use the remote production instance
"""

import asyncio
import logging
import os
from typing import Optional

import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("causal-memory-railway-client")

# Create server instance (MCP server that proxies to Railway)
server = Server("causal-memory-railway-client")

# Railway endpoint configuration
RAILWAY_BASE_URL = os.getenv(
    "RAILWAY_BASE_URL", 
    "https://causal-memory-core-production.up.railway.app"
)
API_KEY = os.getenv("API_KEY")  # Optional API key for Railway endpoint

# HTTP client with timeout and retry configuration
http_client = httpx.AsyncClient(
    base_url=RAILWAY_BASE_URL,
    timeout=30.0,
    headers={"x-api-key": API_KEY} if API_KEY else {}
)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools (same as local MCP server)"""
    return [
        types.Tool(
            name="add_event",
            description="Add a new event to the causal memory system on Railway. The system will automatically determine causal relationships with previous events using semantic similarity and LLM reasoning, creating links that enable narrative chain reconstruction.",
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
            description="Query the causal memory on Railway",
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
        ),
        types.Tool(
            name="health_check",
            description="Check the health status of the Railway deployment",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        types.Tool(
            name="get_stats",
            description="Get memory statistics from the Railway deployment (total events, linked events, orphan events)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Optional[dict]) -> list[types.TextContent]:
    """Handle tool calls by proxying to Railway REST API"""
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
            
            # POST to /events endpoint
            response = await http_client.post(
                "/events",
                json={"effect_text": effect}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Added event to Railway: {effect}")
            return [types.TextContent(
                type="text",
                text=f"Successfully added event to Railway memory: {effect}"
            )]
            
        elif name == "query":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            # POST to /query endpoint
            response = await http_client.post(
                "/query",
                json={"query": query}
            )
            response.raise_for_status()
            
            result = response.json()
            narrative = result.get("narrative", "No context found")
            logger.info(f"Retrieved context from Railway for query: {query}")
            return [types.TextContent(
                type="text",
                text=narrative
            )]
            
        elif name == "health_check":
            # GET /health endpoint
            response = await http_client.get("/health")
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status", "unknown")
            version = result.get("version", "unknown")
            db_connected = result.get("database_connected", False)
            
            health_text = (
                f"Railway Instance Health Check:\n"
                f"Status: {status}\n"
                f"Version: {version}\n"
                f"Database Connected: {db_connected}\n"
                f"Endpoint: {RAILWAY_BASE_URL}"
            )
            
            return [types.TextContent(
                type="text",
                text=health_text
            )]
            
        elif name == "get_stats":
            # GET /stats endpoint
            response = await http_client.get("/stats")
            response.raise_for_status()
            
            result = response.json()
            total = result.get("total_events", 0)
            linked = result.get("linked_events", 0)
            orphan = result.get("orphan_events", 0)
            
            stats_text = (
                f"Railway Memory Statistics:\n"
                f"Total Events: {total}\n"
                f"Linked Events: {linked}\n"
                f"Orphan Events: {orphan}\n"
                f"Chain Coverage: {(linked/total*100 if total > 0 else 0):.1f}%"
            )
            
            return [types.TextContent(
                type="text",
                text=stats_text
            )]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Railway API error ({e.response.status_code}): {e.response.text}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=error_msg
        )]
    except httpx.RequestError as e:
        error_msg = f"Railway connection error: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=error_msg
        )]
    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


def _build_initialization_options() -> InitializationOptions:
    return InitializationOptions(
        server_name="causal-memory-railway-client",
        server_version=Config.MCP_SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )


async def _run_stdio_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            _build_initialization_options(),
        )


async def main():
    """Main entry point for the Railway MCP client"""
    logger.info(f"Starting Railway MCP client (proxying to {RAILWAY_BASE_URL})")
    await _run_stdio_server()


if __name__ == "__main__":
    asyncio.run(main())
