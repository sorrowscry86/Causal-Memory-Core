#!/usr/bin/env python3
"""
MCP Server for the Causal Memory Core
Exposes memory.add_event and memory.query tools via the Model Context Protocol
Supports dual transports: stdio for local usage and Starlette/uvicorn SSE for cloud deployments (Railway, etc.).
"""

import asyncio
import logging
import os

# MCP SDK imports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

try:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.requests import Request
    import uvicorn
except ImportError:  # pragma: no cover - optional SSE deps
    SseServerTransport = None
    Starlette = None
    Response = None
    Request = None
    Route = None
    uvicorn = None

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
            description="Query the causal memory",
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

def _build_initialization_options() -> InitializationOptions:
    return InitializationOptions(
        server_name=Config.MCP_SERVER_NAME,
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


async def _run_sse_server(port: str) -> None:
    if Starlette is None or SseServerTransport is None or uvicorn is None or Response is None or Request is None:
        raise RuntimeError("SSE deployment requires starlette+uvicorn+mcp.server.sse dependencies")

    app = Starlette(debug=False)
    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(
                streams[0],
                streams[1],
                _build_initialization_options(),
            )

    async def handle_messages(request: Request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    async def handle_health(request: Request) -> Response:
        return Response("Causal Memory Core MCP Active 🧠", media_type="text/plain")

    app.add_route("/sse", handle_sse, methods=["GET"])
    app.add_route("/messages", handle_messages, methods=["POST"])
    app.add_route("/", handle_health, methods=["GET"])

    config = uvicorn.Config(app, host="0.0.0.0", port=int(port), log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


async def main():
    """Main entry point for the MCP server"""
    http_port = os.getenv("PORT")
    if http_port:
        if Starlette is None or uvicorn is None or SseServerTransport is None:
            logger.error(
                "PORT is set but SSE dependencies (starlette, uvicorn, mcp.server.sse) are missing."
            )
            raise RuntimeError("Missing SSE dependencies for cloud deployment")
        logger.info("Detected PORT=%s, starting SSE server", http_port)
        await _run_sse_server(http_port)
    else:
        logger.info("Starting stdio server (no PORT detected)")
        await _run_stdio_server()

if __name__ == "__main__":
    asyncio.run(main())
