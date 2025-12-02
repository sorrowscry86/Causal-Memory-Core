#!/bin/bash
# Start both REST API and MCP server on Railway

# Determine which server to run based on SERVICE_TYPE env var
if [ "$SERVICE_TYPE" = "mcp" ]; then
    echo "Starting MCP Server (SSE) on port $PORT"
    exec python src/mcp_server.py
else
    echo "Starting REST API Server on port $PORT"
    exec python src/api_server.py
fi
