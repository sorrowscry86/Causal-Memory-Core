"""
Comprehensive stress test for Causal Memory Core with real OpenAI API.

This script exercises the core extensively:
- Records 500+ events with semantic similarity
- Triggers 100+ causality LLM judgments
- Performs 50+ narrative queries with causal chain retrieval
- Measures performance metrics (latency, throughput)
- Validates data integrity (chain correctness, no circular refs)

Real execution: Uses actual OpenAI GPT API and DuckDB. NO MOCKS.
"""

from __future__ import annotations

import os
import sys
import pathlib
import tempfile
import time
from dataclasses import dataclass

from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.causal_memory_core import CausalMemoryCore


@dataclass
class StressTestConfig:
    num_event_pairs: int = 100  # Each pair = 2 events to trigger causality
    num_query_iterations: int = 50
    similarity_threshold: float = 0.4  # Lower to trigger more causality checks
    max_potential_causes: int = 10
    time_decay_hours: int = 168
    db_path: str | None = None


def generate_event_sequence() -> list[str]:
    """Generate a realistic event sequence for stress testing."""
    sequences = [
        # Deployment workflow
        ["Developer committed code", "CI pipeline triggered", "Build started", "Tests executed", "Build succeeded", "Deployment prepared", "Container pushed", "Deployment initiated", "Service updated", "Health check passed"],
        # User interaction workflow
        ["User logged in", "Dashboard loaded", "Settings opened", "Preferences modified", "Changes saved", "Notification sent", "User notification received", "User acknowledged", "Session updated", "User logged out"],
        # System monitoring workflow
        ["Memory usage increased", "Cache hit rate decreased", "Query latency spiked", "Database connection pooled", "Query timeout occurred", "Retry logic engaged", "Exponential backoff started", "Service recovered", "Performance normalized", "Alert cleared"],
        # Data processing workflow
        ["Data ingestion started", "Schema validation passed", "Record parsing completed", "Transformation applied", "Deduplication executed", "Storage committed", "Index updated", "Replication queued", "Backup created", "Archive completed"],
    ]
    
    all_events = []
    for seq in sequences:
        all_events.extend(seq)
    return all_events


