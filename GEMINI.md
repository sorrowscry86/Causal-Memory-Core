# Project: Causal Memory Core

## Project Overview

This project, the Causal Memory Core, is a sophisticated memory system designed for AI agents. It's built with Python and leverages a fusion of semantic recall and causal reasoning. The core's purpose is to enable agents to not only retrieve information based on conceptual similarity but also to understand and reconstruct the sequence of events and cause-and-effect relationships.

The architecture is centered around a DuckDB database, which makes it a portable, file-based solution without external server dependencies. Events are stored with vector embeddings (generated using `sentence-transformers`) for semantic search. An LLM (like OpenAI's GPT series) is used to intelligently determine causal links between events.

The main logic is encapsulated in the `CausalMemoryCore` class within `src/causal_memory_core.py`.

## Building and Running

### 1. Installation

The project uses a `requirements.txt` file for its dependencies. Installation can be done via pip. A `setup.py` script is also provided to automate the process.

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

The project requires environment variables for configuration, which are loaded from a `.env` file. A template is provided in `.env.template`. The most critical variable is `OPENAI_API_KEY`.

Key configuration settings in `config.py` include:
- `DB_PATH`: Path to the DuckDB database file.
- `EMBEDDING_MODEL`: The sentence-transformer model to use.
- `LLM_MODEL`: The OpenAI model to use for causal reasoning.
- `SIMILARITY_THRESHOLD`: The threshold for determining potential causal links.

### 3. Running the Application

The Causal Memory Core can be used in several ways:

**a) Direct Library Usage:**
The core can be imported and used directly in a Python script.

```python
from src.causal_memory_core import CausalMemoryCore

memory = CausalMemoryCore()
memory.add_event("An event occurred.")
context = memory.get_context("What happened?")
print(context)
memory.close()
```

**b) Command-Line Interface (CLI):**
The `cli.py` script provides an interactive shell or direct command execution.

```bash
# Run in interactive mode
python cli.py --interactive

# Add an event directly
python cli.py --add "The user clicked the save button."

# Query for context directly
python cli.py --query "Why was the file saved?"
```

**c) MCP Server:**
The `src/mcp_server.py` script exposes the core's functionality via the Model Context Protocol (MCP), allowing other AI agents or tools to interact with it.

```bash
# Start the MCP server
python src/mcp_server.py
```

## Development Conventions

### Testing

The project uses `pytest` for testing. The configuration is located in `pytest.ini`. Tests are organized in the `tests/` directory.

To run the main test suite:
```bash
python -m pytest tests/test_memory_core.py -v
```

To run all tests:
```bash
python -m pytest tests/ -v
```

Test files are clearly separated by their purpose (e.g., `test_cli.py`, `test_memory_core.py`, `e2e/test_api_e2e.py`).

### Code Structure

- `src/`: Contains the main source code.
  - `causal_memory_core.py`: The primary class and logic.
  - `mcp_server.py`: The MCP server implementation.
- `tests/`: Contains all unit and end-to-end tests.
- `config.py`: Centralized configuration management.
- `cli.py`: The command-line interface.
- `requirements.txt`: Python package dependencies.
- `setup.py`: Project setup and installation script.
