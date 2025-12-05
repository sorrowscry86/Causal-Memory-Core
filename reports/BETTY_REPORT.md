# Betty Report

**Date:** 2025-12-03

## Summary

- Restored `src/causal_memory_core.py` to the v1.1.2 implementation with soft-link fallback, embedding cache, and narrative formatting aligned with the project instructions.
- Updated `requirements.txt` so every dependency (duckdb, sentence-transformers, openai, numpy, python-dotenv, mcp, starlette, uvicorn, fastapi, slowapi, httpx, pydantic) matches the requested minimum versions.

## Testing

- **17/17 tests passed** (`tests/test_memory_core.py`) in 59 seconds.

## Next Steps

1. Exercise the CLI or MCP server to confirm higher-level flows remain green.
2. Consider a quick E2E run (`python -m pytest tests/e2e/ -v`) if additional confidence is needed.

=========================================== test session starts ===========================================
platform win32 -- Python 3.13.9, pytest-7.4.3, pluggy-1.6.0 -- C:\Users\Wykeve\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: D:\Development\Causal Memory Core
configfile: pytest.ini
plugins: anyio-4.10.0, aio-1.9.0, cov-4.1.0
collected 17 items

tests/test_memory_core.py::TestCausalMemoryCore::test_add_event_with_cause PASSED                    [  5%]
tests/test_memory_core.py::TestCausalMemoryCore::test_add_event_without_cause PASSED                 [ 11%]
tests/test_memory_core.py::TestCausalMemoryCore::test_cosine_similarity_calculation PASSED           [ 17%]
tests/test_memory_core.py::TestCausalMemoryCore::test_database_initialization PASSED                 [ 23%]
tests/test_memory_core.py::TestCausalMemoryCore::test_event_class PASSED                             [ 29%]
tests/test_memory_core.py::TestCausalMemoryCore::test_get_context_causal_chain PASSED                [ 35%]
tests/test_memory_core.py::TestCausalMemoryCore::test_get_context_delegates_to_query PASSED          [ 41%]
tests/test_memory_core.py::TestCausalMemoryCore::test_get_context_empty_string_raises_error PASSED   [ 47%]
tests/test_memory_core.py::TestCausalMemoryCore::test_get_context_no_events PASSED                   [ 52%]
tests/test_memory_core.py::TestCausalMemoryCore::test_get_context_single_event PASSED                [ 58%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_empty_string_raises_error PASSED         [ 64%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_no_relevant_context_returns_default_message PASSED [ 70%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_uses_embedding_cache PASSED              [ 76%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_valid_single_event PASSED                [ 82%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_whitespace_only_raises_error PASSED      [ 88%]
tests/test_memory_core.py::TestCausalMemoryCore::test_query_with_causal_chain_returns_full_narrative PASSED [ 94%]
tests/test_memory_core.py::TestCausalMemoryCore::test_similarity_threshold PASSED                    [100%]

=========================================== 17 passed in 59.21s ==========================================
