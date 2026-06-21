# Your AI Agent's Memory Is Just a Database. Here's What Actual Memory Looks Like.

**Tags:** `ai`, `python`, `agents`, `opensource`

---

Every agent memory system I've seen has the same architecture: store events, embed them, retrieve by similarity. The more you use the agent, the more events accumulate. Eventually your retrieval is competing with thousands of events of varying relevance, and the agent starts behaving as though everything that ever happened is equally important.

That's not memory. That's a retrieval index.

Real memory forgets. Not randomly — strategically. Things you've recalled recently feel closer. Things you haven't touched in months feel distant. Important events that other events cite as causes stay vivid. Low-signal noise fades.

CMC v1.2.0 ships a **vitality-based forgetting algorithm** that does exactly this.

---

## How Vitality Works

Every event in CMC carries a `vitality` score from 0 to 1, initialized at 1.0 on creation. Three things affect it:

**Time decay.** Every maintenance sweep:
```
vitality = vitality × exp(-DECAY_RATE × hours_elapsed)
```
With the default `DECAY_RATE = 0.001`, a month of inactivity brings vitality down to about 0.47. A year brings it to about 0.0002 — below the archive threshold.

**Access boost.** Every time `query()` returns an event: `+0.2` vitality. Things you're actively thinking about stay fresh.

**Causal boost.** When a new event links an older event as its cause: `+0.1` vitality. Events that explain other events stay relevant.

**Archiving.** When vitality drops below `0.05`, the event moves to `events_archive` — not deleted, just deprioritized. History is preserved. Active retrieval stays clean.

---

## It Changes Query Behavior Too

Anchor selection for causal chain reconstruction is now `70% semantic similarity + 30% vitality`. High-vitality events compete more effectively for the anchor slot. A semantically similar but stale event loses ground to a semantically similar but recently-active one.

This is the right behavior. "What's relevant to this query" and "what has the agent been working with lately" should both inform what surfaces.

---

## Maintenance Is Explicit

There's no background thread. You trigger maintenance when it makes sense for your use case:

```python
result = memory.run_memory_maintenance()
# {scanned: 142, updated: 138, archived: 4, live_count: 138,
#  vitality_min: 0.08, vitality_max: 1.0, vitality_mean: 0.71}
```

Or via the MCP tool: `run_memory_maintenance` with no arguments.

---

## vcL2l Integration (v1.2.0 also ships this)

CMC now has two new MCP tools for agents using structured chain protocols:

- **`query_as_ref`** — query memory, receive the result as a vcL2l CONTEXT_REF ref dict. Ready to embed in an agent's completion chain as evidence.
- **`add_event_chain`** — pass a vcL2l wire-format chain; CMC extracts the learning-flagged steps and stores them as causal memory events automatically.

---

## What CMC Is

CMC is a Python library + MCP server. DuckDB backend (embedded, no separate DB process). OpenAI-compatible LLM for causal relationship detection. Semantic embeddings via sentence-transformers.

```python
from causal_memory_core import CausalMemoryCore
memory = CausalMemoryCore(db_path="agent.db")

memory.add_event("Deployed the new auth service")
memory.add_event("Users started reporting login failures")
memory.add_event("Rolled back the auth deployment")

print(memory.query("why did users have login failures?"))
# → "Users had login failures because the new auth service was deployed,
#    which caused the failures, leading to a rollback."
```

MIT license. [GitHub →](https://github.com/sorrowscry86/Causal-Memory-Core)

---

*Cover image suggestion: dark background, glowing event nodes connected by causal arrows, some nodes dim/faded (archived), some bright (high vitality).*
