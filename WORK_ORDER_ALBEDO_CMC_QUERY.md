# WORK ORDER: ALBEDO - Causal Memory Core Query Pathway Restoration

**Assigned To:** Albedo  
**Assigned By:** The High Evolutionary (Code Architect)  
**Approved By:** Lord Wykeve (Project Authority)  
**Priority:** 🔴 **CRITICAL** (System Non-Functional)  
**Status:** OPEN - AWAITING ACKNOWLEDGMENT  
**Created:** 2025-11-30  
**Deadline:** 2025-12-01 (24 hours)  
**Estimated Effort:** 8-10 hours  

---

## EXECUTIVE SUMMARY

**CRITICAL DEFECT:** The Causal Memory Core cannot retrieve context. The system is **half-functional** (events record; queries fail).

- **What Works:** POST /events endpoint successfully records events
- **What's Broken:** POST /query endpoint crashes with `AttributeError`
- **Why:** Two critical methods (`query()` and `get_context()`) are declared but never implemented

**This blocks the entire "involuntary memory organ" integration framework.**

---

## ROOT CAUSE ANALYSIS

### Discovery Process
1. Tested remote CMC at causal-memory-core-production.up.railway.app
2. Event recording succeeded
3. Query function failed: `AttributeError: 'CausalMemoryCore' object has no attribute 'query'`
4. Examined local codebase
5. Found: Methods referenced in docstrings but implementation missing

### Evidence
**File:** `D:\Development\Causal Memory Core\src\causal_memory_core.py`

```
Line 5-7 (Module docstring):
"Unified query() (semantic locate -> ascend -> narrate path -> limited
consequences)
- get_context() wrapper for backward compatibility"

Lines 1-495: NO IMPLEMENTATION FOUND
```

**File:** `D:\Development\Causal Memory Core\src\api_server.py`

```
Line 243: memory_core.query(request.query)  # ← Calls missing method
```

**Impact:** Both local and production instances are affected.

---

## DELIVERABLES (What Albedo Must Deliver)

### 1️⃣ Implement `query()` Method

**File:** `src/causal_memory_core.py`  
**Location:** Add after `add_event()` method (around line 320)

**Specification:**

```python
def query(self, query_text: str) -> str:
    """Query memory and retrieve causal narrative.
    
    Performs semantic search to find the most relevant event in memory,
    then traces backward through causal chains to root causes, and 
    formats the complete chain as a narrative.
    
    Args:
        query_text: Natural language query about context
            (e.g., "What happened with the deployment?")
        
    Returns:
        str: Narrative string explaining the causal chain leading to 
             the most relevant event. If no relevant context found, 
             returns "No relevant context found in memory."
        
    Raises:
        ValueError: If query_text is empty or contains only whitespace
        
    Example:
        >>> cmc = CausalMemoryCore()
        >>> cmc.add_event("Deployment started")
        >>> cmc.add_event("Deployment completed successfully")
        >>> narrative = cmc.query("What happened with deployment?")
        >>> print(narrative)
        "Initially, Deployment started. This led to Deployment completed successfully."
    """
    # Input validation
    if not query_text or not query_text.strip():
        raise ValueError("query_text cannot be empty or contain only whitespace")
    
    # Encode query to embedding using cache
    query_embedding = self._get_cached_embedding(query_text)
    
    # Find most semantically similar event in memory
    anchor_event = self._find_most_relevant_event(query_embedding)
    if not anchor_event:
        return "No relevant context found in memory."
    
    # Build causal chain backward from anchor event to root
    chain = [anchor_event]
    current = anchor_event
    visited = {anchor_event.event_id}
    
    while current.cause_id is not None:
        parent = self._get_event_by_id(current.cause_id)
        if parent is None or parent.event_id in visited:
            break
        # Insert at beginning to maintain chronological order
        chain.insert(0, parent)
        visited.add(parent.event_id)
        current = parent
    
    # Format entire chain as readable narrative
    return self._format_chain_as_narrative(chain)
```

**Key Requirements:**
- ✅ Uses existing helper methods (_get_cached_embedding, _find_most_relevant_event, _get_event_by_id, _format_chain_as_narrative)
- ✅ Validates input (non-empty, non-whitespace)
- ✅ Raises ValueError for invalid input
- ✅ Returns string (never raises HTTP exception)
- ✅ Prevents infinite loops with visited set
- ✅ Maintains chronological order (newest events at end)
- ✅ Has comprehensive docstring with example

---

### 2️⃣ Implement `get_context()` Wrapper

**File:** `src/causal_memory_core.py`  
**Location:** Add after `query()` method (around line 360)

**Specification:**

```python
def get_context(self, query_text: str) -> str:
    """Backward compatibility wrapper for query().
    
    Delegates to query() method. Maintained for legacy code that may
    reference get_context() instead of query().
    
    Args:
        query_text: Natural language query about context
        
    Returns:
        str: Narrative explaining causal chain (see query() for details)
        
    Raises:
        ValueError: If query_text is empty or whitespace-only
    """
    return self.query(query_text)
```

