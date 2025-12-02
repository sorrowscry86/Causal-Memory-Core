import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch
import numpy as np

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore, Event

class TestCausalMemoryCore(unittest.TestCase):
    """Test suite for the Causal Memory Core"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database path (don't create the file, let DuckDB create it)
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        os.unlink(self.temp_db_path)  # Remove the empty file, let DuckDB create it
        
        # Mock the LLM and embedding model
        self.mock_llm = Mock()
        self.mock_embedder = Mock()
        
        # Set up mock responses
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Initialize memory core with mocks
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
    def tearDown(self):
        """Clean up test fixtures"""
        self.memory_core.close()
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
    def test_database_initialization(self):
        """Test that the database is properly initialized"""
        # Check that events table exists (DuckDB syntax)
        result = self.memory_core.conn.execute("""
            SELECT table_name FROM duckdb_tables()
            WHERE table_name = 'events'
        """).fetchone()
        
        self.assertIsNotNone(result)
        
    def test_add_event_without_cause(self):
        """Test adding an event with no causal relationship"""
        # Mock LLM to return no causal relationship
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Add an event
        self.memory_core.add_event("The user opened a file")
        
        # Check that event was added
        result = self.memory_core.conn.execute("""
            SELECT effect_text, cause_id FROM events
        """).fetchone()
        
        self.assertEqual(result[0], "The user opened a file")
        self.assertIsNone(result[1])  # No cause_id
        
    def test_add_event_with_cause(self):
        """Test adding an event with a causal relationship"""
        # Add first event
        self.memory_core.add_event("The user clicked on a file")
        
        # Mock LLM to return a causal relationship for second event
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The click action caused the file to open"
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Mock embedder to return similar embeddings (high similarity)
        self.mock_embedder.encode.side_effect = [
            np.array([0.1, 0.2, 0.3, 0.4]),  # First event
            np.array([0.11, 0.21, 0.31, 0.41])  # Second event (similar)
        ]
        
        # Add second event
        self.memory_core.add_event("The file opened")
        
        # Check that both events exist and second has causal link
        events = self.memory_core.conn.execute("""
            SELECT event_id, effect_text, cause_id, relationship_text 
            FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][2], None)  # First event has no cause
        self.assertEqual(events[1][2], events[0][0])  # Second event caused by first
        self.assertIsNotNone(events[1][3])  # Has relationship text
        
    def test_get_context_no_events(self):
        """Test querying context when no events exist"""
        result = self.memory_core.get_context("test query")
        self.assertEqual(result, "No relevant context found in memory.")
        
    def test_get_context_single_event(self):
        """Test querying context with a single event"""
        # Add an event
        self.memory_core.add_event("The user opened a file")
        
        # Query for context
        result = self.memory_core.get_context("file opening")
        
        # Should return the single event narrative
        self.assertIn("Initially,", result)
        self.assertIn("The user opened a file", result)
        
    def test_get_context_causal_chain(self):
        """Test querying context that returns a causal chain"""
        # Reset the mock to ensure clean state
        self.mock_embedder.encode.reset_mock()
        
        # Mock embeddings for first event (similar to setup)
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Add first event
        self.memory_core.add_event("The user clicked on a file")
        
        # Mock LLM to return causal relationship
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The click caused the file to open"
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Mock similar embeddings for second event (high similarity to trigger causal detection)
        self.mock_embedder.encode.return_value = np.array([0.11, 0.21, 0.31, 0.41])
        
        # Add second event
        self.memory_core.add_event("The file opened")
        
        # Mock embedding for query (similar to second event to find it)
        self.mock_embedder.encode.return_value = np.array([0.11, 0.21, 0.31, 0.41])
        
        # Query for context
        result = self.memory_core.get_context("file opened")
        
        # Should return a narrative chain
        self.assertIn("Initially,", result)
        self.assertIn("This led to", result)
        
    def test_cosine_similarity_calculation(self):
        """Test that cosine similarity is calculated correctly"""
        # Create test embeddings
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0])
        embedding3 = np.array([1.0, 0.0, 0.0])
        
        # Calculate similarities manually
        sim_1_2 = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        sim_1_3 = np.dot(embedding1, embedding3) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding3))
        
        self.assertAlmostEqual(sim_1_2, 0.0)  # Orthogonal vectors
        self.assertAlmostEqual(sim_1_3, 1.0)  # Identical vectors
        
    def test_event_class(self):
        """Test the Event class"""
        event = Event(
            event_id=1,
            timestamp=datetime.now(),
            effect_text="Test event",
            embedding=[0.1, 0.2, 0.3],
            cause_id=None,
            relationship_text=None
        )
        
        self.assertEqual(event.event_id, 1)
        self.assertEqual(event.effect_text, "Test event")
        self.assertIsNone(event.cause_id)
        
    @patch('config.Config.SIMILARITY_THRESHOLD', 0.5)
    def test_similarity_threshold(self):
        """Test that similarity threshold is respected"""
        # Add first event
        self.memory_core.add_event("First event")
        
        # Mock embeddings with low similarity
        self.mock_embedder.encode.side_effect = [
            np.array([1.0, 0.0, 0.0, 0.0]),  # First event
            np.array([0.0, 0.0, 0.0, 1.0])   # Second event (low similarity)
        ]
        
        # Add second event - should not find causal relationship due to low similarity
        self.memory_core.add_event("Completely different event")
        
        # Check that second event has no cause
        events = self.memory_core.conn.execute("""
            SELECT cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertIsNone(events[0][0])  # First event
        self.assertIsNone(events[1][0])  # Second event (no cause due to low similarity)

    # Additional tests for query() method
    def test_query_valid_single_event(self):
        """Query with single event returns that event."""
        # Setup similar to test_get_context_single_event
        self.memory_core.add_event("Test event")
        # Mock finding the event
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])

        result = self.memory_core.query("test")
        assert isinstance(result, str)
        assert "Test event" in result

    def test_query_empty_string_raises_error(self):
        """Query with empty string raises ValueError."""
        with self.assertRaises(ValueError):
            self.memory_core.query("")

    def test_query_whitespace_only_raises_error(self):
        """Query with whitespace-only string raises ValueError."""
        with self.assertRaises(ValueError):
            self.memory_core.query("   ")

    def test_query_with_causal_chain_returns_full_narrative(self):
        """Query with related events returns complete chain."""
        # Reset mock
        self.mock_embedder.encode.reset_mock()

        # Setup causal chain
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        self.memory_core.add_event("Root cause occurred")

        # Mock causal relationship
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Root cause led to secondary effect"
        self.mock_llm.chat.completions.create.return_value = mock_response

        self.mock_embedder.encode.return_value = np.array([0.11, 0.21, 0.31, 0.41])
        self.memory_core.add_event("This triggered secondary effect")

        # Mock query embedding finding the second event
        self.mock_embedder.encode.return_value = np.array([0.11, 0.21, 0.31, 0.41])

        result = self.memory_core.query("root cause")
        assert "Root cause occurred" in result
        assert "This triggered secondary effect" in result

    def test_query_no_relevant_context_returns_default_message(self):
        """Query with no matching events returns default message."""
        # Add unrelated event
        self.memory_core.add_event("Unrelated event")

        # Patch _find_most_relevant_event for this test to be sure
        with patch.object(self.memory_core, '_find_most_relevant_event', return_value=None):
            result = self.memory_core.query("completely unrelated query xyz123")
            assert "No relevant context" in result

    def test_query_uses_embedding_cache(self):
        """Query uses embedding cache (verify cache hit)."""
        self.memory_core.add_event("Test event")

        # Mock embedding
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])

        # First query
        result1 = self.memory_core.query("test")

        # Check cache is populated
        assert len(self.memory_core._embedding_cache) > 0
        assert "test" in self.memory_core._embedding_cache

        # Count calls to embedder.encode
        initial_call_count = self.mock_embedder.encode.call_count

        # Second identical query should hit cache
        result2 = self.memory_core.query("test")

        # Results should be identical
        assert result1 == result2

        # Should not increase call count if cached
        assert self.mock_embedder.encode.call_count == initial_call_count

    # Test get_context() method explicit delegation
    def test_get_context_delegates_to_query(self):
        """get_context() returns same result as query()."""
        self.memory_core.add_event("Test event")

        # Mock embedding
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])

        query_result = self.memory_core.query("test")
        context_result = self.memory_core.get_context("test")
        assert query_result == context_result

    def test_get_context_empty_string_raises_error(self):
        """get_context() with empty string raises ValueError."""
        with self.assertRaises(ValueError):
            self.memory_core.get_context("")

if __name__ == '__main__':
    unittest.main()
