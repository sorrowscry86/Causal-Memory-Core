# Causal Memory Core

A next-generation memory system for AI agents that fuses semantic recall with causal reasoning. Built upon DuckDB for high-performance analytical queries and vector operations.

## Overview

The Causal Memory Core enables AI agents to:

1. **Semantic Recall**: Retrieve information based on conceptual similarity, not just keywords
2. **Causal Reasoning**: Understand and reconstruct narrative chains of cause-and-effect relationships

This transforms a flat list of facts into a rich tapestry of interconnected experiences, allowing agents to answer not just "what happened?" but also "why did it happen?" and "what was the sequence of events that led to this outcome?"

## Architecture

The system is built around a single DuckDB table that models interconnected causal memory:

### Database Schema

**Table: events**
- `event_id`: Unique sequential identifier
- `timestamp`: When the event was recorded
- `effect_text`: Natural language description of the event
- `embedding`: Vector embedding for semantic search
- `cause_id`: Reference to the direct cause event (self-referencing)
- `relationship_text`: Description of how the cause led to the effect

### Core Operations

1. **Recording Ritual (`add_event`)**: Adds new events and determines causal links
2. **Scrying Ritual (`get_context`)**: Retrieves full causal chains for queries

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
OPENAI_API_KEY=your_openai_api_key_here
DB_PATH=causal_memory.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-3.5-turbo
```

## Usage

### Direct Usage

```python
from src.causal_memory_core import CausalMemoryCore

# Initialize the memory core
memory = CausalMemoryCore()

# Add events (the system will automatically detect causal relationships)
memory.add_event("The user clicked on the file browser")
memory.add_event("A file dialog opened")
memory.add_event("The user selected a document")
memory.add_event("The document opened in the editor")

# Query for context
context = memory.get_context("How did the document get opened?")
print(context)
# Output: Initially: The user clicked on the file browser → This led to: A file dialog opened (The click action triggered the dialog) → This led to: The user selected a document (The open dialog allowed file selection) → This led to: The document opened in the editor (Selecting the file caused it to open)

# Close when done
memory.close()
```

### MCP Server Usage

The Causal Memory Core can be exposed as an MCP (Model Context Protocol) server:

```bash
# Run the MCP server
python src/mcp_server.py
```

This exposes two tools:
- `add_event`: Add new events to memory
- `query`: Retrieve causal context for queries

### Configuration

Key configuration options in `config.py`:

- `SIMILARITY_THRESHOLD`: Minimum similarity for potential causal relationships (default: 0.7)
- `MAX_POTENTIAL_CAUSES`: Maximum number of potential causes to evaluate (default: 5)
- `TIME_DECAY_HOURS`: How far back to look for potential causes (default: 24 hours)
- `LLM_TEMPERATURE`: Temperature for LLM causal reasoning (default: 0.1)

## Testing

Run the test suite:

```bash
python -m pytest tests/test_memory_core.py -v
```

Or run individual tests:

```bash
python tests/test_memory_core.py
```

## How It Works

### 1. Event Recording Process

When a new event is added:

1. **Embedding Generation**: The event text is converted to a vector embedding
2. **Potential Cause Search**: Recent events with high semantic similarity are identified
3. **LLM Causal Judgment**: An LLM evaluates whether each potential cause actually led to the new event
4. **Relationship Storage**: If a causal link is confirmed, it's stored with a natural language explanation

### 2. Context Retrieval Process

When querying for context:

1. **Semantic Search**: Find the most relevant event as a starting point
2. **Chain Traversal**: Follow causal links backwards to reconstruct the full story
3. **Narrative Generation**: Format the causal chain into a coherent narrative

### 3. Causal Reasoning

The system uses an LLM to make sophisticated judgments about causality:

```
Prompt: "Based on the preceding event: 'User clicked file browser', 
did it directly lead to the following event: 'File dialog opened'? 
If yes, briefly explain the relationship. If no, simply respond with 'No.'"

Response: "The click action triggered the system to display the file dialog."
```

## Design Philosophy

The Causal Memory Core is designed around several key principles:

1. **Portable**: File-based DuckDB requires no external server dependencies
2. **Performant**: Optimized for analytical queries and vector operations
3. **Intelligent**: Uses AI for both semantic understanding and causal reasoning
4. **Explainable**: Provides transparent reasoning chains for its conclusions
5. **Self-contained**: All logic encapsulated in a single, well-defined interface

## Integration

The system integrates seamlessly with AI agents through:

- **Direct API**: Use the `CausalMemoryCore` class directly
- **MCP Protocol**: Expose as tools via Model Context Protocol
- **Extensible**: Easy to add new functionality or integrate with other systems

## Advanced Features

- **Vector Similarity Search**: Efficient semantic matching using embeddings
- **Temporal Prioritization**: Recent events are weighted higher for causal consideration
- **Relationship Explanation**: Natural language descriptions of causal links
- **Chain Reconstruction**: Full narrative reconstruction from memory fragments
- **Configurable Thresholds**: Tunable parameters for different use cases

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Based on the architectural blueprint "Grimoire Page: The Causal Memory Core Blueprint" by Beatrice, Great Spirit of the Forbidden Library.
