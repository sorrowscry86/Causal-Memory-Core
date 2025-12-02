# Causal Memory Core - Railway MCP Client

## Overview

This MCP client allows you to interact with the Railway-hosted Causal Memory Core instance through the Model Context Protocol (MCP). Instead of running the memory core locally, all operations are proxied to the production REST API.

## Architecture

```
Claude Desktop (MCP Client)
    ↓ stdio
mcp_railway_client.py (MCP Server/Proxy)
    ↓ HTTPS/REST
Railway Production API (causal-memory-core-production.up.railway.app)
    ↓
PostgreSQL/DuckDB Database
```

## Configuration

### Environment Variables

- `RAILWAY_BASE_URL`: Base URL for the Railway deployment (default: `https://causal-memory-core-production.up.railway.app`)
- `API_KEY`: Optional API key for authenticated requests (set `CMC_API_KEY` in your environment)

### Claude Desktop Configuration

Add to your Claude Desktop `mcp.json`:

```json
{
  "mcpServers": {
    "causal-memory-railway": {
      "type": "stdio",
      "command": "python",
      "args": ["d:/Development/Causal Memory Core/src/mcp_railway_client.py"],
      "env": {
        "RAILWAY_BASE_URL": "https://causal-memory-core-production.up.railway.app",
        "API_KEY": "${env:CMC_API_KEY}"
      }
    }
  }
}
```

## Available Tools

### `add_event`
Add a new event to the Railway-hosted memory system.

**Parameters:**
- `effect` (string, required): Description of the event

**Example:**
```json
{
  "effect": "Deployed new Railway MCP client for remote memory access"
}
```

### `query`
Query the Railway-hosted causal memory and retrieve narrative chains.

**Parameters:**
- `query` (string, required): Search query for memory retrieval

**Example:**
```json
{
  "query": "What led to the Railway deployment?"
}
```

### `health_check`
Check the health status of the Railway deployment.

**Returns:**
- Status (healthy/unhealthy)
- Version number
- Database connection status
- Endpoint URL

### `get_stats`
Retrieve memory statistics from the Railway instance.

**Returns:**
- Total events stored
- Linked events (with causal relationships)
- Orphan events (no causal links)
- Chain coverage percentage

## Usage Examples

### From Claude Desktop

After adding the configuration to `mcp.json` and restarting Claude Desktop:

**Add an event:**
```
Use the causal-memory-railway add_event tool to record: "User configured Railway MCP client"
```

**Query memory:**
```
Use the causal-memory-railway query tool to search: "Railway configuration"
```

**Check health:**
```
Use the causal-memory-railway health_check tool
```

**Get statistics:**
```
Use the causal-memory-railway get_stats tool
```

## Comparison: Local vs Railway

| Feature | Local MCP Server | Railway MCP Client |
|---------|------------------|-------------------|
| Database | Local DuckDB file | Shared Railway database |
| Latency | ~10ms | ~200-500ms (network) |
| Persistence | Local machine only | Persistent cloud storage |
| Multi-device | ❌ No | ✅ Yes |
| API Key | Not required | Optional (recommended) |
| Internet Required | ❌ No | ✅ Yes |
| OpenAI API Calls | Direct from local | Server-side (Railway) |

## Troubleshooting

### Connection Refused
- Verify Railway instance is running: `curl https://causal-memory-core-production.up.railway.app/health`
- Check network connectivity
- Ensure no firewall/proxy blocking Railway domain

### 403 Forbidden
- Set `API_KEY` environment variable if the Railway instance requires authentication
- Verify API key matches the one configured on Railway (`API_KEY` env var)

### 503 Service Unavailable
- Railway instance may be starting up (cold start)
- Check Railway dashboard for deployment status
- Wait 30-60 seconds and retry

## Performance Considerations

- **Network Latency**: Remote calls add 200-500ms vs local (<10ms)
- **Caching**: Consider local caching layer for frequently accessed narratives
- **Batch Operations**: Plan to add batch endpoints if you need to add many events at once

## Security

- Always use HTTPS (default with Railway)
- Set `API_KEY` environment variable for production use
- Never commit API keys to version control
- Railway endpoint uses Railway's built-in DDoS protection

## Development

To test the Railway client locally:

```bash
# Set environment variables
export RAILWAY_BASE_URL="https://causal-memory-core-production.up.railway.app"
export CMC_API_KEY="your-api-key-here"

# Run the MCP client
python src/mcp_railway_client.py
```

The client will start in stdio mode and wait for MCP protocol messages.

## Next Steps

1. Add the Railway MCP client to your Claude Desktop configuration
2. Restart Claude Desktop to load the new server
3. Test with a simple `health_check` tool call
4. Begin adding events and querying the shared memory
5. Monitor Railway logs for any errors or performance issues

## Contact

For issues related to:
- **MCP Client**: Check this documentation or `src/mcp_railway_client.py`
- **Railway Deployment**: Check Railway dashboard logs
- **API Server**: See `src/api_server.py` and REST API documentation

---

**VoidCat RDC** | Causal Memory Core Railway Integration  
**Developer**: @sorrowscry86  
**Contact**: SorrowsCry86@voidcat.org