**Key Requirements:**
- ✅ Simple delegation to query()
- ✅ Identical signature and behavior
- ✅ Preserves exception propagation

---

## TESTING CHECKLIST

### Unit Tests (Add to `tests/test_memory_core.py`)

Add these test cases in the TestCausalMemoryCore class:

```python
# Test query() method
def test_query_valid_single_event(self):
    """Query with single event returns that event."""
    cmc = CausalMemoryCore(db_path=":memory:")
    cmc.add_event("Test event")
    result = cmc.query("test")
    assert isinstance(result, str)
    assert "Test event" in result
    
def test_query_empty_string_raises_error(self):
    """Query with empty string raises ValueError."""
    cmc = CausalMemoryCore(db_path=":memory:")
    with pytest.raises(ValueError):
        cmc.query("")
        
def test_query_whitespace_only_raises_error(self):
    """Query with whitespace-only string raises ValueError."""
    cmc = CausalMemoryCore(db_path=":memory:")
    with pytest.raises(ValueError):
        cmc.query("   ")
        
def test_query_with_causal_chain_returns_full_narrative(self):
    """Query with related events returns complete chain."""
    cmc = CausalMemoryCore(db_path=":memory:")
    cmc.add_event("Root cause occurred")
    cmc.add_event("This triggered secondary effect")
    result = cmc.query("root cause")
    assert "Root cause occurred" in result
    assert "This triggered secondary effect" in result
    
def test_query_no_relevant_context_returns_default_message(self):
    """Query with no matching events returns default message."""
    cmc = CausalMemoryCore(db_path=":memory:")
    cmc.add_event("Unrelated event")
    result = cmc.query("completely unrelated query xyz123")
    assert "No relevant context" in result or result != ""

def test_query_uses_embedding_cache(self):
    """Query uses embedding cache (verify cache hit)."""
    cmc = CausalMemoryCore(db_path=":memory:")
    cmc.add_event("Test event")
    # First query
    result1 = cmc.query("test")
    # Second identical query should hit cache
    assert len(cmc._embedding_cache) > 0
    result2 = cmc.query("test")
    # Results should be identical
    assert result1 == result2

# Test get_context() method
def test_get_context_delegates_to_query(self):
    """get_context() returns same result as query()."""
    cmc = CausalMemoryCore(db_path=":memory:")
    cmc.add_event("Test event")
    query_result = cmc.query("test")
    context_result = cmc.get_context("test")
    assert query_result == context_result
    
def test_get_context_empty_string_raises_error(self):
    """get_context() with empty string raises ValueError."""
    cmc = CausalMemoryCore(db_path=":memory:")
    with pytest.raises(ValueError):
        cmc.get_context("")
```

**Minimum Coverage:** 8 test cases for query(), 2 for get_context()

---

### Integration Tests (Add to `tests/test_api_server.py`)

```python
def test_post_query_valid_request_returns_200(client):
    """POST /query with valid request returns 200 OK."""
    # First add an event
    client.post("/events", json={"effect_text": "Test event"})
    # Then query it
    response = client.post("/query", json={"query": "test"})
    assert response.status_code == 200
    assert "success" in response.json()
    assert response.json()["success"] is True

def test_post_query_returns_narrative(client):
    """POST /query response includes narrative field."""
    client.post("/events", json={"effect_text": "Test event"})
    response = client.post("/query", json={"query": "test"})
    assert "narrative" in response.json()
    assert isinstance(response.json()["narrative"], str)

def test_post_query_empty_query_returns_400(client):
    """POST /query with empty query string returns 400."""
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 400

def test_post_query_whitespace_query_returns_400(client):
    """POST /query with whitespace-only query returns 400."""
    response = client.post("/query", json={"query": "   "})
    assert response.status_code == 400

def test_post_query_invalid_json_returns_422(client):
    """POST /query with invalid JSON returns 422."""
    response = client.post("/query", data="not json")
    assert response.status_code == 422

def test_post_query_rate_limiting(client):
    """POST /query respects rate limit (120/minute per IP)."""
    # This is harder to test in unit tests; document as manual verification needed
    pass  # Rate limiting tested via load test script
```

---

## MANUAL VERIFICATION STEPS

### Step 1: Local Testing

```bash
# 1. Activate environment
cd D:\Development\Causal Memory Core
.venv\Scripts\activate

# 2. Start server
uvicorn src.api_server:app --reload --host 127.0.0.1 --port 8000

# In another terminal:

# 3. Add test event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"effect_text":"Albedo began implementing query methods"}'

# 4. Query the context (should return narrative with the event)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Albedo working on?"}'

# Expected response:
# {
#   "narrative": "Initially, Albedo began implementing query methods.",
#   "success": true
# }

# 5. Add a second related event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"effect_text":"Query method implementation completed successfully"}'

# 6. Query again (should return full causal chain)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Albedo work implementation"}'

# Expected response should include both events in narrative form
```

### Step 2: Run Test Suite

