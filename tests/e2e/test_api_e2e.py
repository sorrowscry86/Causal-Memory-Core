"""
End-to-End Tests for Causal Memory Core API
Tests complete user workflows through the direct API interface
"""

import pytest
import tempfile
import os
import time
from datetime import datetime
from unittest.mock import Mock, patch

# Add src to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from causal_memory_core import CausalMemoryCore


class TestCausalMemoryCoreE2E:
    """End-to-End tests for the Causal Memory Core API"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db.name
        temp_db.close()
        os.unlink(temp_db_path)  # Let DuckDB create the file
        yield temp_db_path
        # Cleanup
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The user clicking the file button caused the file to open."
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def mock_embedder(self):
        """Mock sentence transformer for testing"""
        mock_embedder = Mock()
        mock_embedder.encode.return_value = [0.1, 0.2, 0.3, 0.4]  # Consistent embeddings
        return mock_embedder
    
    def test_e2e_single_event_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test complete workflow: Initialize -> Add Event -> Query -> Cleanup"""
        # Initialize memory core
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Add a single event
            event_text = "User opened the main application"
            memory_core.add_event(event_text)
            
            # Query for context
            context = memory_core.get_context("opening application")
            
            # Verify context is returned
            assert context != "No relevant context found in memory."
            assert context.startswith("Initially,")
            assert event_text in context
            
        finally:
            memory_core.close()
    
    def test_e2e_causal_chain_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test complete causal chain workflow: Multiple events -> Causal relationships -> Query chain"""
        # Set up mock responses for causal relationships
        def side_effect_embed(text):
            if "clicked" in text:
                return [0.8, 0.1, 0.1, 0.1]  # Similar to first event
            elif "opened" in text:
                return [0.7, 0.2, 0.1, 0.1]  # Similar but not identical
            else:
                return [0.1, 0.2, 0.3, 0.4]  # Default
        
        mock_embedder.encode.side_effect = side_effect_embed
        
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Add sequence of related events
            events = [
                "User clicked on the file menu",
                "File menu opened displaying options",
                "User selected 'Open' from the menu",
                "File dialog appeared",
                "User chose a document file",
                "Document loaded into the editor"
            ]
            
            for event in events:
                memory_core.add_event(event)
                # Small delay to ensure different timestamps
                time.sleep(0.01)
            
            # Query for the complete context
            context = memory_core.get_context("how did the document get loaded")
            
            # Verify we get a narrative chain
            assert context != "No relevant context found in memory."
            # Should contain causal chain elements
            assert any(keyword in context.lower() for keyword in ["initially", "this led to", "then", "finally"])
            # Should contain some of our events
            assert any(event_part in context for event_part in ["clicked", "menu", "document"])
            
        finally:
            memory_core.close()
    
    def test_e2e_memory_persistence(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test that memory persists across different sessions"""
        event_text = "User created a new project"
        
        # Session 1: Add event
        memory_core1 = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        memory_core1.add_event(event_text)
        memory_core1.close()
        
        # Session 2: Query for the event
        memory_core2 = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            context = memory_core2.get_context("project creation")
            
            # Verify the event persists
            assert context != "No relevant context found in memory."
            assert event_text in context
            
        finally:
            memory_core2.close()
    
    def test_e2e_no_relevant_context(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test querying when no relevant context exists"""
        # Set up embedder to return very different embeddings
        mock_embedder.encode.side_effect = [
            [1.0, 0.0, 0.0, 0.0],  # Event embedding
            [0.0, 0.0, 0.0, 1.0]   # Query embedding (very different)
        ]
        
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Add event about cooking
            memory_core.add_event("User prepared a delicious pasta dish")
            
            # Query about something completely unrelated
            context = memory_core.get_context("rocket science calculations")
            
            # Should return no relevant context
            assert context == "No relevant context found in memory."
            
        finally:
            memory_core.close()
    
    def test_e2e_error_handling_invalid_db_path(self, mock_openai_client, mock_embedder):
        """Test error handling with invalid database path"""
        # Try to initialize with an invalid path (directory that doesn't exist)
        invalid_path = "/nonexistent/directory/test.db"
        
        with pytest.raises(Exception):
            memory_core = CausalMemoryCore(
                db_path=invalid_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
    
    def test_e2e_large_context_query(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test querying with many events in memory"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Add many events
            for i in range(20):
                memory_core.add_event(f"User performed action {i} in the workflow")
                time.sleep(0.001)  # Small delay for timestamp variation
            
            # Query should still work efficiently
            context = memory_core.get_context("workflow actions")
            
            # Should get some relevant context
            assert context != "No relevant context found in memory."
            
        finally:
            memory_core.close()

    def test_e2e_bug_report_saga_narrative(self, temp_db_path, mock_openai_client, mock_embedder):
        """Phase 2: Bug Report Saga — exact chronological narrative match"""
        # Configure embedder to make each event most similar to its immediate predecessor
        def embed_side_effect(text):
            text_l = str(text).lower()
            if "bug report" in text_l:
                return [1.0, 0.00, 0.0, 0.0]
            if "logs" in text_l:
                return [1.0, 0.01, 0.0, 0.0]
            if "service code" in text_l or "code is reviewed" in text_l or "code" in text_l:
                return [1.0, 0.02, 0.0, 0.0]
            if "patch is written" in text_l or "patch" in text_l:
                return [1.0, 0.03, 0.0, 0.0]
            if "deployed" in text_l or "resolved" in text_l:
                return [1.0, 0.04, 0.0, 0.0]
            # default for queries
            return [1.0, 0.04, 0.0, 0.0]
        mock_embedder.encode.side_effect = embed_side_effect

        # Configure LLM to confirm causality with specific relationships, in order
        relationships = [
            "Investigating logs was the next step after the bug report",
            "The logs indicated a null reference, prompting code review",
            "The missing check necessitated a patch",
            "Deployment resolved the issue"
        ]
        def llm_side_effect(*args, **kwargs):
            resp = Mock()
            resp.choices = [Mock()]
            # Pop next relationship; if exhausted, repeat last
            content = relationships.pop(0) if relationships else "Deployment resolved the issue"
            resp.choices[0].message.content = content
            return resp
        mock_openai_client.chat.completions.create.side_effect = llm_side_effect

        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )

        try:
            events = [
                'A bug report is filed for "User login fails with 500 error"',
                'The production server logs are inspected, revealing a NullPointerException',
                'The UserAuthentication service code is reviewed, identifying a missing null check',
                'A patch is written to add the necessary null check',
                'The patch is successfully deployed to production, and the bug is marked as resolved'
            ]

            for e in events:
                memory_core.add_event(e)
                time.sleep(0.01)

            # Query near the final event
            narrative = memory_core.get_context("bug resolved")

            # Check that the narrative contains the complete causal chain
            expected_parts = [
                'A bug report is filed for "User login fails with 500 error"',
                'The production server logs are inspected, revealing a NullPointerException',
                'Investigating logs was the next step after the bug report',
                'The UserAuthentication service code is reviewed, identifying a missing null check',
                'The logs indicated a null reference, prompting code review',
                'A patch is written to add the necessary null check',
                'The missing check necessitated a patch',
                'The patch is successfully deployed to production, and the bug is marked as resolved',
                'Deployment resolved the issue'
            ]

            # Ensure all expected parts are in the narrative
            for part in expected_parts:
                assert part in narrative, f"Expected '{part}' to be in narrative: {narrative}"
        finally:
            memory_core.close()
    
    def test_e2e_special_characters_in_events(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test handling events with special characters and unicode"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Test various special characters and unicode
            special_events = [
                "User entered: Hello, World! (with punctuation)",
                "File saved as 'project_v1.2.3.txt'",
                "Error: Cannot access file '/path/to/file'",
                "User typed: αβγδε (Greek letters)",
                "Message: Success! ✅ Task completed",
                "Data: {\"key\": \"value\", \"number\": 42}"
            ]
            
            for event in special_events:
                memory_core.add_event(event)
            
            # Query should handle special characters
            context = memory_core.get_context("special characters and symbols")
            
            # Should get relevant context without errors
            assert isinstance(context, str)
            
        finally:
            memory_core.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])