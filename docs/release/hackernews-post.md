# Show HN: CMC – Causal Memory Core with vitality-based forgetting for AI agents

**URL:** https://github.com/sorrowscry86/Causal-Memory-Core

---

Most agent memory systems are retrieval indexes: they accumulate every event and retrieve by similarity. CMC v1.2.0 adds a vitality-based forgetting algorithm: events decay over time, get boosts on retrieval and causal citation, and get archived below a threshold. Anchor selection for causal chain reconstruction is 70% semantic + 30% vitality, so recently-active events compete more effectively. DuckDB backend, MCP-compatible, MIT license.

---

## Notes for posting

- Post on a weekday between 8–10am ET for best front-page odds
- Be available to respond to comments for the first 2–3 hours — HN ranks heavily on early engagement velocity
- Likely questions to prepare for:
  - "How does this compare to MemGPT / Letta?" (CMC is causal-chain focused + vitality forgetting; MemGPT is paging-based; different problem)
  - "Why DuckDB?" (embedded, zero ops, fast on analytical queries, portable)
  - "Why not just TTL?" (TTL is time-only; vitality is usage-weighted — a frequently-accessed old event stays alive)
  - "Does this work with local LLMs?" (yes, any OpenAI-compatible endpoint)
  - "What's vcL2l?" (internal structured chain protocol; can ignore for public release or explain briefly)
