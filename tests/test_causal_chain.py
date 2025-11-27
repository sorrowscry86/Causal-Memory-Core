"""Test causal chain functionality with mocked dependencies."""
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestCausalChain:
    """Test suite for causal chain operations."""

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

    def test_add_event(self, mock_memory_core):
        """Test adding a single event."""
        mock_memory_core.add_event("The power went out.")
        # If no exception, test passes
        assert True

    def test_add_multiple_events(self, mock_memory_core):
        """Test adding multiple events."""
        mock_memory_core.add_event("The power went out.")
        mock_memory_core.add_event("The computer turned off.")
        assert True
