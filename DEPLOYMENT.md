# Causal Memory Core - Deployment Guide

This guide covers deploying Causal Memory Core to various platforms, enabling your LLMs to access the same memories across desktop, web, and mobile.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Cloud Deployment Options](#cloud-deployment-options)
  - [Railway (Recommended)](#railway-recommended)
  - [Render](#render)
  - [Fly.io](#flyio)
- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [API Usage](#api-usage)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

## Overview

Causal Memory Core can be deployed as:

1. **HTTP/REST API Server** (Default) - For web and mobile access
2. **MCP Server** - For local AI agent integration

The HTTP API mode is recommended for cloud deployment, allowing universal access from any platform.

## Prerequisites

- **OpenAI API Key** - Required for causal relationship detection
- **Python 3.8+** (for local development)
- **Docker** (optional, for containerized deployment)

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run the API Server

```bash
python src/api_server.py
```

The server will start on `http://localhost:8000`

Visit `http://localhost:8000/docs` for interactive API documentation.

## Cloud Deployment Options

### Railway (Recommended)

Railway offers a generous free tier and automatic deployments from GitHub.

**Steps:**

1. **Create Railway Account**: Visit [railway.app](https://railway.app)

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Causal-Memory-Core repository

3. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

4. **Deploy**: Railway will automatically detect `railway.json` and deploy

5. **Add Persistent Storage** (Important for database):
   - Go to your service settings
   - Add a volume mounted at `/app/data`
   - Recommended: 1GB storage

**Estimated Cost**: Free tier includes 500 hours/month + $5 credit

**Configuration**: Already included in `railway.json`

### Render

Render provides free static site hosting and paid web services with persistent disks.

**Steps:**

1. **Create Render Account**: Visit [render.com](https://render.com)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect `render.yaml`

3. **Configure Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Other variables are pre-configured in `render.yaml`

4. **Deploy**: Render will build and deploy automatically

**Estimated Cost**:
- Free tier: Available for static sites
- Paid tier: $7/month for web services with persistent disk

**Configuration**: Already included in `render.yaml`

**Note**: The free tier on Render doesn't include persistent disks. For production use with persistent memory, use the $7/month plan.

### Fly.io

Fly.io offers generous free tier with persistent volumes included.

**Steps:**

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly**:
   ```bash
   flyctl auth login
   ```

3. **Launch Application**:
   ```bash
   flyctl launch
   ```

   This will:
   - Detect `fly.toml` configuration
   - Create a new app
   - Set up the app configuration

4. **Create Persistent Volume**:
   ```bash
   flyctl volumes create causal_memory_data --size 1
   ```

5. **Set Secrets**:
   ```bash
   flyctl secrets set OPENAI_API_KEY=sk-your-api-key-here
   ```

6. **Deploy**:
   ```bash
   flyctl deploy
   ```

7. **Check Status**:
   ```bash
   flyctl status
   flyctl logs
   ```

**Estimated Cost**:
- Free tier: 3GB persistent storage + 160GB transfer
- Paid usage: $0.15/GB-month for additional storage

**Configuration**: Already included in `fly.toml`

## Docker Deployment

### Using Docker Compose (Recommended for Self-Hosting)

1. **Create `.env` file**:
   ```bash
   cp .env.template .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Check logs**:
   ```bash
   docker-compose logs -f
   ```

4. **Stop the service**:
   ```bash
   docker-compose down
   ```

The database will persist in a Docker volume named `causal_memory_data`.

### Using Docker Directly

```bash
# Build the image
docker build -t causal-memory-core:latest .

# Run HTTP API server (default)
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key-here \
  -v causal_memory_data:/app/data \
  causal-memory-core:latest

# Run MCP server instead
docker run -d \
  -e OPENAI_API_KEY=sk-your-key-here \
  -v causal_memory_data:/app/data \
  causal-memory-core:latest \
  python src/mcp_server.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT models |
| `DB_PATH` | No | `causal_memory.db` | Database file path |
| `LLM_MODEL` | No | `gpt-3.5-turbo` | OpenAI model to use |
| `SIMILARITY_THRESHOLD` | No | `0.7` | Minimum similarity for causal links (0-1) |
| `MAX_POTENTIAL_CAUSES` | No | `5` | Max events to check for causality |
| `TIME_DECAY_HOURS` | No | `24` | How far back to look for causes |
| `PORT` | No | `8000` | HTTP server port |
| `HOST` | No | `0.0.0.0` | HTTP server host |
| `API_KEY` | No | - | Optional API key for authentication |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated) |

## API Usage

### Base URL

After deployment, your base URL will be:
- **Railway**: `https://your-app.up.railway.app`
- **Render**: `https://your-app.onrender.com`
- **Fly.io**: `https://your-app.fly.dev`
- **Local**: `http://localhost:8000`

### Endpoints

#### Add Event

```bash
curl -X POST https://your-app.railway.app/events \
  -H "Content-Type: application/json" \
  -d '{"effect_text": "User clicked the save button"}'
```

#### Query Memory

```bash
curl -X POST https://your-app.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What happened after the user clicked save?"}'
```

#### Health Check

```bash
curl https://your-app.railway.app/health
```

#### Get Statistics

```bash
curl https://your-app.railway.app/stats
```

### Interactive Documentation

Visit `https://your-app.railway.app/docs` for interactive API documentation powered by Swagger UI.

### Using with LLMs

#### From Desktop (Python)

```python
import requests

BASE_URL = "https://your-app.railway.app"

# Add an event
requests.post(f"{BASE_URL}/events", json={
    "effect_text": "User reported login issue"
})

# Query memory
response = requests.post(f"{BASE_URL}/query", json={
    "query": "What issues have users reported?"
})
print(response.json()["narrative"])
```

#### From Web/Mobile (JavaScript)

```javascript
const BASE_URL = "https://your-app.railway.app";

// Add event
await fetch(`${BASE_URL}/events`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    effect_text: 'User completed checkout'
  })
});

// Query memory
const response = await fetch(`${BASE_URL}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What happened during checkout?'
  })
});
const data = await response.json();
console.log(data.narrative);
```

## Health Checks

All cloud platforms support health checks via the `/health` endpoint.

**Response Example**:
```json
{
  "status": "healthy",
  "version": "1.1.1",
  "database_connected": true
}
```

Configure your platform's health check to:
- **Path**: `/health`
- **Expected Status**: 200
- **Interval**: 30 seconds
- **Timeout**: 5 seconds

## Security

### API Key Authentication (Optional)

To require API key authentication:

1. Set the `API_KEY` environment variable:
   ```bash
   API_KEY=your-secret-key-here
   ```

2. Include the key in requests:
   ```bash
   curl -X POST https://your-app.railway.app/events \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-secret-key-here" \
     -d '{"effect_text": "Event text"}'
   ```

### CORS Configuration

By default, CORS allows all origins (`*`). To restrict to specific domains:

```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Troubleshooting

### Database Not Persisting

**Problem**: Data is lost after redeployment.

**Solution**: Ensure persistent volume is properly configured:
- **Railway**: Add a volume in service settings
- **Render**: Enable persistent disk in service settings
- **Fly.io**: Create volume with `flyctl volumes create`
- **Docker**: Use named volumes (`-v causal_memory_data:/app/data`)

### Out of Memory Errors

**Problem**: Service crashes with memory errors.

**Solution**:
1. Increase memory allocation in platform settings
2. Reduce `MAX_POTENTIAL_CAUSES` to lower memory usage
3. Use `gpt-3.5-turbo` instead of larger models

### Slow Response Times

**Problem**: API responses are slow.

**Solutions**:
1. Check `SIMILARITY_THRESHOLD` - higher values = fewer LLM calls
2. Reduce `MAX_POTENTIAL_CAUSES` for faster processing
3. Ensure database is on persistent disk, not network storage
4. Use dedicated compute (paid tiers) instead of shared

### OpenAI Rate Limits

**Problem**: 429 errors from OpenAI API.

**Solutions**:
1. Increase `SIMILARITY_THRESHOLD` to reduce LLM API calls
2. Upgrade OpenAI API plan for higher rate limits
3. Implement request queuing in your application

## Cost Optimization

### Tips for Free/Low-Cost Deployment

1. **Start with Railway**: Best free tier for getting started
2. **Use gpt-3.5-turbo**: Much cheaper than GPT-4
3. **Increase SIMILARITY_THRESHOLD**: Reduces LLM API calls
4. **Fly.io for Production**: Good free tier with persistent storage
5. **Share one instance**: Multiple LLMs can use the same deployment

### Estimated Monthly Costs

**Scenario**: 1,000 events/month, 500 queries/month

- **Cloud Platform**: $0 (free tier on Railway/Fly.io)
- **OpenAI API**: ~$5-10 depending on usage
- **Total**: ~$5-10/month

**Scenario**: 10,000 events/month, 5,000 queries/month

- **Cloud Platform**: ~$7 (Render paid tier with disk)
- **OpenAI API**: ~$50-100 depending on usage
- **Total**: ~$57-107/month

## Next Steps

1. **Deploy to your preferred platform**
2. **Test with the example requests**
3. **Integrate with your LLM application**
4. **Monitor usage and costs**
5. **Scale as needed**

## Support

For issues or questions:
- Check the [main README](README.md)
- Review [architecture documentation](docs/architecture.md)
- Check [API documentation](docs/api.md)
- Open an issue on GitHub

---

**Pro Tip**: Start with Railway for development, then migrate to Fly.io for production if you need better free tier limits with persistent storage.
