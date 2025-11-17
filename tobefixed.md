# Causal Memory Core - Action List

This document tracks all findings, recommendations, and action items from the comprehensive review of the Causal Memory Core project.

## Progression Tracking

- [ ] **Not Started**
- [ ] **In Progress**
- [ ] **Completed**
- [ ] **Won't Fix**

---

## 1. Issues & Bugs

| ID | Description | Severity | Status | Assigned To | Notes |
|----|-------------|----------|--------|-------------|-------|
| BUG-001 | `sentence-transformers` has a potential Arbitrary Code Execution vulnerability due to insecure `torch.load()` usage. | Critical | Not Started | TBD | The `_initialize_embedder` method in `src/causal_memory_core.py` might be affected. Investigate and mitigate. See [Snyk DB](https://security.snyk.io/package/pip/sentence-transformers/3.0.0) |
| BUG-002 | `numpy` has a potential vulnerability (CVE-2019-6446) related to `numpy.load` and unsafe unpickling. | Medium | Not Started | TBD | The project does not appear to use `numpy.load` directly, but a dependency might. It's worth investigating the usage of numpy arrays and ensuring no untrusted data is loaded. |

---

## 2. Code/Performance Improvements

| ID | Description | Severity | Status | Assigned To | Notes |
|----|-------------|----------|--------|-------------|-------|
| CPI-001 | The `_initialize_embedder` method hardcodes the embedding model. | Low | Not Started | TBD | Allow passing a `SentenceTransformer` model during `CausalMemoryCore` initialization for more flexibility. |
| CPI-002 | The `_judge_causality` method uses a broad `except Exception`. | Low | Not Started | TBD | Catch more specific exceptions to avoid masking unrelated errors and improve debugging. |
| CPI-003 | The `add_event` method lacks input validation for `effect_text`. | Medium | Not Started | TBD | Add validation to handle empty strings or other invalid inputs to prevent storing meaningless events. |
| CPI-004 | The `get_context` method is a redundant wrapper for the `query` method. | Low | Not Started | TBD | Consider deprecating `get_context` in a future version to simplify the public API. |
| CPI-005 | Review all database queries for potential SQL injection vulnerabilities. | Medium | Not Started | TBD | While the current queries seem safe, a thorough review is a good security practice. |
| CPI-006 | The test suite has 0% coverage for `src/api_server.py`. | High | Not Started | TBD | The API server logic is completely untested, which could hide significant bugs. Add comprehensive tests for all API endpoints. |
| CPI-007 | Improve test coverage for `src/causal_memory_core.py` and `src/mcp_server.py`. | Medium | Not Started | TBD | While coverage is good (90% and 94%), there are still untested lines of code. Aim for 100% coverage to ensure all edge cases are handled. |
| CPI-008 | Use a vector index for more efficient similarity searches. | High | Not Started | TBD | The current brute-force search will not scale. Implement a vector index (e.g., FAISS, Annoy, or DuckDB's VSS extension) for faster nearest neighbor searches. |
| CPI-009 | Cache query embeddings to avoid redundant computations. | Medium | Not Started | TBD | Implement a cache for query embeddings to improve performance for repeated queries. |
| CPI-010 | Implement a batch `add_events` method for more efficient event ingestion. | Medium | Not Started | TBD | A batch method would be much more performant for adding a large number of events. |
| CPI-011 | Make the consequence chain length configurable. | Low | Not Started | TBD | The hardcoded limit of 2 consequences might not be suitable for all use cases. Add a configuration option to control this. |
| CPI-012 | Improve the robustness of the causal judgement mechanism. | Medium | Not Started | TBD | The current LLM-based approach can be noisy. Explore more robust causal inference techniques or an ensemble of models. |

---

## 3. New Features & Enhancements

| ID | Description | Value | Status | Assigned To | Notes |
|----|-------------|-------|--------|-------------|-------|
| FE-001 | Visual Graph Explorer | High | Not Started | TBD | A web-based interface to visualize the causal graph would greatly improve usability and debugging. |
| FE-002 | Confidence Scoring for Causal Links | High | Not Started | TBD | Returning a confidence score for causal links would allow for more nuanced filtering and analysis. |
| FE-003 | Time-Based Queries | Medium | Not Started | TBD | The ability to query for events within a specific time range would be a powerful addition. |
| FE-004 | Event Summarization | Medium | Not Started | TBD | Automatically summarizing long causal chains would improve the user experience. |
| FE-005 | Multi-User Support | High | Not Started | TBD | Adding support for multiple users with separate memory stores would make the system much more useful. |
| FE-006 | Plugin Architecture | High | Not Started | TBD | A plugin architecture would allow for easy extension of the system with new functionality. |

---

## 4. Documentation & Product Quality

| ID | Description | Severity | Status | Assigned To | Notes |
|----|-------------|----------|--------|-------------|-------|
| DOC-001 | The "Recent Test Results" section in `README.md` is outdated. | Low | Not Started | TBD | Update the test results to reflect the current 100% pass rate. |
| DOC-002 | The documentation links in `README.md` are broken. | High | Not Started | TBD | Fix the broken links to the documentation files in the `docs/` directory. |
| DOC-003 | The `CONTRIBUTING.md` file is missing. | Medium | Not Started | TBD | Create a `CONTRIBUTING.md` file to provide guidelines for contributors. |
| DOC-004 | The Docker tags in `README.md` are outdated. | Low | Not Started | TBD | Update the Docker tags to reflect the latest version of the project. |
| DOC-005 | The performance metrics in `README.md` are not well-documented. | Medium | Not Started | TBD | Provide more information about how the performance metrics were measured to make them more meaningful. |
