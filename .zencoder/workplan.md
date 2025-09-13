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
- [ ] Measure performance on 7-event chain (< 500ms target)

---
Usage: We’ll check off items and commit per phase. Confirm which phase to start now (recommend Phase 1).