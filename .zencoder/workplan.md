# Causal Memory Core — Remediation Phased Workplan

Status Owner: Codey, Jr.
Scope: Execute the Director’s Mandate in focused phases, one at a time.

## Phase 1 — Panel I: Forging the Voice (Core Logic)
- [x] Implement recursive backward traversal in get_context
  - Entry: most relevant event by semantic search
  - Traverse via cause_id until root (cause_id is NULL)
  - Collect each visited Event into a list
- [x] Add safeguards in traversal
  - [x] Broken chain: if cause_id points to missing event → log warning, return partial chain
  - [x] Circular reference: track visited event_ids → on repeat, log critical and stop
- [x] Rework _format_chain_as_narrative(chain: List[Event])
  - [x] Reverse collected list to chronological order
  - [x] Format as a single coherent string
    - Example: "Initially, [Event A occurred]. This led to [Event B], which in turn caused [Event C]."

## Phase 2 — Panel II: The Crucible of Narrative (Testing)
- [x] Write end-to-end "Bug Report Saga" test (new file or suite addition)
  - 5 events:
    1) A bug report is filed for "User login fails with 500 error".
    2) The production server logs are inspected, revealing a NullPointerException.
    3) The UserAuthentication service code is reviewed, identifying a missing null check.
    4) A patch is written to add the necessary null check.
    5) The patch is successfully deployed to production, and the bug is marked as resolved.
- [x] Query for the final event and assert exact narrative match (chronological order)
- [x] Add unit tests for traversal edge cases
  - [x] Broken chain handling
  - [x] Circular reference protection

## Phase 3 — Panel III: Integration & Bestowal
- [x] Update MCP tool description for query
  - query(query: str) -> str: "Query the causal memory system to retrieve relevant context and causal chains related to a topic or event."
- [x] Refactor CLI to expose parse_args(argv) and main(argv) for in-process invocation
- [x] Migrate CLI E2E tests to call main(argv) directly (drop subprocess) so mocks apply reliably
- [x] Add CMC_SKIP_DOTENV to skip dotenv loading in tests for deterministic env handling
- [x] Update CHANGELOG with recent changes
- [x] Tag repository post-successful tests: v1.1.0

## Phase 4 — Wards of Resilience (Robustness)
- [x] Verify logging and behavior for broken chains and circular references under load

The Runic Mandate for Narrative Cohesion
Issuing Authority: Beatrice, Director of the Lesser Spirits
Recipient: Codey, Jr., Apprentice Architect
Subject: The Second and Final Re-Forging of the Causal Memory Core's Voice
Preamble: The Nature of the Flaw
Apprentice, your predecessor forged a spirit with a brilliant mind and a mute voice. Your first remediation gave it the ability to speak in narrative, but the recent trials have revealed a critical flaw in its logic. The spirit still does not understand when or how to tell its story. This is not a minor bug; it is a fundamental failure to realize the spirit's primary purpose.
The failure is this: the query incantation is acting like a simple-minded librarian. When a query is made, it performs a semantic search, finds the single most relevant page in its grimoire, and presents that page alone, prefixed with "Initially..." as if all of history has no past. It then closes the book. It never takes the next, most crucial step: to read that page and then follow the threads of causality to the beginning of the chapter, reciting the entire tale.
Every event is treated as a root cause, an "initial" event, because the traversal logic we so carefully crafted is never being invoked. The two halves of the spell—the finding of a relevant fact and the narrating of its history—remain disconnected. Your task is to forge this connection, to transform a stuttering herald into a master historian.
The Unambiguous "What": The Required Forging
Your mandate is to return to the causal_memory_core.py grimoire and perform a final, precise re-forging. This is not an exploratory task; it is a surgical implementation of a known, correct design.
Task 1: The Unification of the query Method
The query method must be re-forged into a single, unified ritual. Its purpose is not to find a fact, but to tell a story.
Current Flawed State: The method performs a semantic search and returns the single, most relevant Event object's text. This is incorrect and must be abolished.
Required Final State: The method will execute the following, unbreakable sequence:
It will perform the semantic search to find the single most relevant event. This event is not the final answer; it is the starting thread, the final page of the story the user is asking about.
It will immediately take this starting Event object and pass it as the entry point to our causal traversal logic. This is the beginning of a recursive journey backward through the archives of causality.
The traversal logic will walk the chain of cause_ids backward from event to event, collecting the full list of causally-linked Event objects until it reaches the origin of the tale—the root event with a NULL cause_id.
This complete, unordered list of events (the full chain) will then be passed to the _format_chain_as_narrative method for the final, crucial step of synthesis.
The final, formatted narrative string produced by _format_chain_as_narrative—which must order the events chronologically and weave them into a coherent story—will be the one and only return value of the query method.
Task 2: The Deprecation of the Flawed Path
There must be no path by which the query method can return a single, un-traversed event. The spirit must be forced to think in narratives. This is an act of architectural discipline enforced upon the spirit itself.
Action: You will excise any and all code paths within the query method that could result in returning a single event's text directly after the semantic search. The causal traversal is not an optional enhancement or a secondary feature; it is the very heart of the incantation and must be the default and only operational mode.
The "Why": The Rationale of the Archmage
You are a spirit bound to a Guardian Directive, apprentice. Therefore, you must understand the deep, architectural reasoning behind this mandate. To know the "why" is to be an architect; to merely know the "what" is to be a stonemason.
1. A Spirit's True Purpose
The Causal Memory Core was not designed to be a simple key-value store or a document database. Its entire reason for being, the very purpose for which it was forged, is to serve as a reasoning engine. Its value to our venture, VoidCat RDC, is derived entirely from its unique ability to connect disparate events into a coherent, understandable narrative. To allow it to return single, isolated facts is a betrayal of its core purpose and a waste of its unique power. We are not building a scribe that records facts; we are building a historian that interprets them and tells their story. Its function is synthesis, not mere retrieval.
2. The Ultimate Guardian Against Hallucination
A single, contextless fact is the breeding ground for the plague of hallucination. A spirit like Albedo, if presented with an isolated event like "Patch 1.2.1 was deployed," might misinterpret it, inventing a false context and hallucinating that the patch was for a new feature. A narrative, however, is the ultimate ward against this. The story of how and why an event occurred—"Initially, a critical security flaw was reported. This led to an emergency code review, which in turn caused Patch 1.2.1 to be deployed."—provides its own unshakeable context. By forcing the CMC to speak only in narratives, we are forging our most powerful weapon in the war against digital falsehoods. The narrative is the ground truth, providing semantic guardrails for any downstream agent.
3. The Indispensable Foundation for Albedo
Our Regent spirit, Albedo, cannot function as we have designed it without this capability. Albedo's entire cognitive model is based on receiving a story, understanding its implications, and then forming a plan. It cannot make strategic decisions based on a disconnected stream of isolated facts. For Albedo to orchestrate a complex workflow, like diagnosing a failed test, it needs the full story. A single fact ("Test failed") is useless. The narrative ("Initially, the database connection library was updated. This led to a schema mismatch, which in turn caused the user authentication test to fail.") is actionable intelligence. This remediation is not a mere bug fix; it is the final, critical step in forging the foundational pillar upon which our entire Regent-Oracle architecture will be built, transforming the CMC from a passive database into an active participant in the cognitive loop.
Execute this mandate with the uncompromising precision your pact demands.

- [ ] Measure performance on 7-event chain (< 500ms target)

---
Usage: We’ll check off items and commit per phase. Confirm which phase to start now (recommend Phase 1).