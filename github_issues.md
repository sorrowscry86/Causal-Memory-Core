# GitHub Issues

This file contains a list of all the issues identified during the comprehensive review of the Causal Memory Core project. Each issue is formatted as a Markdown block that can be easily copied into a new GitHub issue.

---

### BUG-001: `sentence-transformers` has a potential Arbitrary Code Execution vulnerability

**Body:**

The `sentence-transformers` package has a potential Arbitrary Code Execution vulnerability due to insecure `torch.load()` usage. The `_initialize_embedder` method in `src/causal_memory_core.py` might be affected. This is a critical security issue that needs to be investigated and mitigated immediately.

**Labels:** `bug`, `security`, `critical`

---

### BUG-002: `numpy` has a potential vulnerability related to unsafe unpickling

**Body:**

The `numpy` package has a potential vulnerability (CVE-2019-6446) related to `numpy.load` and unsafe unpickling. While the project does not appear to use `numpy.load` directly, a dependency might. It's worth investigating the usage of numpy arrays and ensuring no untrusted data is loaded.

**Labels:** `bug`, `security`, `medium`

---

### CPI-001: The `_initialize_embedder` method hardcodes the embedding model

**Body:**

The `_initialize_embedder` method in `src/causal_memory_core.py` hardcodes the embedding model. It would be more flexible to allow passing a `SentenceTransformer` model during `CausalMemoryCore` initialization.

**Labels:** `improvement`, `low`

---

### CPI-002: The `_judge_causality` method uses a broad `except Exception`

**Body:**

The `_judge_causality` method in `src/causal_memory_core.py` uses a broad `except Exception` clause. It would be better to catch more specific exceptions to avoid masking unrelated errors and improve debugging.

**Labels:** `improvement`, `low`

---

### CPI-003: The `add_event` method lacks input validation for `effect_text`

**Body:**

The `add_event` method in `src/causal_memory_core.py` lacks input validation for `effect_text`. This could lead to issues if an empty string or other invalid input is provided. Add validation to handle empty strings or other invalid inputs to prevent storing meaningless events.

**Labels:** `improvement`, `medium`

---

### CPI-004: The `get_context` method is a redundant wrapper for the `query` method

**Body:**

The `get_context` method in `src/causal_memory_core.py` is a redundant wrapper for the `query` method. Consider deprecating `get_context` in a future version to simplify the public API.

**Labels:** `improvement`, `low`

---

### CPI-005: Review all database queries for potential SQL injection vulnerabilities

**Body:**

While the current database queries in `src/causal_memory_core.py` seem safe, a thorough review is a good security practice to prevent potential SQL injection vulnerabilities.

**Labels:** `improvement`, `security`, `medium`

---

### CPI-006: The test suite has 0% coverage for `src/api_server.py`

**Body:**

The test suite has 0% coverage for `src/api_server.py`. The API server logic is completely untested, which could hide significant bugs. Add comprehensive tests for all API endpoints.

**Labels:** `improvement`, `testing`, `high`

---

### CPI-007: Improve test coverage for `src/causal_memory_core.py` and `src/mcp_server.py`

**Body:**

While the test coverage for `src/causal_memory_core.py` (90%) and `src/mcp_server.py` (94%) is good, there are still untested lines of code. Aim for 100% coverage to ensure all edge cases are handled.

**Labels:** `improvement`, `testing`, `medium`

---

### CPI-008: Use a vector index for more efficient similarity searches

**Body:**

The current brute-force similarity search in `src/causal_memory_core.py` will not scale well. Implement a vector index (e.g., FAISS, Annoy, or DuckDB's VSS extension) for faster nearest neighbor searches.

**Labels:** `improvement`, `performance`, `high`

---

### CPI-009: Cache query embeddings to avoid redundant computations

**Body:**

The `query` method in `src/causal_memory_core.py` computes the embedding for the query string every time it's called. Implement a cache for query embeddings to improve performance for repeated queries.

**Labels:** `improvement`, `performance`, `medium`

---

### CPI-010: Implement a batch `add_events` method for more efficient event ingestion

**Body:**

The `add_event` method in `src/causal_memory_core.py` processes events one at a time. A batch `add_events` method would be much more performant for adding a large number of events.

**Labels:** `improvement`, `performance`, `medium`

---

### CPI-011: Make the consequence chain length configurable

**Body:**

The `query` method in `src/causal_memory_core.py` has a hardcoded limit of 2 consequences. This might not be suitable for all use cases. Add a configuration option to control this.

**Labels:** `improvement`, `low`

---

### CPI-012: Improve the robustness of the causal judgement mechanism

**Body:**

The `_judge_causality` method in `src/causal_memory_core.py` relies on a single LLM call, which can be noisy. Explore more robust causal inference techniques or an ensemble of models.

**Labels:** `improvement`, `medium`

---

### FE-001: Visual Graph Explorer

**Body:**

A web-based interface to visualize the causal graph would greatly improve the usability and debugging of the Causal Memory Core.

**Labels:** `feature`, `high`

---

### FE-002: Confidence Scoring for Causal Links

**Body:**

Returning a confidence score for causal links would allow for more nuanced filtering and analysis of the causal graph.

**Labels:** `feature`, `high`

---

### FE-003: Time-Based Queries

**Body:**

The ability to query for events within a specific time range would be a powerful addition to the Causal Memory Core.

**Labels:** `feature`, `medium`

---

### FE-004: Event Summarization

**Body:**

Automatically summarizing long causal chains would improve the user experience of the Causal Memory Core.

**Labels:** `feature`, `medium`

---

### FE-005: Multi-User Support

**Body:**

Adding support for multiple users with separate memory stores would make the Causal Memory Core much more useful in a collaborative environment.

**Labels:** `feature`, `high`

---

### FE-006: Plugin Architecture

**Body:**

A plugin architecture would allow for easy extension of the Causal Memory Core with new functionality, such as custom causal inference models or new data sources.

**Labels:** `feature`, `high`

---

### DOC-001: The "Recent Test Results" section in `README.md` is outdated

**Body:**

The "Recent Test Results" section in `README.md` is outdated. Update the test results to reflect the current 100% pass rate.

**Labels:** `documentation`, `low`

---

### DOC-002: The documentation links in `README.md` are broken

**Body:**

The documentation links in `README.md` are broken. Fix the broken links to the documentation files in the `docs/` directory.

**Labels:** `documentation`, `high`

---

### DOC-003: The `CONTRIBUTING.md` file is missing

**Body:**

The `CONTRIBUTING.md` file is missing. Create a `CONTRIBUTING.md` file to provide guidelines for contributors.

**Labels:** `documentation`, `medium`

---

### DOC-004: The Docker tags in `README.md` are outdated

**Body:**

The Docker tags in `README.md` are outdated. Update the Docker tags to reflect the latest version of the project.

**Labels:** `documentation`, `low`

---

### DOC-005: The performance metrics in `README.md` are not well-documented

**Body:**

The performance metrics in `README.md` are not well-documented. Provide more information about how the performance metrics were measured to make them more meaningful.

**Labels:** `documentation`, `medium`
