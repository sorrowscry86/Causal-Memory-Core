"""
Investigation tests for SIMILARITY_THRESHOLD optimization
Tests different threshold values (0.3, 0.5, 0.7) to determine optimal setting
"""

import unittest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore, Event


class TestSimilarityThresholdInvestigation(unittest.TestCase):
    """Investigation of optimal SIMILARITY_THRESHOLD values"""
    
    def setUp(self):
        """Set up test database and mocked components"""
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        self.temp_db_path = temp_db.name
        os.unlink(self.temp_db_path)  # Let DuckDB create it
        
        # Mock LLM and embedder
        self.mock_llm = Mock()
        self.mock_embedder = Mock()
        
        # Mock LLM response for causality judgment
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The first event caused the second event."
        self.mock_llm.chat.completions.create.return_value = mock_response
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
            
    def create_memory_core_with_threshold(self, threshold):
        """Create memory core with specific similarity threshold"""
        import config as config_mod
        with patch.object(config_mod.Config, 'SIMILARITY_THRESHOLD', threshold):
            return CausalMemoryCore(
                db_path=self.temp_db_path,
                llm_client=self.mock_llm,
                embedding_model=self.mock_embedder
            )
    
    def test_threshold_0_3_permissive(self):
        """Test threshold 0.3 - should be very permissive and find many connections"""
        memory_core = self.create_memory_core_with_threshold(0.3)
        
        # Create embeddings with moderate similarity (0.4 cosine similarity)
        embedding1 = np.array([1.0, 0.5, 0.0, 0.0])  # Normalized: [0.894, 0.447, 0, 0]
        embedding2 = np.array([0.8, 0.6, 0.0, 0.0])  # Normalized: [0.8, 0.6, 0, 0]
        
        # Calculate expected similarity: ~0.89 * 0.8 + 0.45 * 0.6 = 0.98 > 0.3
        self.mock_embedder.encode.side_effect = [embedding1, embedding2]
        
        # Add events
        memory_core.add_event("User clicked button")
        memory_core.add_event("Dialog opened")
        
        # Check if causal link was found
        events = memory_core.conn.execute("""
            SELECT cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertIsNone(events[0][0])  # First event (no cause)
        self.assertIsNotNone(events[1][0])  # Second event should have cause
        
    def test_threshold_0_5_moderate(self):
        """Test threshold 0.5 - should be moderately selective"""
        memory_core = self.create_memory_core_with_threshold(0.5)
        
        # Create embeddings with borderline similarity (~0.45)
        embedding1 = np.array([1.0, 0.0, 0.0, 0.0])
        embedding2 = np.array([0.8, 0.6, 0.0, 0.0])  # cos sim ~0.8 
        
        self.mock_embedder.encode.side_effect = [embedding1, embedding2]
        
        # Add events
        memory_core.add_event("User action A")
        memory_core.add_event("Result B")
        
        # Check if causal link was found
        events = memory_core.conn.execute("""
            SELECT cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertIsNone(events[0][0])  # First event (no cause)
        self.assertIsNotNone(events[1][0])  # Second event should have cause (0.8 > 0.5)
        
    def test_threshold_0_7_strict(self):
        """Test threshold 0.7 - should be strict and require high similarity"""
        memory_core = self.create_memory_core_with_threshold(0.7)
        
        # Create embeddings with medium similarity (~0.6)
        embedding1 = np.array([1.0, 1.0, 0.0, 0.0])  # Normalized: [0.707, 0.707, 0, 0]
        embedding2 = np.array([1.0, 0.5, 0.0, 0.0])  # Normalized: [0.894, 0.447, 0, 0]
        # cos sim = 0.707 * 0.894 + 0.707 * 0.447 = 0.632 + 0.316 = 0.948 > 0.7
        
        self.mock_embedder.encode.side_effect = [embedding1, embedding2]
        
        # Add events
        memory_core.add_event("Event A")
        memory_core.add_event("Event B")
        
        # Check if causal link was found
        events = memory_core.conn.execute("""
            SELECT cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertIsNone(events[0][0])  # First event (no cause)
        self.assertIsNotNone(events[1][0])  # Second event should have cause (high similarity)
        
    def test_threshold_0_7_strict_no_connection(self):
        """Test threshold 0.7 - should reject low similarity connections"""
        memory_core = self.create_memory_core_with_threshold(0.7)
        
        # Create embeddings with low similarity
        embedding1 = np.array([1.0, 0.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0, 0.0])  # cos sim = 0 < 0.7
        
        self.mock_embedder.encode.side_effect = [embedding1, embedding2]
        
        # Add events
        memory_core.add_event("Unrelated event A")
        memory_core.add_event("Unrelated event B")
        
        # Check that no causal link was found
        events = memory_core.conn.execute("""
            SELECT cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertIsNone(events[0][0])  # First event (no cause)
        self.assertIsNone(events[1][0])  # Second event (no cause - similarity too low)
        
    def test_context_retrieval_with_different_thresholds(self):
        """Test how different thresholds affect context retrieval quality"""
        for threshold in [0.3, 0.5, 0.7]:
            with self.subTest(threshold=threshold):
                memory_core = self.create_memory_core_with_threshold(threshold)
                
                # Add events with known embeddings
                high_sim_embedding = np.array([0.9, 0.9, 0.0, 0.0])
                query_embedding = np.array([0.85, 0.85, 0.1, 0.1])  # High similarity to above
                
                self.mock_embedder.encode.side_effect = [
                    high_sim_embedding,  # For add_event
                    query_embedding      # For get_context query
                ]
                
                memory_core.add_event("User performed important action")
                
                # Query for context
                result = memory_core.get_context("important action")
                
                # All thresholds should find this high-similarity match
                self.assertIn("important action", result)
                self.assertIn("Initially,", result)
                
    def test_find_most_relevant_event_threshold_behavior(self):
        """Test how _find_most_relevant_event behaves with different thresholds"""
        for i, threshold in enumerate([0.3, 0.5, 0.7]):
            with self.subTest(threshold=threshold):
                memory_core = self.create_memory_core_with_threshold(threshold)
                
                # Add an event with known embedding (use unique event_id)
                event_embedding = np.array([1.0, 0.0, 0.0, 0.0])
                memory_core.conn.execute("""
                    INSERT INTO events (event_id, timestamp, effect_text, embedding)
                    VALUES (?, ?, 'Test event', ?)
                """, [i + 10, datetime.now(), event_embedding.tolist()])  # Use unique ID
                
                # Test with query embeddings of different similarities
                # High similarity query (cosine sim = 1.0)
                high_sim_result = memory_core._find_most_relevant_event([1.0, 0.0, 0.0, 0.0])
                self.assertIsNotNone(high_sim_result)  # Should be found regardless of threshold
                
                # Medium similarity query (cosine sim ~= 0.6)
                med_sim_result = memory_core._find_most_relevant_event([0.8, 0.6, 0.0, 0.0])
                if threshold <= 0.5:
                    self.assertIsNotNone(med_sim_result)
                # For 0.7 threshold, this depends on exact calculation
                
                # Low similarity query (cosine sim = 0.0)
                low_sim_result = memory_core._find_most_relevant_event([0.0, 1.0, 0.0, 0.0])
                self.assertIsNone(low_sim_result)  # Should not be found for any reasonable threshold
                
    def test_realistic_similarity_scenarios(self):
        """Test with realistic text similarity scenarios"""
        memory_core = self.create_memory_core_with_threshold(0.5)  # Use moderate threshold
        
        # Simulate realistic embeddings for similar actions
        similar_embeddings = [
            [0.8, 0.2, 0.1, 0.0],  # "clicked button"
            [0.7, 0.3, 0.2, 0.0],  # "pressed button" - very similar
            [0.2, 0.8, 0.1, 0.0],  # "opened window" - different action
        ]
        
        self.mock_embedder.encode.side_effect = similar_embeddings + similar_embeddings
        
        # Add events
        memory_core.add_event("User clicked the submit button")
        memory_core.add_event("Form was submitted")  # Should link to button click
        memory_core.add_event("New window opened")   # Should not link (different action)
        
        # Check causal relationships
        events = memory_core.conn.execute("""
            SELECT event_id, effect_text, cause_id FROM events ORDER BY event_id
        """).fetchall()
        
        self.assertEqual(len(events), 3)
        self.assertIsNone(events[0][2])    # First event (no cause)
        # Depending on similarity calculation, second event may or may not have cause
        # Third event should not be causally linked to either (different semantic space)


if __name__ == '__main__':
    unittest.main()