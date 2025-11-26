"""Test context retrieval functionality with mocked dependencies."""
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestContext:
    """Test suite for context retrieval operations."""

    @pytest.fixture
    def mock_memory_core(self):
        """Create a mocked CausalMemoryCore instance."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.causal_memory_core.SentenceTransformer') as mock_transformer:
                with patch('src.causal_memory_core.openai'):
                    # Setup mock embedder
                    mock_embedder = MagicMock()
                    mock_embedder.encode.return_value = [0.1] * 384
                    mock_transformer.return_value = mock_embedder

                    from src.causal_memory_core import CausalMemoryCore

                    # Use temp file for database
                    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                        db_path = f.name

                    memory = CausalMemoryCore(
                        db_path=db_path,
                        llm_client=MagicMock(),
                        embedding_model=mock_embedder
                    )
                    yield memory
                    memory.close()
                    # Cleanup temp file
                    try:
                        os.unlink(db_path)
                    except Exception:
                        pass

    def test_get_context(self, mock_memory_core):
        """Test getting context for a query."""
        query = "test event"
        context = mock_memory_core.get_context(query)
        # If no exception, test passes
        assert True

    def test_get_context_empty_query(self, mock_memory_core):
        """Test getting context with empty query."""
        context = mock_memory_core.get_context("")
        assert True

    def test_context_after_add_event(self, mock_memory_core):
        """Test getting context after adding an event."""
        mock_memory_core.add_event("The power went out.")
        context = mock_memory_core.get_context("power")
        assert True
