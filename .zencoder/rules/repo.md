---
description: Repository Information Overview
alwaysApply: true
---

# Causal Memory Core Information

## Summary
A next-generation memory system for AI agents that fuses semantic recall with causal reasoning. Built upon DuckDB for high-performance analytical queries and vector operations. The system enables AI agents to perform semantic recall and causal reasoning, transforming a flat list of facts into a rich tapestry of interconnected experiences.

## Structure
- **src/**: Core implementation files including the main memory core and MCP server
- **tests/**: Unit tests for the memory core functionality
- **data/**: Directory for storing data files (created during setup)
- **logs/**: Directory for log files (created during setup)
- **.github/**: GitHub-related configuration files
- **.specstory/**: Specification and story files

## Language & Runtime
**Language**: Python
**Version**: Python 3.8+ (3.13 compatible)
**Build System**: Standard Python setuptools
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- duckdb>=0.9.0: Database engine for storage and vector operations
- sentence-transformers>=2.2.0: For generating embeddings
- openai>=1.0.0: For LLM-based causal reasoning
- numpy>=1.24.0: For numerical operations
- python-dotenv>=1.0.0: For environment variable management
- mcp>=0.9.0: For Model Context Protocol server implementation

## Build & Installation
```bash
# Clone repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Set up environment
# Copy .env.template to .env and add OpenAI API key
```

## Testing
**Framework**: pytest (primary testing framework)
**Unit Tests**: tests/test_memory_core.py 
**E2E Tests**: tests/e2e/
**Naming Convention**: test_*.py files with test_* methods
**Run Commands**:
```bash
# Run unit tests
python -m pytest tests/test_memory_core.py -v

# Run E2E tests
python -m pytest tests/e2e/ -v

# Run all tests
python -m pytest tests/ -v
```

**E2E Test Coverage**:
- CLI interface testing (interactive and command-line modes)
- Direct API usage testing (memory core operations)
- MCP Server interface testing (tool calls and responses)

## Usage
**Direct API**:
```python
from src.causal_memory_core import CausalMemoryCore

# Initialize the memory core
memory = CausalMemoryCore()

# Add events
memory.add_event("The user clicked on the file browser")

# Query for context
context = memory.get_context("How did the document get opened?")
```

**CLI**:
```bash
# Interactive mode
python cli.py --interactive

# Add event
python cli.py --add "The user opened a file"

# Query memory
python cli.py --query "How did the file get opened?"
```

**MCP Server**:
```bash
# Start MCP server
python src/mcp_server.py
```

## Configuration
**Environment Variables**:
- OPENAI_API_KEY: Required for LLM-based causal reasoning
- DB_PATH: Path to the DuckDB database file (default: causal_memory.db)
- EMBEDDING_MODEL: Model for generating embeddings (default: all-MiniLM-L6-v2)
- LLM_MODEL: OpenAI model for causal reasoning (default: gpt-3.5-turbo)
- LLM_TEMPERATURE: Temperature for LLM (default: 0.1)
- SIMILARITY_THRESHOLD: Minimum similarity for potential causal relationships (default: 0.7)
- MAX_POTENTIAL_CAUSES: Maximum number of potential causes to evaluate (default: 5)
- TIME_DECAY_HOURS: How far back to look for potential causes (default: 24 hours)

**MCP Configuration**:
- MCP_SERVER_NAME: Name of the MCP server (default: causal-memory-core)
- MCP_SERVER_VERSION: Version of the MCP server (default: 1.0.0)