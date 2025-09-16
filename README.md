# Causal Memory Core v1.1.0

Causal Memory Core is a next-generation memory system for AI agents, combining semantic recall and causal reasoning. Built on DuckDB and OpenAI, it transforms flat event lists into interconnected causal narratives.

## Key Features

- **Narrative Chain Reconstruction**: Automatically traces causal relationships from any event back to root causes
- **Semantic Search with Causal Context**: Find events and receive complete causal stories, not just isolated facts
- **Real-time Causal Detection**: LLM-powered analysis determines relationships between events as they occur
- **MCP Integration**: Ready for integration with AI agents through Model Context Protocol

## Quick Start

### Local Installation

1. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```
2. **Configure environment:**
	- Copy `.env.template` to `.env` and set your `OPENAI_API_KEY`.
3. **Run the core:**
	- Direct API: `python example_usage.py`
	- CLI: `python cli.py --add "Event description"`
	- MCP Server: `python src/mcp_server.py`

### Docker Deployment

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

## Example Usage

### Narrative Output Format

When you query the system, you get complete causal stories:

```
Query: "How was the login bug resolved?"

Response: "Initially, a bug report was filed for 'User login fails with 500 error'. 
This led to the production server logs being inspected, revealing a NullPointerException, 
which in turn caused the UserAuthentication service code to be reviewed, identifying a missing null check. 
This led to a patch being written to add the necessary null check, 
which in turn caused the patch to be successfully deployed to production, and the bug was marked as resolved."
```

## Key Concepts

- **Event recording:** `add_event()` stores events and detects causal links automatically.
- **Narrative retrieval:** `get_context()` reconstructs complete causal chains as chronological narratives.
- **Causal chain traversal:** System follows cause_id links backward to root events, then formats as story.
- **Config:** All settings in `config.py` (thresholds, model names, etc).

## MCP Integration

The system exposes two primary tools via Model Context Protocol:

- **`add_event(effect: str)`**: Records events with automatic causal relationship detection
- **`query(query: str) -> str`**: Returns complete narrative chains related to the query

Perfect for AI agents that need persistent memory with causal reasoning capabilities.

## Testing

- Unit tests: `python -m pytest tests/test_memory_core.py -v`
- E2E tests: `python -m pytest tests/e2e/ -v`
- Full suite: `python run_comprehensive_tests.py`

## Docker Tags

- `latest`: Current stable release (1.1.0)
- `1.1.0`: Enhanced narrative capabilities with MCP server
- `1.0.0`: Initial release

## Documentation

- See `.github/copilot-instructions.md` for agent and contributor guidelines.
- See `CHANGELOG.md` for recent changes.
- See `The Grand Triptych of Refinement.md` for development strategy.

## License

MIT License. See LICENSE file.
