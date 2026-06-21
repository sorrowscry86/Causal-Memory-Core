"""
Pytest configuration for the Causal Memory Core test suite.
"""
import os

# test_basic_functionality.py is a standalone script (not pytest tests).
# It calls sys.exit(1) at module level, which causes pytest to crash with
# INTERNALERROR on import. Exclude it from collection.
collect_ignore = [
    os.path.join(os.path.dirname(__file__), "test_basic_functionality.py")
]
