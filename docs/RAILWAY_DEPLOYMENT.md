# Railway Deployment Guide - Dual Service Configuration

## Overview

This setup allows you to run **both** the REST API and MCP Server on Railway as separate services, sharing the same database.

## Architecture

```
Railway Project
├── Service 1: REST API (port 8000)
│   └── Endpoints: /health, /events, /query, /stats
└── Service 2: MCP Server (port 8001) 
    └── Endpoints: /sse, /messages, /
```

Both services connect to the same persistent DuckDB database.

## Setup Instructions

### Step 1: Create Railway Project

If you haven't already:

1. Go to [railway.app](https://railway.app)
2. Create a new project from GitHub repo: `sorrowscry86/Causal-Memory-Core`
3. Railway will auto-detect the `Dockerfile` and deploy

### Step 2: Configure REST API Service (Default)

The initial deployment runs the REST API by default.

**Environment Variables (Railway Dashboard):**

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here
PORT=8000

# Optional (with defaults)
DB_PATH=/app/data/causal_memory.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
MAX_POTENTIAL_CAUSES=7
SIMILARITY_THRESHOLD=0.6
TIME_DECAY_HOURS=168
```

**This service will be available at:**
`https://causal-memory-core-production.up.railway.app`

### Step 3: Add MCP Server Service

1. In Railway dashboard, click **"New Service"** → **"Empty Service"**
2. Name it: `causal-memory-mcp`
3. Link it to the same GitHub repo
4. Configure the service:

**Environment Variables for MCP Service:**

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here
SERVICE_TYPE=mcp  # THIS IS KEY - tells startup script to run MCP server
PORT=8001  # Different port from REST API

# Optional (same as REST API service)
DB_PATH=/app/data/causal_memory.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
MAX_POTENTIAL_CAUSES=7
SIMILARITY_THRESHOLD=0.6
TIME_DECAY_HOURS=168
```

**This service will be available at:**
`https://causal-memory-mcp-production.up.railway.app`

### Step 4: Configure Shared Database

Both services need to access the same database. Options:

#### Option A: Shared Volume (Recommended)

1. Create a Railway volume in your project
2. Name it: `causal-memory-data`
3. Mount point: `/app/data`
4. Attach the volume to **both** services
5. Set `DB_PATH=/app/data/causal_memory.db` in both services

#### Option B: External Database

Use Railway PostgreSQL or external database:

```bash
# Both services
DB_TYPE=postgresql
DATABASE_URL=your-postgresql-connection-string
```

### Step 5: Deploy and Verify

**Deploy REST API Service:**

```bash
curl https://causal-memory-core-production.up.railway.app/health
```

**Expected response:**

```json
{
  "status": "healthy",
  "version": "1.1.1",
  "database_connected": true
}
```

**Deploy MCP Server:**

```bash
curl https://causal-memory-mcp-production.up.railway.app/
```

**Expected response:**

```
Causal Memory Core MCP Active 🧠
```

## Claude Desktop Configuration

Add **both** services to your `mcp.json`:

```json
{
  "mcpServers": {
    "causal-memory-railway-sse": {
      "type": "sse",
      "url": "https://causal-memory-mcp-production.up.railway.app/sse",
      "description": "Remote MCP server (SSE transport)"
    }
  }
}
```

You can also access the REST API directly if needed:

```bash
# Add event via REST API
curl -X POST https://causal-memory-core-production.up.railway.app/events \
  -H "Content-Type: application/json" \
  -d '{"effect_text": "Testing dual Railway deployment"}'

# Query via REST API
curl -X POST https://causal-memory-core-production.up.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{"query": "dual deployment"}'
```

## How the Startup Script Works

The `start_server.sh` script checks the `SERVICE_TYPE` environment variable:

```bash
if [ "$SERVICE_TYPE" = "mcp" ]; then
    # Run MCP Server (SSE mode)
    python src/mcp_server.py
else
    # Run REST API (default)
    python src/api_server.py
fi
```

This allows the same Docker image to run different services based on configuration.

## Service Comparison

| Feature | REST API Service | MCP Server Service |
|---------|-----------------|-------------------|
| Port | 8000 | 8001 |
| Protocol | HTTP/REST | MCP/SSE |
| Endpoints | /health, /events, /query, /stats | /sse, /messages, / |
| Clients | curl, Postman, web apps | Claude Desktop, MCP clients |
| Database | Shared volume | Shared volume |
| Use Case | Direct API access | MCP protocol integration |

## Monitoring

### Railway Dashboard

Monitor both services:

- **Metrics**: CPU, memory, network for each service
- **Logs**: Separate logs for REST API and MCP server
- **Deployments**: Independent deployment history
- **Scaling**: Scale services independently

### Health Checks

**REST API:**

```bash
curl https://causal-memory-core-production.up.railway.app/health
```

**MCP Server:**

```bash
curl https://causal-memory-mcp-production.up.railway.app/
```

## Troubleshooting

### Services Can't Connect to Database

**Issue:** Both services need shared database access

**Solutions:**

- Verify shared volume is mounted to both services at `/app/data`
- Check `DB_PATH` matches mount point in both services
- Ensure volume has write permissions
- Check Railway logs for database connection errors

### MCP Server Not Starting

**Issue:** Service starts but MCP endpoints don't work

**Solutions:**

- Verify `SERVICE_TYPE=mcp` is set in environment variables
- Check logs for "Starting MCP Server (SSE)" message
- Ensure port is correctly set (8001 recommended)
- Test health endpoint first: `curl https://[mcp-url]/`

### Services Using Different Databases

**Issue:** Events added via REST API don't appear in MCP queries

**Solutions:**

- Confirm both services have identical `DB_PATH` values
- Verify shared volume is attached to both services
- Check Railway volume dashboard for mount points
- Restart both services after volume configuration changes

### Port Conflicts

**Issue:** Services won't start due to port conflicts

**Solutions:**

- Ensure REST API uses `PORT=8000`
- Ensure MCP Server uses `PORT=8001`
- Railway automatically handles external port mapping
- Internal port conflicts are unlikely in separate services

## Scaling Considerations

### Independent Scaling

You can scale each service independently:

- **REST API**: Scale for high HTTP traffic
- **MCP Server**: Scale for multiple MCP clients

### Database Contention

Both services share one database:

- DuckDB is single-writer, multi-reader
- For high concurrency, consider PostgreSQL
- Monitor Railway metrics for database bottlenecks

## Cost Optimization

Railway pricing considerations:

- **Two services** = 2x compute costs
- **Shared volume** = single storage cost
- **Free tier**: May not support dual services
- **Pro tier**: Recommended for production

## Migration from Single Service

If you're currently running only the REST API:

1. ✅ Keep existing REST API service running
2. ✅ Add new MCP server service (follow Step 3)
3. ✅ Configure shared volume for both
4. ✅ Update Claude Desktop config with MCP SSE URL
5. ✅ Test both services independently
6. ✅ Monitor both service logs

## Next Steps

1. ✅ Deploy REST API service (if not already done)
2. ✅ Create MCP server service with `SERVICE_TYPE=mcp`
3. ✅ Configure shared volume for database
4. ✅ Verify both services can access database
5. ✅ Add MCP SSE endpoint to Claude Desktop
6. ✅ Test events/queries through both interfaces
7. ✅ Monitor Railway metrics for both services

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Project Issues**: [github.com/sorrowscry86/Causal-Memory-Core/issues](https://github.com/sorrowscry86/Causal-Memory-Core/issues)
- **Contact**: SorrowsCry86@voidcat.org

---

**VoidCat RDC** | Causal Memory Core Dual Railway Deployment  
**Developer**: @sorrowscry86
