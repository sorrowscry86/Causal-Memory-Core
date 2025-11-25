# Albedo Integration Guide (CMC)

This guide shows how to integrate the Causal Memory Core (CMC) with Albedo using the Memory-First Protocol outlined in `The_Bestowal_Plan.md`.

## MCP Connection

Add this server to your MCP client config:

```
{
  "mcpServers": {
    "causal-memory-core": {
      "command": "python",
      "args": ["src/mcp_server.py"],
      "cwd": "d:/Development/Causal Memory Core",
      "env": {
        "OPENAI_API_KEY": "<your_key>",
        "DB_PATH": "causal_memory.db",
        "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
        "LLM_MODEL": "gpt-4",
        "LLM_TEMPERATURE": "0.1",
        "MAX_POTENTIAL_CAUSES": "7",
        "SIMILARITY_THRESHOLD": "0.6",
        "TIME_DECAY_HOURS": "168"
      }
    }
  }
}
```

- Tools exposed: `add_event(effect: string)` and `query(query: string) -> string`.
- Ensure `OPENAI_API_KEY` is available in the environment running the server.

## Memory-First Protocol (Albedo)

Sequence to run before major actions:

1. QUERY: Use `query()` to retrieve relevant causal narratives for the current situation.
2. ANALYZE: Parse the narrative for root causes, prior attempts, and constraints.
3. CONTEXTUALIZE: Feed insights into your decision policy.
4. ACT: Execute the action.
5. RECORD: Call `add_event()` to persist the action and outcome.

### Query templates

- Problem Diagnosis: "What led to <current problem>?"
- Solution Selection: "What solutions worked for similar issues?"
- Risk Assessment: "What unintended consequences happened before when we did <action>?"
- Context Building: "What is the complete story behind <situation>?"

### Event recording patterns

Record events for:
- Commands executed
- Decisions with rationale
- Errors and resolution attempts
- Successful task completions
- User interactions and outcomes

## Prototype demo (local, no external APIs)

Run the demo script that exercises the protocol end-to-end using in-process mocks:

- File: `integration/albedo/memory_first_demo.py`
- Behavior: Real DB writes/reads with deterministic mock LLM and embedder (no network).

This is a PROTOTYPE to demonstrate flow; production wiring should call CMC via MCP.

## Configuration recommendations

From The Bestowal Plan:

- `SIMILARITY_THRESHOLD = 0.6`
- `MAX_POTENTIAL_CAUSES = 7`
- `TIME_DECAY_HOURS = 168`
- `LLM_MODEL = "gpt-4"`

## Performance safeguards

- Set a query timeout in your agent runtime (e.g., 10s) and fall back to operating without memory if needed.
- Add a small local cache for frequently accessed narratives.
- Record events asynchronously if the main loop must remain non-blocking.

## Notes

- Tests in this repo mock external services; run them to validate behavior without network access.
- When integrating into Albedo, prefer MCP for process isolation and standardized tooling.
