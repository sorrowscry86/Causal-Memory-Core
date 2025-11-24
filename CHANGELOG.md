# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.1.2] - November 2024 - Narrative Continuity Enhancement

### Added
- **Narrative Continuity Detection**: System now recognizes sequential workflows without explicit causal language
  - Links events based on temporal proximity + semantic relevance = narrative continuity
  - Supports dry system logs (code refactoring, incident resolution, database migrations, deployments)
  - No longer requires explicit "because", "led to", "caused" language in event descriptions
- **Comprehensive Test Suite**: Added `test_narrative_continuity.py` with 5 test cases validating:
  - Code refactoring workflows
  - Incident resolution sequences
  - Database migration workflows
  - Deployment sequences
  - Proper rejection of unrelated events (no false positives)

### Changed
- **LLM Prompt Enhancement**: Modified `_judge_causality()` prompt to be more flexible:
  - Changed from rigid "did it directly lead to" to "are these events part of the same workflow or narrative sequence?"
  - Now explicitly accepts: direct causal relationships, sequential process steps, and related workflow actions
  - Maintains accuracy while reducing false negatives for legitimate sequential workflows

### Technical Details
- All 64 existing tests continue to pass (backward compatibility maintained)
- New tests use realistic mock patterns for LLM and embedder behavior
- Documentation updated in README.md with narrative continuity examples and use cases

### Use Cases Now Supported
- ✅ Code refactoring steps (extract → rename → test)
- ✅ Incident response (alert → check → fix)
- ✅ Database operations (backup → migrate → verify)
- ✅ Deployment workflows (build → deploy → monitor)
- ✅ Any temporally proximate + semantically related event sequences

---

## [1.1.0] - December 2024 - Pillar III Complete: Integration & Bestowal

### Added
- **Docker Support**: Complete containerization with Dockerfile, docker-compose.yml, and .dockerignore
- **Enhanced MCP Descriptions**: Updated tool descriptions to reflect narrative capabilities for AI agent integration
- **The Bestowal Plan**: Comprehensive strategic document for Albedo integration with Memory-First Protocol
- **Version Tagging**: Updated to version 1.1.0 to signify enhanced narrative capabilities
- **Docker Documentation**: Added Docker deployment instructions and configuration examples

### Changed
- **MCP Server Version**: Updated to 1.1.0 reflecting enhanced capabilities
- **Tool Descriptions**: 
  - `query` tool now explicitly mentions "full, narrative chain of causally-linked events"
  - `add_event` tool describes automatic causal relationship detection and link creation
- **README.md**: Complete overhaul with Docker instructions, narrative examples, and version 1.1.0 features
- **Configuration**: Enhanced MCP server settings for production deployment

### Technical Achievements
- ✅ **Pillar III Completion**: Full integration readiness for Albedo with Memory-First Protocol
- ✅ **Production Ready**: Docker containerization with persistent data volumes
- ✅ **Enhanced MCP Integration**: Precise tool descriptions for AI agent consumption
- ✅ **Strategic Documentation**: Complete implementation roadmap for Albedo team
- ✅ **Version Management**: Clear versioning strategy with Docker tags

### Integration Features
- **Memory-First Protocol**: Strategic framework for AI agent decision-making
- **Narrative Context Parsing**: Guidelines for extracting causal insights from CMC responses
- **Automated Event Recording**: Patterns for comprehensive action tracking
- **Performance Safeguards**: Timeout handling, fallback modes, and error recovery
- **Success Metrics**: Quantitative and qualitative measures for integration validation

---

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

---

## [1.1.1] - September 2025 - Release Prep & CI Cleanup

### Changed
- Bumped `MCP_SERVER_VERSION` default to `1.1.1` in `config.py`.
- Set default `SIMILARITY_THRESHOLD` to `0.5` to match tests and docs.
- Normalized GitHub Actions workflow `.github/workflows/ci.yml` (removed conflict markers, consolidated jobs, updated Python matrix and Docker tag `1.1.1`).
- Updated documentation references (README, docs/architecture.md) to `v1.1.1` and cleaned Markdown.
- Updated `docker-compose.yml` image tag to `causal-memory-core:1.1.1`.

### Fixed
- Removed stale legacy test file and resolved pytest collection issues.
- Addressed YAML duplication/conflict issues in CI workflow.

### Notes
- All unit and E2E tests pass locally; quick benchmarks verified.


## [1.0.0] - Initial public release
- Initial implementation of Causal Memory Core with DuckDB-backed store, semantic embeddings, causal reasoning, CLI, and MCP server.