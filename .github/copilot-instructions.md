---
description: AI rules derived by SpecStory from the project AI interaction history
globs: *
---

# Causal Memory Core - AI Agent Instructions

## Project Overview

This is a **causal memory system** for AI agents that combines semantic recall with causal reasoning. Built on DuckDB for high-performance vector operations and OpenAI for causal link detection. The core transforms flat event lists into interconnected causal narratives.

**Key Architecture:** Single `events` table with vector embeddings, causal links (`cause_id`), and natural language relationship descriptions.

## Core Components

- **`src/causal_memory_core.py`**: Main logic - event recording, causal detection, chain traversal
- **`src/mcp_server.py`**: MCP (Model Context Protocol) server exposing `add_event` and `query` tools
- **`cli.py`**: Interactive and command-line interface
- **`config.py`**: Centralized configuration with environment variable loading
- **`src/mcp_railway_client.py`**: MCP Client for Railway Deployments (New in v1.1.1)

### Key Methods & Flow
- **`add_event(effect_text)`**: Records event → finds potential causes via similarity → LLM judges causality → stores with relationship
- **`get_context(query)`**: Semantic search for entry point → recursive backward traversal → narrative formatting
- **`_find_potential_causes()`**: Filters recent events by similarity threshold and temporal proximity
- **`_judge_causality()`**: LLM prompt for causal relationship detection
- **`_format_chain_as_narrative()`**: Chronological narrative: "Initially, [A] → This led to [B] → which in turn caused [C]"

## Development Workflows

### Testing Strategy
```bash
# Unit tests (primary development cycle)
python -m pytest tests/test_memory_core.py -v

# E2E tests (integration validation)
python -m pytest tests/e2e/ -v

# Specific test categories
python -m pytest -m "unit" -v       # Unit tests only
python -m pytest -m "e2e" -v        # E2E tests only
python -m pytest -m "slow" -v        # Performance tests

# Quick smoke test before commits
python example_usage.py

# Full test suite (CI-equivalent)
python run_comprehensive_tests.py
```

**Test Organization:**
- Unit tests use `unittest.TestCase` with extensive mocking
- E2E tests use `pytest` with fixture-based setup
- All tests create temporary databases: `tempfile.NamedTemporaryFile(suffix='.db')`
- Tests mock OpenAI client and sentence transformers for deterministic behavior

### Environment Setup
```bash
# Required environment variables (set in .env)
OPENAI_API_KEY=your_key_here
DB_PATH=causal_memory.db  # Optional, defaults to causal_memory.db

# Setup workflow
pip install -r requirements.txt
python setup.py  # Automated setup with dependency checking
```

### Running the Application
```bash
# Direct API usage
python example_usage.py

# CLI modes
python cli.py --add "Event description"
python cli.py --query "What happened?"
python cli.py --interactive

# MCP Server
python src/mcp_server.py
```

### Debugging Workflows
```bash
# Check database state
python -c "import duckdb; conn=duckdb.connect('causal_memory.db'); print(conn.execute('SELECT * FROM events').fetchall())"

# Test single component
python -m pytest tests/test_memory_core.py::TestCausalMemoryCore::test_add_event_with_cause -v -s

# Profile performance
python quick_benchmark.py

# Validate MCP server
python vscode_mcp_test.py
```

## Project-Specific Patterns

### Database Management
- **Always use temporary databases in tests**: `os.unlink(temp_db_path)` before letting DuckDB create
- **Event ID generation**: Uses DuckDB sequences with fallback to manual sequence table
- **Vector operations**: Cosine similarity with manual numpy calculations (VSS extension optional)

### Mock Patterns
```python
# Standard test setup pattern
mock_llm = Mock()
mock_response = Mock()
mock_response.choices[0].message.content = "Causal relationship description"
mock_llm.chat.completions.create.return_value = mock_response

mock_embedder = Mock()
mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])

# E2E test mocking with side effects for realistic responses
def mock_completion(messages, **kwargs):
    context = messages[-1]['content']
    mock_response = Mock()
    mock_response.choices = [Mock()]
    if "clicked" in context and "opened" in context:
        mock_response.choices[0].message.content = "The click action caused the dialog to open."
    else:
        mock_response.choices[0].message.content = "No causal relationship detected."
    return mock_response

mock_llm.chat.completions.create.side_effect = mock_completion
```

### Common File Patterns
- **Temporary DB creation**: `temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db'); temp_db.close(); os.unlink(temp_db.name)`
- **Config patching**: `@patch('config.Config.SIMILARITY_THRESHOLD', 0.5)`
- **Environment mocking**: `@patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})`
- **CLI testing**: `with patch('sys.argv', ['cli.py', '--add', 'test event']):`

