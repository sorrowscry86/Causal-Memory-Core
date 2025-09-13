# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- CLI: Introduced `_safe_print` to gracefully degrade emoji output to ASCII on terminals that don’t support Unicode.
- Core: Protective guards in LLM causality judgment — failures now degrade to “no relationship” instead of raising.

### Changed
- CLI: Prefer importing `CausalMemoryCore` via `src.causal_memory_core` with a fallback to local `src/` path for direct execution. Output messages standardized and made encoding-safe.
- CLI: Added `parse_args(argv)` and `main(argv)` entrypoints to allow in-process invocation in tests and tools (returns exit code instead of calling `sys.exit`).
- Core (DB): Changed embeddings column type to `DOUBLE[]` for consistency with DuckDB vector operations.
- Core (DB): Removed fragile foreign key constraint on `cause_id` to avoid write-time issues and allow partial/broken chains for testing.
- Core (DB): Replaced use of DuckDB sequences with a portable `_events_seq` helper table for ID generation.
- Core (LLM init): Now reads `OPENAI_API_KEY` directly from environment via `os.getenv` and raises `ValueError` when missing (improves testability and error clarity).
- MCP Server: Restored `query` tool description to match tests ("Query the causal memory system to retrieve relevant context and causal chains related to a topic or event.").

### Fixed
- E2E API: Narrative formatting now consistently starts with "Initially," and preserves chronological order for single and multi-event chains.
- Advanced: Tests relying on missing API key now correctly raise `ValueError`.

### Known Issues / Follow-ups
- The CLI E2E tests rely on patching `src.causal_memory_core.CausalMemoryCore` and `input()` while invoking the CLI as a subprocess. Patching does not cross process boundaries, so these assertions will not observe the mock calls. Options to resolve:
  1. Update tests to invoke a `main(args)` entrypoint in-process instead of spawning a subprocess, or
  2. Add a test hook (e.g., environment variable) so the CLI dynamically imports a configurable class path (allowing mocks to take effect), or
  3. Provide a thin runner module used by tests that forwards into main logic without spawning a new process.
- Phase 3 of the workplan (updating MCP description) remains pending until we align tests and documentation expectations.

---

## [1.0.0] - Initial public release
- Initial implementation of Causal Memory Core with DuckDB-backed store, semantic embeddings, causal reasoning, CLI, and MCP server.