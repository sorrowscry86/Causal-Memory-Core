# Causal Memory Core - Railway MCP Server (SSE)

## Overview

The Railway deployment now exposes the Causal Memory Core as a **remote MCP server** using SSE (Server-Sent Events) transport. Claude Desktop and other MCP clients can connect directly to the Railway instance without needing a local proxy.

## Architecture

```
Claude Desktop (MCP Client)
    ↓ HTTPS/SSE
Railway MCP Server (causal-memory-core-production.up.railway.app)
    ↓
DuckDB Database (persistent volume)
```

## Railway Configuration

The MCP server automatically switches to SSE mode when the `PORT` environment variable is detected (which Railway provides automatically).

### Railway Environment Variables

Set these in your Railway project dashboard:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key
PORT=8000  # Automatically set by Railway

# Optional (with defaults)
DB_PATH=/app/data/causal_memory.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
MAX_POTENTIAL_CAUSES=7
SIMILARITY_THRESHOLD=0.6
TIME_DECAY_HOURS=168
```

### Railway Deployment

The MCP server will run on Railway with these endpoints:

- `GET /` - Health check endpoint
- `GET /sse` - SSE endpoint for MCP client connections
- `POST /messages` - MCP message endpoint

## Claude Desktop Configuration

Add to your Claude Desktop `mcp.json`:

```json
{
  "mcpServers": {
    "causal-memory-railway": {
      "type": "sse",
      "url": "https://causal-memory-core-production.up.railway.app/sse"
    }
  }
}
```

**That's it!** No local Python process needed. Claude Desktop connects directly to Railway.

## Available Tools

### `add_event`

Add a new event to the Railway-hosted memory system.

**Parameters:**

- `effect` (string, required): Description of the event

**Example:**

```json
{
  "effect": "Deployed Railway MCP server with SSE transport"
}
```

### `query`

Query the Railway-hosted causal memory and retrieve narrative chains.

**Parameters:**

- `query` (string, required): Search query for memory retrieval

**Example:**

```json
{
  "query": "What caused the Railway deployment?"
}
```

## Usage Examples

### From Claude Desktop

After adding the SSE configuration to `mcp.json` and restarting Claude Desktop:

**Add an event:**

```
Use the causal-memory-railway add_event tool to record: "Configured Railway MCP server with SSE transport"
```

**Query memory:**

```
Use the causal-memory-railway query tool to search: "Railway MCP deployment"
```

## Comparison: stdio vs SSE

| Feature | stdio (Local) | SSE (Railway) |
|---------|---------------|---------------|
| Connection | Process pipes | HTTPS/SSE |
| Location | Local machine | Remote cloud |
| Setup | Python + dependencies | Just URL |
| Database | Local DuckDB | Shared Railway DB |
| Multi-device | ❌ No | ✅ Yes |
| Latency | ~10ms | ~200-500ms |
| Persistence | Local only | Persistent cloud |
| Auto-start | Manual | Always running |

## Testing the Connection

### 1. Verify Railway Health

```bash
curl https://causal-memory-core-production.up.railway.app/
```

**Expected response:**

```
Causal Memory Core MCP Active 🧠
```

### 2. Test SSE Endpoint

```bash
curl https://causal-memory-core-production.up.railway.app/sse
```

**Expected:** SSE connection opens (Claude Desktop will handle the MCP protocol handshake)

### 3. Check Claude Desktop

After adding the config and restarting:

1. Look for `causal-memory-railway` in the MCP servers list
2. The server should show as "Connected"
3. Test with any tool call

## Troubleshooting

### Connection Failed

**Issue:** Claude Desktop can't connect to SSE endpoint

**Solutions:**

- Verify Railway instance is running (check Railway dashboard)
- Test health endpoint: `curl https://causal-memory-core-production.up.railway.app/`
- Check Railway logs for startup errors
- Ensure no corporate firewall blocking Railway domain

### Server Not Listed in Claude Desktop

**Issue:** `causal-memory-railway` doesn't appear in MCP servers

**Solutions:**

- Verify `mcp.json` syntax is correct (use JSON validator)
- Restart Claude Desktop completely (quit and reopen)
- Check Claude Desktop logs for configuration errors
- Ensure `type: "sse"` is set (not `stdio`)

### Tool Calls Fail

**Issue:** Tools are listed but calls return errors