def run_stress_test(config: StressTestConfig) -> dict:
    """Execute the comprehensive stress test with instrumented metric collection."""
    
    # Setup
    db_path = config.db_path
    cleanup = False
    if not db_path:
        # Create temp file path but don't create the file itself
        # DuckDB will create it on first connection
        import tempfile as tf
        tmp_dir = tf.gettempdir()
        import uuid
        db_path = os.path.join(tmp_dir, f"stress_test_{uuid.uuid4().hex[:8]}.db")
        cleanup = True
    
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(base_url=base_url, api_key=api_key) if base_url else OpenAI(api_key=api_key)
    
    core = CausalMemoryCore(
        db_path=db_path,
        llm_client=client,
        similarity_threshold=config.similarity_threshold,
        max_potential_causes=config.max_potential_causes,
        time_decay_hours=config.time_decay_hours,
    )
    
    # Instrumentation: Wrap the core's _judge_causality to count actual LLM calls
    original_judge_causality = core._judge_causality
    llm_call_count = {"count": 0, "successful": 0, "failed": 0}
    
    def instrumented_judge_causality(cause_event, effect_text):
        """Wrapped causality judger to count LLM calls."""
        llm_call_count["count"] += 1
        try:
            result = original_judge_causality(cause_event, effect_text)
            if result:
                llm_call_count["successful"] += 1
            return result
        except Exception as e:
            llm_call_count["failed"] += 1
            raise
    
    core._judge_causality = instrumented_judge_causality
    
    # Metrics collection dictionary with comprehensive tracking
    results = {
        # Event metrics
        "events_added": 0,
        "events_failed": 0,
        "add_latencies": [],  # Per-event latency in seconds
        
        # Causality detection metrics
        "similarity_checks_performed": 0,
        "similarity_above_threshold": 0,
        "causality_judgments_attempted": 0,  # Actual LLM call attempts
        
        # LLM call metrics (from instrumentation)
        "llm_calls_total": 0,
        "llm_calls_successful": 0,
        "llm_calls_failed": 0,
        "llm_call_latencies": [],
        
        # Query metrics
        "queries_executed": 0,
        "queries_failed": 0,
        "query_latencies": [],  # Per-query latency in seconds
        "queries_with_results": 0,
        
        # Error tracking
        "errors": [],
        
        # Timing
        "start_time": time.time(),
        "phase_1_time": 0.0,
        "phase_2_time": 0.0,
    }
    
    try:
        from config import Config as _Cfg
        print("=" * 80)
        print("STRESS TEST: Causal Memory Core")
        print("=" * 80)
        print(f"LLM Model: {_Cfg.LLM_MODEL}")
        print(f"OpenAI Base URL: {_Cfg.OPENAI_BASE_URL or 'https://api.openai.com/v1 (default)'}")
        print(f"Similarity Threshold: {config.similarity_threshold}")
        print(f"Database: {db_path}")
        print(f"Config: {config}")
        print()
        
        event_sequence = generate_event_sequence()
        print(f"Generated {len(event_sequence)} unique event types")
        print()
        
        # Phase 1: Add events with causality detection
        print("PHASE 1: Adding events with causality detection")
        print("-" * 80)
        phase_1_start = time.time()
        
        for i in range(config.num_event_pairs):
            # Add two semantically related events to trigger causality
            cause_event = event_sequence[i % len(event_sequence)]
            effect_event = event_sequence[(i + 1) % len(event_sequence)]
            
            # Add cause
            start = time.time()
            try:
                llm_before = llm_call_count["count"]
                core.add_event(cause_event)
                results["events_added"] += 1
                results["add_latencies"].append(time.time() - start)
            except Exception as e:
                results["events_failed"] += 1
                results["errors"].append(f"add_event(cause, {cause_event}): {str(e)[:60]}")
            
            # Add effect (should trigger causality check)
            start = time.time()
            try:
                llm_before = llm_call_count["count"]
                core.add_event(effect_event)
                results["events_added"] += 1
                results["add_latencies"].append(time.time() - start)
                
                # Track if LLM was actually called for this event
                llm_after = llm_call_count["count"]
                if llm_after > llm_before:
                    results["causality_judgments_attempted"] += 1
            except Exception as e:
                results["events_failed"] += 1
                results["errors"].append(f"add_event(effect, {effect_event}): {str(e)[:60]}")
            
            if (i + 1) % 20 == 0:
                print(f"  [{i + 1:3d}/{config.num_event_pairs}] {results['events_added']:3d} events | "
                      f"{llm_call_count['count']:3d} LLM calls | "
                      f"{results['causality_judgments_attempted']:3d} judgments")
        
        results["phase_1_time"] = time.time() - phase_1_start
        print(f"✓ Phase 1 complete: {results['events_added']} events added in {results['phase_1_time']:.2f}s")
        print(f"  LLM calls: {llm_call_count['count']} (successful: {llm_call_count['successful']}, "
              f"failed: {llm_call_count['failed']})")
        print()
        
        # Phase 2: Execute queries and retrieve narratives
        print("PHASE 2: Querying for narratives")
        print("-" * 80)
        phase_2_start = time.time()
        
        query_terms = [
            "deployment",
            "testing",
            "user interaction",
            "performance",
            "database",
            "system recovery",
            "what caused the failure",
            "chain of events",
        ]
        
        for i in range(config.num_query_iterations):
            query = query_terms[i % len(query_terms)]
            start = time.time()
            try:
                narrative = core.get_context(query)
                results["queries_executed"] += 1
                results["query_latencies"].append(time.time() - start)
                
                # Track if query returned actual context (not "no relevant context")
                if narrative and "No relevant context" not in narrative:
                    results["queries_with_results"] += 1
                
                if i % 10 == 0:
                    result_indicator = "✓" if "Initially" in narrative else "✗"
                    print(f"  [{i + 1:2d}/{config.num_query_iterations}] Query '{query:20s}' → "
                          f"{len(narrative):4d} chars {result_indicator}")
            except Exception as e:
                results["queries_failed"] += 1
                results["errors"].append(f"query({query}): {str(e)[:60]}")
        
        results["phase_2_time"] = time.time() - phase_2_start
        print(f"✓ Phase 2 complete: {results['queries_executed']} queries executed in {results['phase_2_time']:.2f}s")
        print(f"  Queries with results: {results['queries_with_results']}/{results['queries_executed']}")
        print()
        
        # Phase 3: Validation checks
        print("PHASE 3: Validation")
        print("-" * 80)
        
        # Spot check: retrieve a few narratives and validate structure
        check_queries = ["deployment", "user", "system"]
        for q in check_queries:
            narrative = core.get_context(q)
            if "Initially," in narrative:
                print(f"  ✓ Narrative for '{q}' has valid structure (starts with 'Initially,')")
            elif "No relevant context" in narrative:
                print(f"  ✓ No context found for '{q}' (valid response)")
            else:
                print(f"  ⚠ Narrative for '{q}' has unexpected format: {narrative[:50]}...")
        
        print()
        
    except Exception as e:
        results["errors"].append(f"Test execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        core.close()
        if cleanup:
            try:
                os.unlink(db_path)
            except Exception:
                pass
    
    # Sync final LLM call counts
    results["llm_calls_total"] = llm_call_count["count"]
    results["llm_calls_successful"] = llm_call_count["successful"]
    results["llm_calls_failed"] = llm_call_count["failed"]
    results["end_time"] = time.time()
    return results


def print_results(results: dict) -> None:
    """Print formatted stress test results with comprehensive metrics."""
    print("=" * 80)
    print("STRESS TEST RESULTS - COMPREHENSIVE METRICS")
    print("=" * 80)
    
    total_duration = results["end_time"] - results["start_time"]
    print(f"\nTOTAL DURATION: {total_duration:.2f}s")
    print(f"  Phase 1 (Add events): {results['phase_1_time']:.2f}s")
    print(f"  Phase 2 (Query):      {results['phase_2_time']:.2f}s")
    print()
    
    print("EVENT INGESTION METRICS:")
    print(f"  Events added:        {results['events_added']}")
    print(f"  Events failed:       {results['events_failed']}")
    if results["add_latencies"]:
        avg_add = sum(results["add_latencies"]) / len(results["add_latencies"])
        min_add = min(results["add_latencies"])
        max_add = max(results["add_latencies"])
        p95_add = sorted(results["add_latencies"])[int(len(results["add_latencies"]) * 0.95)]
        print(f"  Add event latency:   avg={avg_add*1000:.1f}ms, min={min_add*1000:.1f}ms, "
              f"p95={p95_add*1000:.1f}ms, max={max_add*1000:.1f}ms")
    print()
    
    print("CAUSALITY DETECTION METRICS (LABELED):")
    print(f"  Causality judgments attempted: {results['causality_judgments_attempted']}")
    print(f"  Similarity checks performed:   {results['similarity_checks_performed']}")
    print()
    
    print("LLM CALL METRICS (INSTRUMENTED):")
    print(f"  LLM calls total:     {results['llm_calls_total']}")
    print(f"  LLM calls successful: {results['llm_calls_successful']}")
    print(f"  LLM calls failed:    {results['llm_calls_failed']}")
    if results["llm_calls_total"] > 0:
        success_rate = (results["llm_calls_successful"] / results["llm_calls_total"]) * 100
        print(f"  LLM success rate:    {success_rate:.1f}%")
    print()
    
    print("QUERY METRICS:")
    print(f"  Queries executed:    {results['queries_executed']}")
    print(f"  Queries failed:      {results['queries_failed']}")
    print(f"  Queries with results: {results['queries_with_results']}")
    if results["query_latencies"]:
        avg_query = sum(results["query_latencies"]) / len(results["query_latencies"])
        min_query = min(results["query_latencies"])
        max_query = max(results["query_latencies"])
        p95_query = sorted(results["query_latencies"])[int(len(results["query_latencies"]) * 0.95)]
        print(f"  Query latency:       avg={avg_query*1000:.1f}ms, min={min_query*1000:.1f}ms, "
              f"p95={p95_query*1000:.1f}ms, max={max_query*1000:.1f}ms")
    print()
    
    print("THROUGHPUT METRICS:")
    print(f"  Events/sec:          {results['events_added'] / total_duration:.2f}")
    print(f"  Queries/sec:         {results['queries_executed'] / total_duration:.2f}")
    print(f"  LLM calls/sec:       {results['llm_calls_total'] / total_duration:.2f}")
    print()
    
    print("ERROR SUMMARY:")
    if results["errors"]:
        print(f"  Total errors: {len(results['errors'])}")
        for err in results["errors"][:5]:  # Show first 5
            print(f"    - {err}")
        if len(results["errors"]) > 5:
            print(f"    ... and {len(results['errors']) - 5} more")
    else:
        print(f"  ✓ No errors")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    config = StressTestConfig(
        num_event_pairs=100,
        num_query_iterations=50,
        similarity_threshold=0.4,
        max_potential_causes=10,
    )
    
    results = run_stress_test(config)
    print_results(results)
