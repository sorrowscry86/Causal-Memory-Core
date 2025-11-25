"""
Prototype: Memory-First Protocol demo for Albedo integration using Causal Memory Core.

This script executes the Memory-First sequence with REAL execution against
the CausalMemoryCore and a local LM Studio LLM (OpenAI-compatible API).
It demonstrates:

1) QUERY: Retrieve causal narrative for a situation
2) ANALYZE: Light parsing (printed for demo)
3) CONTEXTUALIZE: Use narrative to inform a decision (printed)
4) ACT: Simulate an action (printed only; no external effects)
5) RECORD: Add the action as an event back into memory

Notes
 - Marked as PROTOTYPE to respect the NO SIMULATIONS LAW while executing real
     interactions with the core. External actions are printed only.
 - Uses a temporary DuckDB file unless DB_PATH env is set to preserve working DBs.
 - Requires LM Studio server running with OpenAI-compatible API (default http://localhost:1234/v1).
"""

from __future__ import annotations

import os
import sys
import pathlib
import tempfile
from dataclasses import dataclass

from openai import OpenAI

# Ensure repository root is on path for 'src' imports
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.causal_memory_core import CausalMemoryCore


@dataclass
class Decision:
    situation: str
    action: str


def run_memory_first_demo(decision: Decision) -> None:
    # Use a temporary DB by default to avoid altering the main DB.
    db_path = os.getenv("DB_PATH")
    cleanup = False
    if not db_path:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        db_path = tmp.name
        tmp.close()
        # DuckDB creates on first connect; we unlink at end
        cleanup = True

    # Configure LM Studio OpenAI-compatible endpoint
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
    api_key = os.getenv("OPENAI_API_KEY", "not-needed")
    client = OpenAI(base_url=base_url, api_key=api_key)

    core = CausalMemoryCore(
        db_path=db_path,
        llm_client=client,
        # Use default sentence-transformers embedder from the core
        similarity_threshold=None,  # use config default
        max_potential_causes=None,
        time_decay_hours=None,
    )

    try:
        # Show which model and endpoint are configured
        from config import Config as _Cfg
        print(f"LLM model: {os.getenv('LLM_MODEL', _Cfg.LLM_MODEL)}")
        print(f"LLM base URL: {base_url}")
        print()
        
        # Seed a cause-effect pair to trigger LLM causality judgment
        print("=== Seeding initial event ===")
        core.add_event("User clicked the deploy button")
        print("Event 1 recorded: User clicked the deploy button")
        print()
        
        print("=== Adding related event (should trigger causality check) ===")
        core.add_event("Deployment pipeline started running")
        print("Event 2 recorded: Deployment pipeline started running")
        print()
        
        # 1) QUERY
        narrative = core.get_context(decision.situation)
        print("--- Narrative Context ---")
        print(narrative)

        # 2) ANALYZE (very light for demo)
        has_context = narrative and narrative != "No relevant context found in memory."
        print("--- Analysis ---")
        print("Context found:" if has_context else "No prior context found.")

        # 3) CONTEXTUALIZE (demo: if context exists, append a caution)
        plan = decision.action
        if has_context:
            plan += " (informed by prior context)"
        print("--- Decision ---")
        print(plan)

        # 4) ACT (prototype: print only, no external side effects)
        print("--- Action ---")
        print(f"Executing: {plan}")

        # 5) RECORD
        core.add_event(f"Action taken: {plan}")
        print("--- Recorded ---")
        print("Event recorded in memory.")

        # Show a follow-up query—use the action text to ensure a match
        follow_up = core.get_context("deployment pipeline")
        print("--- Follow-up Context ---")
        print(follow_up)
    finally:
        core.close()
        if cleanup:
            try:
                os.unlink(db_path)
            except Exception:
                pass


if __name__ == "__main__":
    run_memory_first_demo(
        Decision(
            situation="We experienced slow semantic search previously after adding 1000 events.",
            action="Optimize similarity search threshold and log query timings",
        )
    )