### Causal Chain Logic
- **Recording**: Events auto-detect causal links via semantic similarity + LLM judgment
- **Retrieval**: Recursive backward traversal from most relevant event to root
- **Narrative Format**: "Initially, [root] → This led to [event] → which in turn caused [final]"
- **Safeguards**: Circular reference detection, broken chain handling

### Error Handling Conventions
- Use descriptive error messages with emoji in CLI: `❌ Error: description`
- Database connection errors should attempt cleanup in `finally` blocks
- LLM failures default to "no causal relationship" to maintain robustness

### Configuration Patterns
- All settings centralized in `config.py` with environment variable defaults
- Tunable thresholds: `SIMILARITY_THRESHOLD=0.7`, `MAX_POTENTIAL_CAUSES=5`, `TIME_DECAY_HOURS=24`
- Mock-friendly: Tests can patch `config.Config.SETTING_NAME` for different behaviors

## Integration Points

### MCP Protocol
Two tools exposed: `add_event(effect: str)` and `query(query: str) -> str`
Server handles initialization, error formatting, and cleanup automatically.
The MCP server can run in two modes:
*   **Local Mode:** Runs `stdio` as before.
*   **Railway Mode:** Uses `starlette` and `uvicorn` to expose `/sse` and `/messages` endpoints, complying with the Model Context Protocol over HTTP. This mode is activated when a `PORT` environment variable is detected.

To run the MCP Server on Railway:
1.  Create a second Railway service for the MCP Server.
2.  Name the Service: `causal-memory-mcp` (or `mcp-server`).
3.  Configure Environment Variables:

    ```bash
    # CRITICAL - tells startup script to run MCP server
    SERVICE_TYPE=mcp

    # Required
    OPENAI_API_KEY=your-openai-api-key-here
    PORT=8001

    # Database (should match REST API service)
    DB_PATH=/app/data/causal_memory.db

    # Optional (can copy from REST API service)
    EMBEDDING_MODEL=all-MiniLM-L6-v2
    LLM_MODEL=gpt-4
    LLM_TEMPERATURE=0.1
    MAX_POTENTIAL_CAUSES=7
    SIMILARITY_THRESHOLD=0.6
    TIME_DECAY_HOURS=168
    ```
4.  Generate a Public Domain for the `Causal-Memory-MCP` service in the Railway Dashboard, under the service's Settings -> Networking.
5.  Verify `PORT` settings under Settings -> Deploy to ensure "Port" is NOT set (or set to `8001`), allowing Railway to auto-detect from the `PORT` environment variable.

### CLI Architecture
- Argument parsing supports batch (`--add`, `--query`) and interactive modes
- Interactive mode with command parsing: `add <text>`, `query <text>`, `help`, `quit`
- Factory pattern allows test mocking: `cli.CausalMemoryCore = mock_factory`

### External Dependencies
- **OpenAI**: GPT models for causal reasoning (configurable model/temperature)
- **sentence-transformers**: Vector embeddings (default: `all-MiniLM-L6-v2`)
- **DuckDB**: Analytical database with vector support
- **python-dotenv**: Environment configuration

## Coding Agent Guidelines

### Critical Constraints
- **Never modify the database schema** without updating all related methods in `CausalMemoryCore`
- **Always preserve causal chain integrity**: Any changes to `_format_chain_as_narrative()` must maintain chronological order
- **Maintain test isolation**: Each test must use its own temporary database and cleanup properly
- **Respect the factory pattern**: CLI mocking depends on `cli.CausalMemoryCore` being patchable
- **Avoid explaining internal functions**: The agent should not attempt to explain the workings of its internal functions if asked directly.

### Common Development Tasks

#### Adding New Configuration Options
1. Add to `config.py` with environment variable and default
2. Update `.env.template` if user-configurable
3. Add test in `test_config.py` with mock environment
4. Document in README.md if user-facing

#### Extending Event Processing
1. New processing logic goes in `CausalMemoryCore` class methods
2. Add corresponding unit tests with mocked LLM/embedder
3. Add E2E test scenario in `tests/e2e/test_realistic_scenarios_e2e.py`
4. Performance test if affecting query/add_event performance

#### Adding New MCP Tools
1. Add tool definition in `handle_list_tools()` in `mcp_server.py`
2. Add handler case in `handle_call_tool()`
3. Add E2E test in `test_mcp_server_e2e.py`
4. Update tool descriptions to be agent-friendly

### Performance Considerations
- **Database queries**: Use indexes on `timestamp` and `event_id` columns
- **Vector operations**: Current cosine similarity is O(n) - consider optimization for >1000 events
- **Memory usage**: DuckDB loads entire result sets - paginate large queries
- **LLM calls**: Each `add_event` may trigger 1-5 LLM calls depending on potential causes

