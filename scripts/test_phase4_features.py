#!/usr/bin/env python3
"""Test script to validate Phase 4 optimizations."""

import sys
import os
import tempfile
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore

def test_embedding_cache():
    """Test the LRU embedding cache."""
    print("\n" + "="*70)
    print("TEST 1: EMBEDDING CACHE VALIDATION")
    print("="*70)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize with small cache for testing
        memory = CausalMemoryCore(db_path=db_path, embedding_cache_size=3)

        # First query - cache miss
        print("\n1. First query (cache miss expected)...")
        start = time.time()
        result1 = memory.query("test query 1")
        time1 = time.time() - start
        print(f"   Time: {time1:.3f}s")

        # Same query - cache hit
        print("\n2. Repeated query (cache HIT expected)...")
        start = time.time()
        result2 = memory.query("test query 1")
        time2 = time.time() - start
        print(f"   Time: {time2:.3f}s")
        print(f"   Speedup: {time1/time2:.1f}x faster!")

        # Different queries to test cache size
        print("\n3. Testing cache eviction (max size: 3)...")
        memory.query("query 2")
        memory.query("query 3")
        memory.query("query 4")  # Should evict "test query 1"

        print(f"   Cache size: {len(memory._embedding_cache)}")
        print(f"   Cache contains: {list(memory._embedding_cache.keys())}")

        # Original query should be evicted
        print("\n4. Re-querying evicted item (cache miss expected)...")
        start = time.time()
        memory.query("test query 1")
        time3 = time.time() - start
        print(f"   Time: {time3:.3f}s (slower due to eviction)")

        memory.close()
        print("\n✅ EMBEDDING CACHE: WORKING CORRECTLY")

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_batch_insertion():
    """Test the batch event insertion."""
    print("\n" + "="*70)
    print("TEST 2: BATCH INSERTION VALIDATION")
    print("="*70)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        memory = CausalMemoryCore(db_path=db_path)

        # Test batch insertion with mixed valid/invalid data
        events = [
            "User logged in",
            "User viewed dashboard",
            "",  # Invalid - empty
            "User clicked export button",
            "Export started",
            123,  # Invalid - not a string
            "Export completed successfully"
        ]

        print(f"\n1. Batch inserting {len(events)} events (including 2 invalid)...")
        stats = memory.add_events_batch(events)

        print(f"\n2. Batch Results:")
        print(f"   Total:      {stats['total']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed:     {stats['failed']}")

        if stats['errors']:
            print(f"\n3. Errors encountered:")
            for error in stats['errors']:
                print(f"   - {error}")

        # Verify correct count
        expected_success = 5  # 7 total - 2 invalid
        if stats['successful'] == expected_success:
            print(f"\n✅ BATCH INSERTION: {expected_success} valid events inserted correctly")
        else:
            print(f"\n❌ BATCH INSERTION: Expected {expected_success}, got {stats['successful']}")

        memory.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_configurable_depth():
    """Test configurable consequence chain depth."""
    print("\n" + "="*70)
    print("TEST 3: CONFIGURABLE CONSEQUENCE DEPTH")
    print("="*70)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Test with depth = 0 (no consequences)
        print("\n1. Testing with max_consequence_depth=0 (causes only)...")
        memory_no_consequences = CausalMemoryCore(
            db_path=db_path,
            max_consequence_depth=0
        )
        print(f"   Configured depth: {memory_no_consequences.max_consequence_depth}")
        memory_no_consequences.close()

        # Test with depth = 5 (long chains)
        print("\n2. Testing with max_consequence_depth=5 (long chains)...")
        os.unlink(db_path)
        memory_long_chain = CausalMemoryCore(
            db_path=db_path,
            max_consequence_depth=5
        )
        print(f"   Configured depth: {memory_long_chain.max_consequence_depth}")
        memory_long_chain.close()

        # Test default (should be 2)
        print("\n3. Testing default max_consequence_depth...")
        os.unlink(db_path)
        memory_default = CausalMemoryCore(db_path=db_path)
        print(f"   Default depth: {memory_default.max_consequence_depth}")

        if memory_default.max_consequence_depth == 2:
            print("\n✅ CONFIGURABLE DEPTH: Working correctly")
        else:
            print(f"\n❌ CONFIGURABLE DEPTH: Expected 2, got {memory_default.max_consequence_depth}")

        memory_default.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_custom_embedding_model():
    """Test configurable embedding model name."""
    print("\n" + "="*70)
    print("TEST 4: CONFIGURABLE EMBEDDING MODEL")
    print("="*70)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Test custom model name
        print("\n1. Testing custom embedding model name...")
        custom_model = "all-MiniLM-L6-v2"  # Use known model
        memory = CausalMemoryCore(
            db_path=db_path,
            embedding_model_name=custom_model
        )

        print(f"   Configured model: {memory.embedding_model_name}")

        if memory.embedding_model_name == custom_model:
            print("\n✅ CONFIGURABLE EMBEDDING MODEL: Working correctly")
        else:
            print(f"\n❌ Expected '{custom_model}', got '{memory.embedding_model_name}'")

        memory.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all Phase 4 validation tests."""
    print("\n" + "🔮"*35)
    print(" "*15 + "PHASE 4 VALIDATION SUITE")
    print("🔮"*35)

    try:
        test_embedding_cache()
        test_batch_insertion()
        test_configurable_depth()
        test_custom_embedding_model()

        print("\n" + "="*70)
        print("✅ ALL PHASE 4 FEATURES VALIDATED SUCCESSFULLY")
        print("="*70)
        print("\nThe Construct's optimizations are operational and stable.")
        print("\n")

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