**Solutions:**

- Check Railway logs for server-side errors
- Verify `OPENAI_API_KEY` is set on Railway
- Ensure Railway instance has enough memory (512MB+ recommended)
- Check database path and permissions

### Cold Start Delays

**Issue:** First request after inactivity is slow

**Railway cold starts** can take 30-60 seconds if the instance was idle. Solutions:

- Accept the delay (free tier behavior)
- Upgrade to Railway Pro for always-on instances
- Implement a health check ping every 5 minutes

## Performance Optimization

### Railway Instance Configuration

**Recommended settings:**

- **Memory**: 512MB minimum (1GB for heavy usage)
- **Region**: Choose closest to your location
- **Persistent Volume**: Mount at `/app/data` for database

### Database Persistence

Ensure your Railway project has a persistent volume mounted:

```toml
# railway.toml
[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"

[[volumes]]
mountPath = "/app/data"
```

Set `DB_PATH=/app/data/causal_memory.db` in Railway environment variables.

### Rate Limiting

The MCP server has no built-in rate limiting. For production:

- Use Railway's built-in DDoS protection
- Monitor usage in Railway dashboard
- Consider adding authentication if needed

## Security

### Public Endpoint Considerations

The Railway MCP server is **publicly accessible** by default. Security measures:

1. **No authentication** - Anyone with the URL can use the tools
2. **Consider adding API key authentication** if needed
3. **Monitor Railway logs** for suspicious activity
4. **Use Railway's built-in protections** (DDoS, rate limiting)

### Adding Authentication (Optional)

To add API key authentication, modify the Railway environment:

```bash
API_KEY=your-secret-key-here
```

Update `mcp_server.py` to check this key on SSE connections (requires code modification).

## Development

### Local Testing of SSE Mode

Run the MCP server in SSE mode locally:

```bash
# Set PORT to enable SSE mode
export PORT=8000
export OPENAI_API_KEY=your-key

# Run server
python src/mcp_server.py
```

Server will start on `http://localhost:8000` with SSE endpoints.

Test the connection:

```bash
curl http://localhost:8000/
```

### Deploying Updates

1. Push changes to GitHub
2. Railway auto-deploys from `main` branch
3. Monitor Railway build logs
4. Test SSE endpoint after deployment
5. Restart Claude Desktop to pick up changes

## Migration from stdio to SSE

If you're currently using the local stdio MCP server:

**Old configuration:**

```json
{
  "mcpServers": {
    "causal-memory": {
      "type": "stdio",
      "command": "python",
      "args": ["d:/Development/Causal Memory Core/src/mcp_server.py"]
    }
  }
}
```

**New configuration:**

```json
{
  "mcpServers": {
    "causal-memory-railway": {
      "type": "sse",
      "url": "https://causal-memory-core-production.up.railway.app/sse"
    }
  }
}
```

**Migration steps:**

1. Export existing local database (if you want to preserve events)
2. Update `mcp.json` with new SSE configuration
3. Restart Claude Desktop
4. Test the Railway connection
5. Optionally import local events to Railway (requires manual script)

## Monitoring

### Railway Dashboard

Monitor your MCP server:

- **Metrics**: CPU, memory, network usage
- **Logs**: Real-time server logs and errors
- **Deployments**: Build history and rollback
- **Scaling**: Auto-scaling rules (Pro tier)

### Key Metrics to Watch

- **Response time**: Should be <500ms for most operations
- **Memory usage**: Should stay under 80% of allocated
- **Error rate**: Watch for LLM API failures or database errors
- **Database size**: Monitor growth rate

## Next Steps

1. ✅ Set Railway environment variables
2. ✅ Update Claude Desktop `mcp.json` with SSE configuration
3. ✅ Restart Claude Desktop
4. ✅ Test connection with health check
5. ✅ Add first event and query memory
6. ✅ Monitor Railway logs for issues

## Additional Resources

- **Railway Documentation**: [railway.app/docs](https://railway.app/docs)
- **MCP SSE Transport**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Project Repository**: [github.com/sorrowscry86/Causal-Memory-Core](https://github.com/sorrowscry86/Causal-Memory-Core)

---

**VoidCat RDC** | Causal Memory Core Railway MCP Server  
**Developer**: @sorrowscry86  
**Contact**: SorrowsCry86@voidcat.org
