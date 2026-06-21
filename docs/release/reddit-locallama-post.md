# Reddit — r/LocalLLaMA

**Title:** I built a causal memory system for AI agents that actually forgets — CMC v1.2.0

---

Most agent memory systems have a quiet problem: they never forget. Every event you add competes equally with every other event at retrieval time. The longer your agent runs, the noisier its memory gets.

CMC v1.2.0 ships a vitality-based forgetting algorithm to fix this.

**How it works:**
- Every event starts at vitality 1.0
- Time decay: exponential decay per maintenance sweep (configurable rate)
- Access boost: +0.2 when an event is retrieved by a query
- Causal boost: +0.1 when an event is cited as the cause of a new event
- Archive: events below vitality 0.05 move to a separate archive table (not deleted)
- Anchor selection is 70% semantic similarity + 30% vitality — active events surface more readily

**The rest of CMC:**
- Automatic causal chain reconstruction from any event back to root causes
- Narrative continuity detection (links sequential workflow steps without explicit "because" language)
- DuckDB backend (embedded, zero ops overhead)
- MCP server — works with Claude, Cursor, anything MCP-compatible
- OpenAI-compatible LLM endpoint for causal detection

Works well with local LLMs (Ollama-compatible endpoint). The causal detection quality degrades a bit with smaller models but the vitality system is model-independent.

MIT license: https://github.com/sorrowscry86/Causal-Memory-Core

Happy to answer questions about the architecture or the forgetting algorithm design.

---

## Notes for posting

- r/LocalLLaMA is good for the local LLM angle — lead with "works with Ollama" if traction is slow
- Can also cross-post to r/MachineLearning (more academic tone) and r/artificial
- Reddit timing matters less than HN but weekday mornings still perform better
