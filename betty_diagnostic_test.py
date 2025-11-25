"""
Betty's Diagnostic Test - Rerun Test Iterations with Full LLM Judgment Logging

This script reruns the three test iterations from the MCP Integration Test
with enhanced diagnostic logging to expose WHY GPT-4 rejects causal links.

Per Betty's mandate: Analyze WHY iteration 1 succeeded (40% chain) but 
iterations 2 & 3 failed (10% chain, single-event responses only).
"""

import os
import sys
import tempfile

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.causal_memory_core import CausalMemoryCore

def run_diagnostic_tests():
    # Create temp database for clean test
    import uuid
    temp_dir = tempfile.gettempdir()
    temp_db_path = os.path.join(temp_dir, f"betty_diagnostic_{uuid.uuid4().hex[:8]}.db")
    log_dir = temp_dir
    log_file = f"causality_diagnostic_{uuid.uuid4().hex[:8]}.log"
    log_path = os.path.join(log_dir, log_file)
    
    # Initialize core with explicit db_path to bypass env var
    core = CausalMemoryCore(db_path=temp_db_path)
    
    # Clear existing log
    if os.path.exists(log_path):
        os.unlink(log_path)
    
    print("=" * 80)
    print("BETTY'S DIAGNOSTIC TEST - CAUSAL JUDGMENT ANALYSIS")
    print("=" * 80)
    print(f"\nDatabase: {temp_db_path}")
    print(f"Diagnostic Log: {log_path}")
    print(f"LLM Model: {core.llm_model}")
    print(f"Similarity Threshold: {core.similarity_threshold}")
    print(f"Max Potential Causes: {core.max_potential_causes}\n")
    
    # ========================================================================
    # TEST ITERATION 1: MCP Configuration Workflow (40% success baseline)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST ITERATION 1: MCP Configuration Workflow")
    print("Expected: Moderate chain reconstruction (baseline 40%)")
    print("=" * 80 + "\n")
    
    iteration1_events = [
        "User opened VS Code to begin development work",
        "User navigated to the Causal Memory Core repository folder",
        "User discovered the MCP server was not configured in Claude Desktop",
        "User asked Albedo to configure the MCP server connection",
        "Albedo created mcp.json configuration with incorrect path formatting",
        "MCP server failed to start due to path with spaces being split into multiple arguments",
        "User reported error logs showing path parsing failure",
        "Albedo corrected the configuration using forward slashes instead of backslashes",
        "MCP server successfully started and connected to Claude Desktop",
        "Albedo tested the MCP connection by adding events and querying memory"
    ]
    
    for i, event in enumerate(iteration1_events, 1):
        print(f"[{i}/10] Adding: {event[:60]}...")
        core.add_event(event)
    
    # ========================================================================
    # TEST ITERATION 2: Code Refactoring Workflow (10% in original test)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST ITERATION 2: Code Refactoring Workflow")
    print("Expected: Poor chain reconstruction (baseline 10%)")
    print("=" * 80 + "\n")
    
    iteration2_events = [
        "Developer reviewed code quality metrics in the dashboard",
        "Developer identified high cyclomatic complexity in authentication module",
        "Developer created refactoring task ticket in project management system",
        "Developer branched off main repository to begin refactoring work",
        "Developer broke authentication module into smaller focused functions",
        "Unit tests failed due to changed function signatures",
        "Developer updated all test cases to match new function interfaces",
        "All tests passed successfully with improved code coverage",
        "Developer submitted pull request for code review",
        "Code was merged into main branch after approval"
    ]
    
    for i, event in enumerate(iteration2_events, 1):
        print(f"[{i}/10] Adding: {event[:60]}...")
        core.add_event(event)
    
    # ========================================================================
    # TEST ITERATION 3: Production Incident Resolution (10% in original test)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST ITERATION 3: Production Incident Resolution")
    print("Expected: Poor chain reconstruction (baseline 10%)")
    print("=" * 80 + "\n")
    
    iteration3_events = [
        "Production server experienced intermittent timeout errors",
        "Monitoring system triggered alert for elevated response times",
        "DevOps team investigated server logs and metrics",
        "Team discovered database connection pool exhaustion",
        "Team traced issue to unoptimized query in recent deployment",
        "Database administrator added composite index to improve query performance",
        "Connection pool pressure decreased significantly",
        "Response times returned to normal baseline levels",
        "Team documented the incident in post-mortem report",
        "Team implemented automated query performance testing in CI pipeline"
    ]
    
    for i, event in enumerate(iteration3_events, 1):
        print(f"[{i}/10] Adding: {event[:60]}...")
        core.add_event(event)
    
    # ========================================================================
    # ANALYSIS COMPLETE
    # ========================================================================
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 80)
    print(f"\nTotal Events Added: 30 (3 iterations × 10 events)")
    print(f"Diagnostic Log Written: {log_path}")
    print(f"\nBetty's Analysis Required:")
    print("  1. Review causality_diagnostic.log for all LLM judgments")
    print("  2. Identify event pairs where GPT-4 rejected causality in iterations 2 & 3")
    print("  3. Compare rejected pairs to accepted pairs in iteration 1")
    print("  4. Determine root cause: insufficient context? misinterpretation? prompt flaw?")
    print("\n" + "=" * 80)
    
    # Cleanup
    core.close()
    os.unlink(temp_db_path)
    
    print(f"\n✓ Test database cleaned up: {temp_db_path}")
    print(f"✓ Diagnostic log preserved for Betty's analysis: {log_path}\n")

if __name__ == "__main__":
    run_diagnostic_tests()