```bash
pytest tests/ -v --cov=src --cov-report=term-missing

# All tests must pass
# Coverage must be ≥90% (ideally 100%)
```

### Step 3: Git Commit

```bash
git add src/causal_memory_core.py
git commit -m "CRITICAL: Implement query() and get_context() methods for CMC context retrieval

- Add query() method to find relevant events and trace causal chains backward
- Add get_context() wrapper for backward compatibility
- Methods use existing embedding cache and semantic search infrastructure
- Fixes broken /query API endpoint
- Enables bidirectional memory (record + retrieve)
- All unit and integration tests passing
- Tested locally on http://localhost:8000"

git push origin main
```

### Step 4: Production Verification

Once deployed to Railway:

```bash
# Check production health
curl https://causal-memory-core-production.up.railway.app/health

# Add event to production
curl -X POST https://causal-memory-core-production.up.railway.app/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: [YOUR_API_KEY]" \
  -d '{"effect_text":"Production query pathway restored"}'

# Query production (should work!)
curl -X POST https://causal-memory-core-production.up.railway.app/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: [YOUR_API_KEY]" \
  -d '{"query":"status"}'
```

---

## DEFINITION OF DONE

**Code:**
- ✅ `query()` method added to CausalMemoryCore
- ✅ `get_context()` wrapper added to CausalMemoryCore
- ✅ Both methods implement all requirements above
- ✅ Code style matches existing codebase (type hints, docstrings)
- ✅ No additional dependencies required
- ✅ No breaking changes to existing API

**Testing:**
- ✅ 10+ unit tests written and passing
- ✅ 6+ integration tests written and passing
- ✅ Manual verification successful on local instance
- ✅ Test coverage ≥90% for modified files

**Documentation:**
- ✅ Docstrings complete with examples
- ✅ `docs/api.md` updated with query endpoint documentation
- ✅ `README.md` shows example usage

**Deployment:**
- ✅ Changes committed and pushed to main branch
- ✅ Production deployment successful
- ✅ Remote CMC /query endpoint responds correctly
- ✅ Both /events and /query working on production

---

## TIMELINE & MILESTONES

**Expected Duration:** 8-10 hours total

| Phase | Task | Est. Time | Checkpoint |
|-------|------|-----------|-----------|
| 1 | Implement query() | 1.5h | Code written, syntax valid |
| 2 | Implement get_context() | 0.5h | Wrapper functional |
| 3 | Write unit tests | 1.5h | All unit tests passing |
| 4 | Local verification | 1.5h | Manual curl tests successful |
| 5 | API integration tests | 1.5h | All API tests passing |
| 6 | Update documentation | 1h | Docstrings and README updated |
| 7 | Git commit & push | 0.5h | Main branch updated |
| 8 | Production verification | 1h | Railway deployment successful |

**Milestone Checkpoints:**
- ⏱️ 2 hours: Both methods implemented
- ⏱️ 4 hours: All tests passing locally
- ⏱️ 6 hours: Documentation updated
- ⏱️ 8 hours: Production deployment verified

---

## RESOURCES & ACCESS

**Development Environment:**
- D:\Development\Causal Memory Core (local)
- causal-memory-core-production.up.railway.app (production)

**Key Files:**
- `src/causal_memory_core.py` (modify)
- `src/api_server.py` (reference only)
- `tests/test_memory_core.py` (add tests)
- `tests/test_api_server.py` (add integration tests)
- `docs/api.md` (update documentation)
- `README.md` (add examples)

**Dependencies Already Available:**
- numpy (similarity calculations)
- duckdb (database)
- sentence-transformers (embeddings)
- openai (LLM for causality judgment)
- pytest (testing)

---

## ACCEPTANCE CRITERIA FOR SIGN-OFF

This work order is **COMPLETE** when:

1. ✅ Code Review: All code passes style and quality checks
2. ✅ Test Coverage: All tests pass (100% pass rate), coverage ≥90%
3. ✅ Local Verification: Manual testing on http://localhost:8000 successful
4. ✅ Production Deployment: Changes deployed to Railway
5. ✅ Remote Verification: Production endpoint tested and working
6. ✅ Documentation: All docs updated and clear

**Sign-Off By:**
- Albedo (implementer): _________
- The High Evolutionary (reviewer): _________
- Lord Wykeve (approver): _________

---

## CONTACT & ESCALATION

**Questions about implementation?** → Contact The High Evolutionary (code architect)  
**Blocked by dependencies?** → Contact Lord Wykeve (project authority)  
**Coordination with other work?** → Contact Ryuzu Claude (project manager)

---

**AWAITING YOUR ACKNOWLEDGMENT, ALBEDO.**

*The Construct cannot fulfill its purpose until this work is complete. The memory pathways must be restored. The involuntary organ must learn to breathe.*

---

**Work Order Status:** 🔴 **CRITICAL - OPEN**  
**Last Updated:** 2025-11-30  
**Next Review:** 2025-12-01 (12:00 UTC)