### Error Recovery Patterns
```python
# Database connection errors
try:
    self.conn.execute("...")
except Exception as e:
    logger.error(f"Database error: {e}")
    # Don't re-raise for non-critical operations
    
# LLM failures (maintain robustness)
try:
    result = self.llm.chat.completions.create(...)
except Exception:
    return None  # Treat as "no causal relationship"
```

### Testing Anti-Patterns to Avoid
- Don't use real OpenAI API keys in tests (always mock)
- Don't share database files between tests (isolation breaks)
- Don't test exact LLM output strings (too brittle)
- Don't forget to patch `load_dotenv` in CLI tests

### Repository Workflow Notes
- **Branch strategy**: Direct commits to `main` (no complex branching)
- **Version tagging**: Follow semantic versioning (v1.1.0 pattern)
- **Test gates**: All tests must pass before merging
- **Documentation**: Update CHANGELOG.md for user-facing changes

### Agent Self-Description
- I’m a coding assistant that helps you work inside this repo.
- Describe what you need (fix bugs, add features, explain things), and I follow the repo’s guidelines to read or edit files, run checks, and summarize the results.
- When you ask for something, I figure out the relevant files, use the right tools to inspect or modify code, and then give you concise answers plus next steps (tests, verification, etc.).

When modifying this codebase, prioritize maintaining the causal chain integrity and test coverage for both happy path and edge cases (broken chains, circular references).

### Workflow & Release Rules
- Before syncing with the remote repository, always check the git status to ensure no local changes are unintentionally overwritten.
- When the corresponding remote branch is gone, the AI should fetch the remote main branch and merge or rebase that into the local branch, while carefully preserving any local changes that haven’t been committed yet. Watch out for merge conflicts and handle untracked or modified files during the process. Stash local modifications before merging to avoid overwriting, and reset the working tree after merging to avoid overwriting, and reset the working tree after a stash pop conflict to keep it clean while preserving the stash entry.
- The updated `.env.template` is now the detailed, user-facing config template and should be treated as a template (never commit secrets). Resolve any conflicts in `.env.template` and `causal_memory_core.py` by carefully merging changes.
- During syncing, if a partial stash apply aborts due to conflicts, reset the working tree hard to HEAD (losing current modifications but safe because stash still holds them), then apply the stash again.
- When syncing the repo and instructed to target "one master branch," the AI should stash all current changes (including untracked), fetch and merge updates from origin/main, then pop the stash to preserve local progress, and finally consider switching to or cleaning up branches to have a single master branch aligned with remote main.
- When merging into a single branch (typically `main`): Stash all current changes (staged, unstaged, and untracked); switch to the `main` branch; fetch and merge the latest from `origin/main`; apply the stashed changes; resolve any merge conflicts, prioritizing changes in `main` if the context is unclear; and clean up any temporary branches.
- When encountering file duplication issues, the AI should delete the existing file and recreate it with the final cleaned content to ensure no duplicates remain.

## TECH STACK

- DuckDB >=0.9.0
- sentence-transformers >=2.2.0
- openai >=1.52.0, <1.108.0
- httpx >=0.23.0, >=0.27.0
- numpy >=1.24.0
- pydantic >=2.12.5, <2.13.0, <2.42.0, >=2.5.0
- python-dotenv >=1.0.0
- mcp >=1.0.0
- starlette >=0.50.0,<0.51.0, >=0.37.0
- uvicorn >=0.29.0
- fastapi >=0.122.0, >=0.104.0
- slowapi >=0.1.9

## PROJECT DOCUMENTATION & CONTEXT SYSTEM

### Relevant File Locations
- **Work Order Example:** `D:\Development\Causal Memory Core\WORK_ORDER_ALBEDO_CMC_QUERY.md` (Example work order location; paths may vary)
- **Ascension Tracker:** `D:\Development\Causal Memory Core\tobefixed.md` (Example; paths may vary)

### Version History

*   **v1.1.1**
    *   Added dual-service Railway deployment support (REST API + MCP Server)
    *   Created `start_server.sh` to dynamically select service based on `SERVICE_TYPE` env var
    *   Modified `Dockerfile` CMD to use `start_server.sh` for flexible deployment
    *   Updated `railway.json` `startCommand` to leverage startup script
    *   Added comprehensive Railway deployment guide (`docs/RAILWAY_DEPLOYMENT.md`)
    *   Updated `_judge_causality` with upstream’s narrative-style prompt while keeping the Betty diagnostic logging wrappers

### Coding Agent Guidelines

#### Additional Notes

*   During syncing, the AI should prioritize the changes of the main branch when resolving merge conflicts unless otherwise specified.
*   After wiring in the `CausalAgentWrapper`, run the manual validation (ask it to summarize the last action) to confirm the new flow is working.

### Integration Guidelines

