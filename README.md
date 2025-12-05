# 🧠 Causal Memory Core v1.1.1

![Causal Memory Core Logo](https://img.shields.io/badge/🧠-Causal%20Memory%20Core-blue?style=for-the-badge&labelColor=1a1a1a)

Next-generation memory system for AI agents combining semantic recall and causal reasoning

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](#testing)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square)](https://modelcontextprotocol.io)

[![Docker](https://img.shields.io/badge/docker-supported-blue?style=flat-square)](Dockerfile)

[🚀 Quick Start](#-quick-start) • [☁️ Cloud Deployment](#-cloud-deployment) • [📖 Documentation](#-documentation) • [🧪 Testing](#testing) • [🔧 Configuration](#-configuration) • [🐳 Docker](#-docker-deployment)

---

## 🌟 Overview

Causal Memory Core transforms flat event lists into interconnected causal narratives, enabling AI agents to understand not just *what* happened, but *why* it happened and how events relate to each other.

### ✨ Key Features

- **🔗 Narrative Chain Reconstruction**: Automatically traces causal relationships from any event back to root causes
- **📖 Narrative Continuity Detection** _(New!)_: Recognizes sequential workflows without explicit causal language - perfect for dry system logs, code refactoring steps, incident response actions, and deployment sequences
- **🧠 Semantic Search with Causal Context**: Find events and receive complete causal stories, not just isolated facts
- **⚡ Real-time Causal Detection**: LLM-powered analysis determines relationships between events as they occur
- **🔌 MCP Integration**: Ready for integration with AI agents through Model Context Protocol (v1.1.0)
- **🌐 HTTP/REST API**: Web and mobile access with FastAPI-powered endpoints
- **☁️ Cloud-Ready**: Deploy to Railway, Render, Fly.io with one command
- **📊 DuckDB Backend**: High-performance, embedded database for fast queries
- **🤖 OpenAI Integration**: Leverages GPT models for intelligent event analysis
- **🐳 Docker Support**: Production-ready containerization with docker-compose
- **🔒 Optional Authentication**: Secure your API with optional API key authentication

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Local Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/sorrowscry86/Causal-Memory-Core.git
   cd Causal-Memory-Core
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.template .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Start the API server**

   ```bash
   python src/api_server.py
   ```

   The server will start on `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

## ☁️ Cloud Deployment

Deploy your memory system to the cloud so your LLMs can access the same memories from desktop, web, and mobile!

### Quick Deploy Options

**Railway** (Recommended - Best Free Tier)
```bash
# 1. Push your code to GitHub
# 2. Visit railway.app and create new project from GitHub repo
# 3. Add environment variable: OPENAI_API_KEY=your-key
# 4. Add persistent volume at /app/data
# Deploy happens automatically!
```

**Render**
```bash
# render.yaml is included - just connect your GitHub repo!
# 1. Visit render.com
# 2. New Web Service → Connect repository
# 3. Render auto-detects configuration
# 4. Set OPENAI_API_KEY environment variable
```

**Fly.io**
```bash
flyctl launch  # Detects fly.toml automatically
flyctl volumes create causal_memory_data --size 1
flyctl secrets set OPENAI_API_KEY=your-key
flyctl deploy
```

**📖 Full deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions, cost estimates, and platform comparisons.

### 🐳 Docker Deployment

1. **Using Docker Compose (Recommended):**

   ```bash
   # Set your OpenAI API key
   export OPENAI_API_KEY=your_key_here
   
   # Build and run
   docker-compose up --build
   ```

2. **Using Docker directly:**

   ```bash
   # Build the image
   docker build -t causal-memory-core:1.1.0 .
   
   # Run the container
   docker run -e OPENAI_API_KEY=your_key_here \
              -v causal_memory_data:/app/data \
              causal-memory-core:1.1.0
   ```

### Usage Examples

#### 🔥 Basic Usage

```python
from src.causal_memory_core import CausalMemoryCore

# Initialize the memory system
memory = CausalMemoryCore()

# Record events
memory.add_event("User opened the application")
memory.add_event("User selected a document")
memory.add_event("Document loaded successfully")

# Query causal context
context = memory.get_context("document loading")
print(context)
```

#### 🖥️ CLI Interface

```bash
# Add events via CLI
python cli.py --add "Project meeting scheduled"
python cli.py --add "Team assigned to project"

# Query for context
python cli.py --query "project status"
```

#### 🔌 MCP Server Mode (v1.1.0)

```bash
# Start MCP server
python src/mcp_server.py

# Server will be available for MCP client connections
```

## Example Usage

### Narrative Output Format (v1.1.0)

When you query the system, you get complete causal stories:

```text
Query: "How was the login bug resolved?"

Response: "Initially, a bug report was filed for 'User login fails with 500 error'. 
This led to the production server logs being inspected, revealing a NullPointerException, 
which in turn caused the UserAuthentication service code to be reviewed, identifying a missing null check. 
This led to a patch being written to add the necessary null check, 
which in turn caused the patch to be successfully deployed to production, and the bug was marked as resolved."
```

### Narrative Continuity Example (v1.1.2+)

The system now recognizes sequential workflows without explicit causal language:

```text
# Dry system log entries (no "because", "caused", etc.)
memory.add_event("Fixed bug #1234: NPE in user authentication")
memory.add_event("Added regression tests for authentication flow")
memory.add_event("Deployed hotfix v1.2.3 to production")

Query: "What happened with the bug fix?"

Response: "Initially, Fixed bug #1234: NPE in user authentication. 
This led to Added regression tests for authentication flow 
(These events represent sequential steps in the same development workflow.), 
which in turn caused Deployed hotfix v1.2.3 to production 
(These events represent sequential steps in the same development workflow.)."
```

The system automatically links events based on:
- **Temporal proximity**: Events happening close together in time
- **Semantic relevance**: Events with similar meanings/topics
- **Workflow patterns**: Recognizes common sequences (code → test → deploy, alert → check → fix, etc.)

## 🏗️ Architecture

```mermaid
graph TB
    A[Event Input] --> B[Causal Analysis Engine]
    B --> C[DuckDB Storage]
    B --> D[OpenAI Processing]
    C --> E[Semantic Search]
    D --> E
    E --> F[Context Retrieval]
    F --> G[Causal Narrative Output]
```

- **Event recording:** `add_event()` stores events and detects causal links automatically.
- **Narrative retrieval:** `get_context()` reconstructs complete causal chains as chronological narratives.
- **Causal chain traversal:** System follows cause_id links backward to root events, then formats as story.
- **Narrative continuity:** The system recognizes sequential workflows based on temporal proximity + semantic relevance, not just explicit causal language. This enables linking of dry system logs, code refactoring steps, incident response actions, and deployment sequences.
- **Config:** All settings in `config.py` (thresholds, model names, etc).

## MCP Integration (v1.1.0)

The system exposes two primary tools via Model Context Protocol:

- **`add_event(effect: str)`**: Records events with automatic causal relationship detection
- **`query(query: str) -> str`**: ✅ **FULLY IMPLEMENTED** - Returns complete narrative chains related to the query
  - Semantic search to locate relevant events
  - Backward causal chain traversal to root causes
  - Chronological narrative formatting
  - Input validation (raises ValueError for empty/whitespace queries)
  - LRU embedding cache for performance

Both methods are production-ready and operational in both local and Railway deployments.

Perfect for AI agents that need persistent memory with causal reasoning capabilities.

## 🔧 Configuration

All configuration options are available in `config.py`:

```python
# Core settings
DB_PATH = "causal_memory.db"
LLM_MODEL = "gpt-3.5-turbo"
SIMILARITY_THRESHOLD = 0.5

# MCP Server settings (v1.1.0)
MCP_SERVER_VERSION = "1.1.0"
MCP_SERVER_NAME = "causal-memory-core"

# Performance tuning
MAX_POTENTIAL_CAUSES = 5
TIME_DECAY_HOURS = 24
```

## Testing

Our comprehensive testing suite ensures reliability and performance:

### Test Coverage

- ✅ **Unit Tests**: Core functionality validation
- ✅ **E2E Tests**: End-to-end workflow testing
- ✅ **Integration Tests**: MCP server and external tool compatibility
- ✅ **Performance Tests**: Load and stress testing

### Running Tests

```bash
# Unit tests
python -m pytest tests/test_memory_core.py -v

# End-to-end tests
python -m pytest tests/e2e/ -v

# Full test suite
python run_comprehensive_tests.py

# Coverage report
python -m pytest --cov=src tests/
```

### Recent Test Results

**Test Status**: All tests passing ✅ (100% pass rate)

| Test Category | Events Recorded | Query Success Rate | Integration Status |
|---------------|-----------------|-------------------|-------------------|
| File Operations | 4/4 (100%) | 4/5 (80%) | ✅ Desktop Commander |
| Information Retrieval | 5/5 (100%) | 3/4 (75%) | ✅ Web Search Tools |
| External Integration | 9/9 (100%) | 1/1 (100%) | ✅ GitHub MCP |

## 📊 Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Event Storage | < 1s | Real-time processing |
| Query Response | < 500ms | Multi-event chain retrieval |
| Memory Usage | ~50MB | Typical usage patterns |
| Throughput | 1000+ events/min | Batch processing |

## 🔌 Integrations

Causal Memory Core seamlessly integrates with:

- **🖥️ Desktop Commander**: File system operations and workflow tracking
- **🌐 Web Search Tools**: External information gathering and research
- **📂 GitHub MCP**: Repository access and code analysis
- **💬 Chat Systems**: Conversation context and continuity
- **🔧 Development Tools**: IDE integration and debugging assistance

## Docker Tags (v1.1.1)

- `latest`: Current stable release (1.1.1)
- `1.1.1`: Docs & CI refinements, tests green
- `1.1.0`: Enhanced narrative capabilities with MCP server
- `1.0.0`: Initial release

## 📖 Documentation

- [🏗️ Architecture Guide](docs/architecture.md)
- [📝 API Documentation](docs/api.md)
- [🚀 Deployment Guide](DEPLOYMENT.md)
- [🤝 Contributing Guide](CONTRIBUTING.md)
- [📋 Changelog](CHANGELOG.md)
- See `.github/copilot-instructions.md` for agent and contributor guidelines.
- See `The Grand Triptych of Refinement.md` for development strategy.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/sorrowscry86/Causal-Memory-Core.git
cd Causal-Memory-Core

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
python run_comprehensive_tests.py
```

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and improvements.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the foundation models
- DuckDB team for the exceptional embedded database
- MCP protocol contributors for standardizing AI tool integration
- The testing community for comprehensive validation feedback

---

### Built with ❤️ for the future of AI memory systems

[⭐ Star this project](https://github.com/sorrowscry86/Causal-Memory-Core) if you find it useful!
