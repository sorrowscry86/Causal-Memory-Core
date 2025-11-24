"""
Test cases for narrative continuity detection in sequential workflows.

These tests validate that the Causal Memory Core can detect and link
sequential events that lack explicit causal language, forming coherent
narrative chains from dry system logs and workflow steps.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock
import numpy as np

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from causal_memory_core import CausalMemoryCore


class TestNarrativeContinuity(unittest.TestCase):
    """Test narrative continuity detection for sequential workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        os.unlink(self.temp_db_path)  # Let DuckDB create the file
    
    def tearDown(self):
        """Clean up test resources"""
        if hasattr(self, 'memory_core') and self.memory_core:
            self.memory_core.close()
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
    
    def _create_mock_llm_for_sequential_workflow(self):
        """Create mock LLM that recognizes sequential workflow relationships"""
        mock_llm = Mock()
        
        def mock_completion(messages, **kwargs):
            context = messages[-1]['content']
            mock_response = Mock()
            mock_response.choices = [Mock()]
            
            # Recognize sequential patterns in workflows
            lower_context = context.lower()
            
            # Code refactoring patterns
            if "extract" in lower_context and "rename" in lower_context:
                mock_response.choices[0].message.content = (
                    "These are sequential refactoring steps in the same code module."
                )
            elif "rename" in lower_context and "test" in lower_context:
                mock_response.choices[0].message.content = (
                    "Tests were added after renaming to validate the refactored code."
                )
            # Incident response patterns
            elif "alert" in lower_context and ("check" in lower_context or "log" in lower_context):
                mock_response.choices[0].message.content = (
                    "These are sequential incident response actions."
                )
            elif ("check" in lower_context or "log" in lower_context) and "restart" in lower_context:
                mock_response.choices[0].message.content = (
                    "Service was restarted after checking its status."
                )
            # Database migration patterns
            elif "backup" in lower_context and "migration" in lower_context:
                mock_response.choices[0].message.content = (
                    "Database was backed up before running the migration."
                )
            elif "migration" in lower_context and "verify" in lower_context:
                mock_response.choices[0].message.content = (
                    "Data integrity was verified after the migration completed."
                )
            # Deployment patterns
            elif "build" in lower_context and "deploy" in lower_context:
                mock_response.choices[0].message.content = (
                    "The application was deployed after the build succeeded."
                )
            elif "deploy" in lower_context and "monitor" in lower_context:
                mock_response.choices[0].message.content = (
                    "Monitoring was started to track the deployment."
                )
            # Generic workflow recognition
            else:
                mock_response.choices[0].message.content = (
                    "These events are part of the same workflow sequence."
                )
            
            return mock_response
        
        mock_llm.chat.completions.create.side_effect = mock_completion
        return mock_llm
    
    def _create_mock_embedder_with_semantic_clusters(self):
        """Create mock embedder that groups semantically related concepts"""
        mock_embedder = Mock()
        
        def mock_encode(text):
            text_lower = text.lower()
            
            # Refactoring cluster
            if any(word in text_lower for word in ["refactor", "extract", "rename", "test"]):
                base = np.array([0.9, 0.8, 0.1, 0.1])
            # Incident response cluster
            elif any(word in text_lower for word in ["alert", "incident", "check", "restart", "log"]):
                base = np.array([0.1, 0.9, 0.8, 0.1])
            # Database operations cluster
            elif any(word in text_lower for word in ["database", "backup", "migration", "verify"]):
                base = np.array([0.1, 0.1, 0.9, 0.8])
            # Deployment cluster
            elif any(word in text_lower for word in ["build", "deploy", "release", "monitor"]):
                base = np.array([0.8, 0.1, 0.1, 0.9])
            else:
                base = np.array([0.5, 0.5, 0.5, 0.5])
            
            # Add small random variation
            variation = np.random.uniform(-0.05, 0.05, 4)
            result = base + variation
            # Normalize to [0, 1]
            return np.clip(result, 0, 1)
        
        mock_embedder.encode.side_effect = mock_encode
        return mock_embedder
    
    def test_code_refactoring_workflow(self):
        """Test that code refactoring steps form a narrative chain"""
        mock_llm = self._create_mock_llm_for_sequential_workflow()
        mock_embedder = self._create_mock_embedder_with_semantic_clusters()
        
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
            similarity_threshold=0.7
        )
        
        # Add refactoring events
        self.memory_core.add_event("Extracted calculateTotal() method from OrderProcessor")
        self.memory_core.add_event("Renamed variables in calculateTotal() for clarity")
        self.memory_core.add_event("Added unit tests for calculateTotal() method")
        
        # Query should return narrative chain
        result = self.memory_core.query("What refactoring was done?")
        
        # Verify narrative chain is formed
        self.assertIn("Initially", result)
        self.assertIn("calculateTotal()", result)
        self.assertNotEqual(result, "No relevant context found in memory.")
        
        # Verify causal links were created
        rows = self.memory_core.conn.execute(
            "SELECT event_id, cause_id, relationship_text FROM events ORDER BY event_id"
        ).fetchall()
        
        # First event has no cause
        self.assertIsNone(rows[0][1])
        
        # Second and third events should have causes
        self.assertIsNotNone(rows[1][1])
        self.assertIsNotNone(rows[1][2])  # relationship_text should exist
        self.assertIsNotNone(rows[2][1])
        self.assertIsNotNone(rows[2][2])
    
    def test_incident_resolution_workflow(self):
        """Test that incident resolution steps form a narrative chain"""
        mock_llm = self._create_mock_llm_for_sequential_workflow()
        mock_embedder = self._create_mock_embedder_with_semantic_clusters()
        
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
            similarity_threshold=0.7
        )
        
        # Add incident response events
        self.memory_core.add_event("Received alert for API service timeout")
        self.memory_core.add_event("Checked service logs and found memory leak")
        self.memory_core.add_event("Restarted service to restore availability")
        
        # Query should return narrative chain
        result = self.memory_core.query("What happened with the incident?")
        
        # Verify narrative chain is formed
        self.assertIn("Initially", result)
        self.assertIn("alert", result.lower())
        self.assertNotEqual(result, "No relevant context found in memory.")
        
        # Verify all events are linked
        rows = self.memory_core.conn.execute(
            "SELECT event_id, cause_id FROM events ORDER BY event_id"
        ).fetchall()
        
        self.assertIsNone(rows[0][1])  # First event has no cause
        self.assertIsNotNone(rows[1][1])  # Second event has cause
        self.assertIsNotNone(rows[2][1])  # Third event has cause
    
    def test_database_migration_workflow(self):
        """Test that database migration steps form a narrative chain"""
        mock_llm = self._create_mock_llm_for_sequential_workflow()
        mock_embedder = self._create_mock_embedder_with_semantic_clusters()
        
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
            similarity_threshold=0.7
        )
        
        # Add database migration events
        self.memory_core.add_event("Created database backup before migration")
        self.memory_core.add_event("Ran migration scripts to update schema")
        self.memory_core.add_event("Verified data integrity after migration")
        
        # Query should return narrative chain
        result = self.memory_core.query("What database work was done?")
        
        # Verify narrative chain
        self.assertIn("Initially", result)
        self.assertIn("backup", result.lower())
        
        # Check links
        rows = self.memory_core.conn.execute(
            "SELECT COUNT(*) FROM events WHERE cause_id IS NOT NULL"
        ).fetchone()
        
        # At least 2 events should have causes (events 2 and 3)
        self.assertGreaterEqual(rows[0], 2)
    
    def test_deployment_workflow(self):
        """Test that deployment steps form a narrative chain"""
        mock_llm = self._create_mock_llm_for_sequential_workflow()
        mock_embedder = self._create_mock_embedder_with_semantic_clusters()
        
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
            similarity_threshold=0.7
        )
        
        # Add deployment events
        self.memory_core.add_event("Built application artifacts from main branch")
        self.memory_core.add_event("Deployed version 2.1.0 to production")
        self.memory_core.add_event("Started monitoring dashboards for new release")
        
        # Query should return narrative chain
        result = self.memory_core.query("What deployment happened?")
        
        # Verify narrative
        self.assertIn("Initially", result)
        
        # Verify relationship texts exist
        rows = self.memory_core.conn.execute(
            "SELECT relationship_text FROM events WHERE relationship_text IS NOT NULL"
        ).fetchall()
        
        # Should have relationship descriptions for linked events
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertIsNotNone(row[0])
            self.assertNotEqual(row[0], "")
    
    def test_narrative_continuity_respects_similarity_threshold(self):
        """Test that unrelated events don't form narrative chains"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "No."
        mock_llm.chat.completions.create.return_value = mock_response
        
        mock_embedder = Mock()
        def mock_encode(text):
            # Return dissimilar embeddings for unrelated events
            if "refactor" in text.lower():
                return np.array([0.9, 0.1, 0.1, 0.1])
            elif "database" in text.lower():
                return np.array([0.1, 0.9, 0.1, 0.1])
            return np.array([0.5, 0.5, 0.5, 0.5])
        
        mock_embedder.encode.side_effect = mock_encode
        
        self.memory_core = CausalMemoryCore(
            db_path=self.temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder,
            similarity_threshold=0.7
        )
        
        # Add unrelated events
        self.memory_core.add_event("Refactored authentication module")
        self.memory_core.add_event("Updated database backup schedule")
        
        # Check that no causal links were created
        rows = self.memory_core.conn.execute(
            "SELECT COUNT(*) FROM events WHERE cause_id IS NOT NULL"
        ).fetchone()
        
        self.assertEqual(rows[0], 0)


if __name__ == '__main__':
    unittest.main()