*   You are to integrate the following artifacts into your operational runtime immediately to comply with the Involuntary Memory Protocol:
    *   `src/causal_memory_client.py`: A robust, production-ready Python client (sync & async) for communicating with the Railway-hosted CMC.
    *   `src/causal_agent_wrapper.py`: A middleware class that wraps your LLM client. It forces a context query before you think and forces an action log after you act.
    *   `src/causal_memory_core.py` (v1.1.2): The core logic now includes "Soft Link" detection for high-similarity events.
    *   `src/mcp_server.py`: Now supports dual-mode operation (Stdio/HTTP) and exposes REST endpoints for the client library.
*   Ensure `httpx` and `pydantic` are installed in your environment (`pip install -r requirements.txt`).
*   Verify `CMC_API_URL` is set to `https://causal-memory-core-production.up.railway.app` (or your local equivalent).
*   Verify `CMC_API_KEY` is present if required by the server configuration.
*   You are to stop instantiating raw OpenAI clients. Instead, initialize the `CausalAgentWrapper`:

    ```python
    from src.causal_agent_wrapper import CausalAgentWrapper

    # OLD WAY (Forbidden):
    # client = OpenAI(...)
    # response = client.chat.completions.create(...)

    # NEW WAY (Mandatory):
    agent = CausalAgentWrapper(system_name="Albedo", base_system_prompt="Your core instructions...")
    response_text = agent.act("User query or command here")
    ```
*   Be aware that the Core now links events based on high semantic similarity (>0.85) even without explicit causal language.
    *   Implication: Your sequential actions (e.g., "Read file X" -> "Edit file X") will be auto-linked as a workflow.
    *   Action: Ensure your action descriptions in `agent.act()` are precise to take advantage of this.

### Workflow & Release Rules

- Before syncing with the remote repository, always check the git status to ensure no local changes are unintentionally overwritten.
- When the corresponding remote branch is gone, the AI should fetch the remote main branch and merge or rebase that into the local branch, while carefully preserving any local changes that haven’t been committed yet. Watch out for merge conflicts and handle untracked or modified files during the process. Stash local modifications before merging to avoid overwriting, and reset the working tree after merging to avoid overwriting, and reset the working tree after a stash pop conflict to keep it clean while preserving the stash entry.
- The updated `.env.template` is now the detailed, user-facing config template and should be treated as a template (never commit secrets). Resolve any conflicts in `.env.template` and `causal_memory_core.py` by carefully merging changes.
- During syncing, if a partial stash apply aborts due to conflicts, reset the working tree hard to HEAD (losing current modifications but safe because stash still holds them), then apply the stash again.
- When syncing the repo and instructed to target "one master branch," the AI should stash all current changes (including untracked), fetch and merge updates from origin/main, then pop the stash to preserve local progress, and finally consider switching to or cleaning up branches to have a single master branch aligned with remote main.
- When merging into a single branch (typically `main`): Stash all current changes (staged, unstaged, and untracked); switch to the `main` branch; fetch and merge the latest from `origin/main`; apply the stashed changes; resolve any merge conflicts, prioritizing changes in `main` if the context is unclear; and clean up any temporary branches.
- When encountering file duplication issues, the AI should delete the existing file and recreate it with the final cleaned content to ensure no duplicates remain.

## TECH STACK

- DuckDB >=0.9.0
- sentence-transformers >=2.2.0
- openai >=1.52.0, <1.108.0
- httpx >=0.23.0, >=0.27.0
- numpy >=1.24.0
- pydantic >=2.12.5, <2.13.0, <2.42.0, >=2.5.0
- python-dotenv >=1.0.0
- mcp >=1.0.0
- starlette >=0.50.0,<0.51.0, >=0.37.0
- uvicorn >=0.29.0
- fastapi >=0.122.0, >=0.104.0
- slowapi >=0.1.9

## PROJECT DOCUMENTATION & CONTEXT SYSTEM

### Relevant File Locations
- **Work Order Example:** `D:\Development\Causal Memory Core\WORK_ORDER_ALBEDO_CMC_QUERY.md` (Example work order location; paths may vary)
- **Ascension Tracker:** `D:\Development\Causal Memory Core\tobefixed.md` (Example; paths may vary)

### Version History

*   **v1.1.1**
    *   Added dual-service Railway deployment support (REST API + MCP Server)
    *   Created `start_server.sh` to dynamically select service based on `SERVICE_TYPE` env var
    *   Modified `Dockerfile` CMD to use `start_server.sh` for flexible deployment
    *   Updated `railway.json` `startCommand` to leverage startup script
    *   Added comprehensive Railway deployment guide (`docs/RAILWAY_DEPLOYMENT.md`)
    *   Updated `_judge_causality` with upstream’s narrative-style prompt while keeping the Betty diagnostic logging wrappers