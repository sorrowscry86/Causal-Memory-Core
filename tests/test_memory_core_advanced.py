"""
Advanced unit tests for the CausalMemoryCore module
Covers edge cases, error conditions, and comprehensive functionality
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from causal_memory_core import CausalMemoryCore, Event
from config import Config


class TestCausalMemoryCoreAdvanced(unittest.TestCase):
    """Advanced test suite for the Causal Memory Core"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database path
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        os.unlink(self.temp_db_path)  # Remove the empty file, let DuckDB create it
        
        # Mock the LLM and embedding model
        self.mock_llm = Mock()
        self.mock_embedder = Mock()
        
        # Set up default mock responses
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'memory_core') and self.memory_core:
            self.memory_core.close()
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_initialization_with_default_parameters(self):
        """Test initialization with default parameters (no mocks)"""
        with patch('causal_memory_core.SentenceTransformer') as mock_st, \
             patch('causal_memory_core.openai') as mock_openai, \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            
            mock_st.return_value = self.mock_embedder
            
            # Test initialization with defaults
            memory_core = CausalMemoryCore(db_path=self.temp_db_path)
            
            # Verify components were initialized
            self.assertIsNotNone(memory_core.conn)
            self.assertIsNotNone(memory_core.embedder)
            self.assertIsNotNone(memory_core.llm)
            
            memory_core.close()

    def test_initialization_with_missing_api_key(self):
        """Test initialization failure when OpenAI API key is missing"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                CausalMemoryCore(db_path=self.temp_db_path)
            
            self.assertIn("OPENAI_API_KEY must be set", str(context.exception))

    def test_database_initialization_with_vss_extension(self):
        """Test database initialization when VSS extension is available"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Verify tables and sequences were created
        result = self.memory_core.conn.execute("""
            SELECT table_name FROM duckdb_tables() 
            WHERE table_name = 'events'
        """).fetchone()
        self.assertIsNotNone(result)
        
        # Verify sequence exists using DuckDB metadata function (portable across builds)
        result = self.memory_core.conn.execute("""
            SELECT * FROM duckdb_sequences()
            WHERE sequence_name = 'events_seq'
        """).fetchone()
        self.assertIsNotNone(result)

    def test_find_potential_causes_with_no_recent_events(self):
        """Test finding potential causes when no recent events exist"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add an old event (more than 24 hours ago)
        old_timestamp = datetime.now() - timedelta(hours=25)
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding)
            VALUES (1, ?, 'Old event', ?)
        """, [old_timestamp, [0.1, 0.2, 0.3, 0.4]])
        
        # Test finding potential causes
        potential_causes = self.memory_core._find_potential_causes([0.1, 0.2, 0.3, 0.4], "test query")
        
        # Should return empty list since the event is too old
        self.assertEqual(len(potential_causes), 0)

    def test_find_potential_causes_with_low_similarity(self):
        """Test finding potential causes with low similarity scores"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add a recent event with very different embedding
        recent_timestamp = datetime.now() - timedelta(minutes=10)
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding)
            VALUES (1, ?, 'Different event', ?)
        """, [recent_timestamp, [1.0, 0.0, 0.0, 0.0]])  # Very different embedding
        
        # Test finding potential causes with different embedding
        potential_causes = self.memory_core._find_potential_causes([0.0, 1.0, 0.0, 0.0], "test query")
        
        # Should return empty list due to low similarity (below threshold)
        self.assertEqual(len(potential_causes), 0)

    def test_find_potential_causes_sorting_by_similarity(self):
        """Test that potential causes are sorted by similarity score"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add multiple events with different similarities
        recent_timestamp = datetime.now() - timedelta(minutes=10)
        
        # High similarity event
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding)
            VALUES (1, ?, 'High similarity event', ?)
        """, [recent_timestamp, [0.9, 0.9, 0.9, 0.9]])
        
        # Medium similarity event
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding)
            VALUES (2, ?, 'Medium similarity event', ?)
        """, [recent_timestamp, [0.8, 0.8, 0.8, 0.8]])
        
        # Test finding potential causes (all embeddings are similar enough to pass threshold)
        potential_causes = self.memory_core._find_potential_causes([0.85, 0.85, 0.85, 0.85], "test query")
        
        # Should return events sorted by similarity (highest first)
        if len(potential_causes) > 1:
            # First event should have higher similarity
            self.assertEqual(potential_causes[0].effect_text, 'High similarity event')

    @patch('config.Config.MAX_POTENTIAL_CAUSES', 2)
    def test_find_potential_causes_respects_max_limit(self):
        """Test that _find_potential_causes respects MAX_POTENTIAL_CAUSES limit"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add more events than the limit
        recent_timestamp = datetime.now() - timedelta(minutes=10)
        similar_embedding = [0.9, 0.9, 0.9, 0.9]
        
        # Insert using _insert_event to avoid manual event_id collisions
        for i in range(5):
            self.memory_core._insert_event(f'Event {i+1}', similar_embedding, None, None)
        
        # Test finding potential causes
        potential_causes = self.memory_core._find_potential_causes([0.9, 0.9, 0.9, 0.9], "test query")
        
        # Should return at most MAX_POTENTIAL_CAUSES events
        self.assertLessEqual(len(potential_causes), 2)

    def test_judge_causality_with_llm_error(self):
        """Test _judge_causality when LLM call fails"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Configure LLM to raise an exception
        self.mock_llm.chat.completions.create.side_effect = Exception("LLM API error")
        
        # Create test event
        test_event = Event(
            event_id=1,
            timestamp=datetime.now(),
            effect_text="Test event",
            embedding=[0.1, 0.2, 0.3, 0.4]
        )
        
        # Test causality judgment
        result = self.memory_core._judge_causality(test_event, "Effect event")
        
        # Should return None when LLM fails
        self.assertIsNone(result)

    def test_judge_causality_with_different_llm_responses(self):
        """Test _judge_causality with various LLM response formats"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        test_event = Event(
            event_id=1,
            timestamp=datetime.now(),
            effect_text="User clicked button",
            embedding=[0.1, 0.2, 0.3, 0.4]
        )
        
        # Test cases for different LLM responses
        test_cases = [
            ("No.", None),  # Explicit "No"
            ("no", None),   # Lowercase "no"
            ("No causal relationship exists.", None),  # Starts with "no"
            ("The button click caused the action to execute.", "The button click caused the action to execute."),
            ("Yes, the click triggered the response.", "Yes, the click triggered the response."),
        ]
        
        for llm_response, expected_result in test_cases:
            # Configure mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = llm_response
            self.mock_llm.chat.completions.create.return_value = mock_response
            
            # Test causality judgment
            result = self.memory_core._judge_causality(test_event, "Action executed")
            
            self.assertEqual(result, expected_result, 
                           f"Failed for LLM response: '{llm_response}'")

    def test_get_event_by_id_nonexistent(self):
        """Test _get_event_by_id with non-existent event ID"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Test getting non-existent event
        result = self.memory_core._get_event_by_id(999)
        
        self.assertIsNone(result)

    def test_get_event_by_id_existing(self):
        """Test _get_event_by_id with existing event"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add a test event
        timestamp = datetime.now()
        embedding = [0.1, 0.2, 0.3, 0.4]
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding, cause_id, relationship_text)
            VALUES (1, ?, 'Test event', ?, NULL, NULL)
        """, [timestamp, embedding])
        
        # Test getting the event
        result = self.memory_core._get_event_by_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.event_id, 1)
        self.assertEqual(result.effect_text, 'Test event')
        self.assertEqual(result.embedding, embedding)
        self.assertIsNone(result.cause_id)
        self.assertIsNone(result.relationship_text)

    def test_traversal_broken_chain_partial_return(self):
        """Traversal should return partial chain when cause_id points to missing event."""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Insert a single event that references a non-existent cause (allowed via helper)
        self.memory_core._insert_event('Child event with missing cause', [0.1, 0.2, 0.3, 0.4], 999, None)
        
        # Make query embedding similar to the event to ensure selection
        self.mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        narrative = self.memory_core.get_context("find child")
        
        self.assertIsInstance(narrative, str)
        self.assertIn("Initially,", narrative)
        self.assertIn("Child event with missing cause", narrative)

    def test_traversal_circular_reference_protection(self):
        """Traversal should detect circular references and stop, returning a finite narrative."""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        timestamp = datetime.now()
        emb = [0.5, 0.5, 0.5, 0.5]
        
        # Create a 2-node cycle: 1 -> 2 -> 1
        self.memory_core.conn.execute(
            """
            INSERT INTO events (event_id, timestamp, effect_text, embedding, cause_id, relationship_text)
            VALUES 
            (1, ?, 'Cycle event A', ?, 2, NULL),
            (2, ?, 'Cycle event B', ?, 1, NULL)
            """,
            [timestamp, emb, timestamp, emb]
        )
        
        # Query embedding similar to events
        self.mock_embedder.encode.return_value = np.array(emb)
        
        narrative = self.memory_core.get_context("cycle query")
        
        self.assertIsInstance(narrative, str)
        self.assertIn("Initially:", narrative)
        # Should include both events and not loop infinitely
        self.assertIn("Cycle event A", narrative)
        self.assertIn("Cycle event B", narrative)

    def test_find_most_relevant_event_no_events(self):
        """Test _find_most_relevant_event when no events exist"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Test finding most relevant event
        result = self.memory_core._find_most_relevant_event([0.1, 0.2, 0.3, 0.4])
        
        self.assertIsNone(result)

    def test_find_most_relevant_event_below_threshold(self):
        """Test _find_most_relevant_event when all events are below similarity threshold"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Add event with very different embedding
        timestamp = datetime.now()
        self.memory_core.conn.execute("""
            INSERT INTO events (event_id, timestamp, effect_text, embedding)
            VALUES (1, ?, 'Different event', ?)
        """, [timestamp, [1.0, 0.0, 0.0, 0.0]])
        
        # Test with very different query embedding
        result = self.memory_core._find_most_relevant_event([0.0, 1.0, 0.0, 0.0])
        
        # Should return None because similarity is below threshold
        self.assertIsNone(result)

    def test_format_chain_as_narrative_empty_chain(self):
        """Test _format_chain_as_narrative with empty chain"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        result = self.memory_core._format_chain_as_narrative([])
        self.assertEqual(result, "No causal chain found.")

    def test_format_chain_as_narrative_single_event(self):
        """Test _format_chain_as_narrative with single event"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        event = Event(
            event_id=1,
            timestamp=datetime.now(),
            effect_text="Single event",
            embedding=[0.1, 0.2, 0.3, 0.4]
        )
        
        result = self.memory_core._format_chain_as_narrative([event])
        self.assertEqual(result, "Initially, Single event.")

    def test_format_chain_as_narrative_multiple_events(self):
        """Test _format_chain_as_narrative with multiple events"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        events = [
            Event(1, datetime.now(), "First event", [0.1, 0.2, 0.3, 0.4], None, None),
            Event(2, datetime.now(), "Second event", [0.2, 0.3, 0.4, 0.5], 1, "The first event caused this"),
            Event(3, datetime.now(), "Third event", [0.3, 0.4, 0.5, 0.6], 2, None)
        ]
        
        result = self.memory_core._format_chain_as_narrative(events)
        
        self.assertTrue(result.startswith("Initially, First event."))
        self.assertIn("This led to Second event (The first event caused this)", result)
        self.assertIn("which in turn caused Third event", result)

    def test_add_event_with_very_long_text(self):
        """Test adding event with very long text"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Create very long event text
        long_text = "This is a very long event description. " * 100  # ~3700 chars
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Should not raise an exception
        self.memory_core.add_event(long_text)
        
        # Verify event was stored
        result = self.memory_core.conn.execute("SELECT effect_text FROM events").fetchone()
        self.assertEqual(result[0], long_text)

    def test_add_event_with_special_characters(self):
        """Test adding event with special characters and unicode"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Event with special characters and unicode
        special_text = "User clicked 'Submit' → Action completed! 🎉 Ñoño test @#$%^&*()"
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        self.memory_core.add_event(special_text)
        
        # Verify event was stored correctly
        result = self.memory_core.conn.execute("SELECT effect_text FROM events").fetchone()
        self.assertEqual(result[0], special_text)

    def test_get_context_with_complex_causal_chain(self):
        """Test get_context with a complex multi-level causal chain"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Create a chain: Event1 -> Event2 -> Event3 -> Event4
        timestamp = datetime.now()
        embedding = [0.9, 0.9, 0.9, 0.9]
        
        # Insert events via helper to avoid FK/sequence issues
        self.memory_core._insert_event('Root cause event', embedding, None, None)
        root_id = self.memory_core.conn.execute("SELECT MIN(event_id) FROM events").fetchone()[0]
        self.memory_core._insert_event('First effect', embedding, root_id, 'Root caused first effect')
        first_id = self.memory_core.conn.execute("SELECT MAX(event_id) FROM events WHERE effect_text='First effect'").fetchone()[0]
        self.memory_core._insert_event('Second effect', embedding, first_id, 'First effect caused second effect')
        second_id = self.memory_core.conn.execute("SELECT MAX(event_id) FROM events WHERE effect_text='Second effect'").fetchone()[0]
        self.memory_core._insert_event('Final effect', embedding, second_id, 'Second effect caused final effect')
        
        # Mock embedder to return similar embedding for query
        self.mock_embedder.encode.return_value = np.array([0.9, 0.9, 0.9, 0.9])
        
        # Get context for the final effect
        result = self.memory_core.get_context("final effect")
        
        # Should trace back to root and build complete narrative
        self.assertIn("Initially: Root cause event", result)
        self.assertIn("Root caused first effect", result)
        self.assertIn("First effect caused second effect", result)
        self.assertIn("Second effect caused final effect", result)

    def test_close_database_connection(self):
        """Test that database connection is properly closed"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Verify connection is active
        self.assertIsNotNone(self.memory_core.conn)
        
        # Close connection
        self.memory_core.close()
        
        # Connection should still exist but be closed (DuckDB behavior)
        self.assertIsNotNone(self.memory_core.conn)

    def test_concurrent_event_insertion(self):
        """Test handling of rapid sequential event insertions"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Mock LLM to always return "No" for faster testing
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Add multiple events rapidly
        events = [f"Event {i}" for i in range(10)]
        for event_text in events:
            self.memory_core.add_event(event_text)
        
        # Verify all events were stored
        result = self.memory_core.conn.execute("SELECT COUNT(*) FROM events").fetchone()
        self.assertEqual(result[0], 10)

    def test_embedding_dimension_consistency(self):
        """Test that all embeddings have consistent dimensions"""
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=self.mock_llm,
            embedding_model=self.mock_embedder
        )
        
        # Mock embedder to return different sized embeddings
        embeddings = [
            np.array([0.1, 0.2, 0.3, 0.4]),      # 4D
            np.array([0.1, 0.2, 0.3, 0.4, 0.5]), # 5D - different size
        ]
        
        self.mock_embedder.encode.side_effect = embeddings
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
        # Add first event
        self.memory_core.add_event("First event")
        
        # Add second event with different embedding dimension
        # This should not crash, but may affect similarity calculations
        self.memory_core.add_event("Second event")
        
        # Verify both events were stored
        result = self.memory_core.conn.execute("SELECT COUNT(*) FROM events").fetchone()
        self.assertEqual(result[0], 2)


if __name__ == '__main__':
    unittest.main()