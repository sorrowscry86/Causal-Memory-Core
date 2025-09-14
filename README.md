# Causal Memory Core
memory.add_event("A file dialog opened")
memory.add_event("The user selected a document")
memory.add_event("The document opened in the editor")
did it directly lead to the following event: 'File dialog opened'? 
If yes, briefly explain the relationship. If no, simply respond with 'No.'"

Causal Memory Core is a next-generation memory system for AI agents, combining semantic recall and causal reasoning. Built on DuckDB and OpenAI, it transforms flat event lists into interconnected causal narratives.

## Quick Start

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

## Key Concepts

- **Event recording:** `add_event()` stores events and detects causal links.
- **Context retrieval:** `get_context()` reconstructs causal chains as narratives.
- **Config:** All settings in `config.py` (thresholds, model names, etc).

## Testing

- Unit tests: `python -m pytest tests/test_memory_core.py -v`
- E2E tests: `python -m pytest tests/e2e/ -v`
- Full suite: `python run_comprehensive_tests.py`

## Documentation

- See `.github/copilot-instructions.md` for agent and contributor guidelines.
- See `CHANGELOG.md` for recent changes.

## License

MIT License. See LICENSE file.
