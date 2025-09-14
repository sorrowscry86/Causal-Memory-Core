"""
End-to-end validation test for semantic search and context retrieval fixes
Tests the complete pipeline to ensure everything works correctly
"""

import unittest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from causal_memory_core import CausalMemoryCore


class TestSemanticSearchValidation(unittest.TestCase):
    """End-to-end validation of semantic search and context retrieval"""
    
    def setUp(self):
        """Set up test database and realistic scenario"""
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        self.temp_db_path = temp_db.name
        os.unlink(self.temp_db_path)
        
        # Mock LLM and embedder for realistic scenarios
        self.mock_llm = Mock()
        self.mock_embedder = Mock()
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
            
    def test_file_editing_workflow_semantic_search(self):
        """Test semantic search with a realistic file editing workflow"""
        
        # Define realistic causal relationships for file editing
        def mock_llm_response(messages, **kwargs):
            prompt = messages[0]['content']
            mock_response = Mock()
            mock_response.choices = [Mock()]
            
            # Realistic causality judgments
            if "opened the text editor" in prompt and "blank document" in prompt:
                mock_response.choices[0].message.content = "Opening the text editor caused a blank document to appear."
            elif "typed" in prompt and "text appeared" in prompt:
                mock_response.choices[0].message.content = "Typing caused the text to appear in the editor."
            elif "pressed Ctrl+S" in prompt and "save dialog" in prompt:
                mock_response.choices[0].message.content = "Pressing Ctrl+S caused the save dialog to open."
            elif "entered filename" in prompt and "file was saved" in prompt:
                mock_response.choices[0].message.content = "Entering the filename caused the file to be saved."
            elif "file was saved" in prompt and "title changed" in prompt:
                mock_response.choices[0].message.content = "Saving the file caused the document title to change."
            else:
                mock_response.choices[0].message.content = "No."
                
            return mock_response
        
        self.mock_llm.chat.completions.create.side_effect = mock_llm_response
        
        # Define realistic embeddings for file editing actions
        # These simulate semantic similarity between related actions
        editing_embeddings = [
            [0.8, 0.2, 0.1, 0.0],  # "opened text editor" 
            [0.7, 0.3, 0.1, 0.0],  # "blank document appeared" - similar to opening
            [0.1, 0.8, 0.2, 0.0],  # "typed text" - different semantic space (input action)
            [0.1, 0.7, 0.3, 0.0],  # "text appeared" - similar to typing
            [0.2, 0.1, 0.8, 0.0],  # "pressed Ctrl+S" - save action
            [0.3, 0.1, 0.7, 0.1],  # "save dialog opened" - similar to save action
            [0.2, 0.2, 0.6, 0.2],  # "entered filename" - file naming action
            [0.1, 0.1, 0.7, 0.3],  # "file was saved" - completion of save
            [0.4, 0.1, 0.5, 0.3],  # "title changed" - UI update related to save
        ]
        
        # Add embeddings for queries
        query_embeddings = [
            [0.2, 0.1, 0.75, 0.1],  # "How was the file saved?" - should match save actions
            [0.1, 0.75, 0.2, 0.0],  # "What caused the text to appear?" - should match typing
            [0.7, 0.25, 0.1, 0.0],  # "How did the editor open?" - should match opening
        ]
        
        all_embeddings = editing_embeddings + query_embeddings
        self.mock_embedder.encode.side_effect = [np.array(emb) for emb in all_embeddings]
        
        # Create memory core with moderate threshold
        import config as config_mod
        with patch.object(config_mod.Config, 'SIMILARITY_THRESHOLD', 0.5):
            memory_core = CausalMemoryCore(
                db_path=self.temp_db_path,
                llm_client=self.mock_llm,
                embedding_model=self.mock_embedder
            )
        
        # Add the file editing sequence
        events = [
            "User opened the text editor application",
            "A blank document appeared on screen",
            "User typed 'Hello World' into the document", 
            "The text appeared in the editor window",
            "User pressed Ctrl+S to save",
            "A save dialog box opened",
            "User entered 'hello.txt' as the filename",
            "The file was saved to disk",
            "The document title changed to show 'hello.txt'"
        ]
        
        # Record events
        for event in events:
            memory_core.add_event(event)
            
        # Test semantic search with different queries
        test_queries = [
            ("How was the file saved?", ["Ctrl+S", "save dialog", "filename", "saved"]),
            ("What caused the text to appear?", ["typed", "Hello World", "text appeared"]),
            ("How did the editor open?", ["opened", "text editor", "blank document"])
        ]
        
        for query, expected_keywords in test_queries:
            with self.subTest(query=query):
                context = memory_core.get_context(query)
                
                # Should return a meaningful narrative
                self.assertIsInstance(context, str)
                self.assertGreater(len(context), 10)
                
                # Should contain relevant keywords
                context_lower = context.lower()
                found_keywords = [kw for kw in expected_keywords if kw.lower() in context_lower]
                self.assertGreater(len(found_keywords), 0, 
                    f"Query '{query}' should find context containing {expected_keywords}, got: {context}")
                
                # Should have proper narrative format
                self.assertTrue(
                    context.startswith("Initially,") or "Initially:" in context,
                    f"Context should start with proper narrative format: {context}"
                )
                
        memory_core.close()
        
    def test_similarity_threshold_effectiveness(self):
        """Test that different similarity thresholds produce appropriate results"""
        
        # Mock LLM that always finds causality (to test threshold filtering)
        self.mock_llm.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="First event caused second event."))]
        )
        
        # Test scenarios with different similarity levels
        test_cases = [
            {
                'threshold': 0.3,
                'embedding1': [1.0, 0.0, 0.0, 0.0],
                'embedding2': [0.4, 0.9, 0.0, 0.0],  # cos sim ≈ 0.4 > 0.3
                'should_link': True,
                'description': 'Low threshold should link moderate similarities'
            },
            {
                'threshold': 0.7, 
                'embedding1': [1.0, 0.0, 0.0, 0.0],
                'embedding2': [0.4, 0.9, 0.0, 0.0],  # cos sim ≈ 0.4 < 0.7
                'should_link': False,
                'description': 'High threshold should reject moderate similarities'
            },
            {
                'threshold': 0.7,
                'embedding1': [1.0, 0.0, 0.0, 0.0], 
                'embedding2': [0.9, 0.1, 0.0, 0.0],  # cos sim ≈ 0.9 > 0.7
                'should_link': True,
                'description': 'High threshold should accept high similarities'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case['description']):
                # Create fresh memory core with specific threshold
                import config as config_mod
                with patch.object(config_mod.Config, 'SIMILARITY_THRESHOLD', case['threshold']):
                    memory_core = CausalMemoryCore(
                        db_path=self.temp_db_path,
                        llm_client=self.mock_llm,
                        embedding_model=self.mock_embedder
                    )
                
                # Set up embeddings
                self.mock_embedder.encode.side_effect = [
                    np.array(case['embedding1']),
                    np.array(case['embedding2'])
                ]
                
                # Add events
                memory_core.add_event("First event")
                memory_core.add_event("Second event")
                
                # Check causal linking
                events = memory_core.conn.execute("""
                    SELECT cause_id FROM events ORDER BY event_id
                """).fetchall()
                
                if case['should_link']:
                    self.assertIsNotNone(events[1][0], 
                        f"Threshold {case['threshold']} should link events with similarity")
                else:
                    self.assertIsNone(events[1][0],
                        f"Threshold {case['threshold']} should not link events with low similarity")
                
                memory_core.close()
                
                # Clean up for next test
                if os.path.exists(self.temp_db_path):
                    os.unlink(self.temp_db_path)
                    
    def test_context_retrieval_accuracy(self):
        """Test that context retrieval finds the most relevant events"""
        
        # Mock LLM for specific causal relationships
        def mock_causality_judgment(messages, **kwargs):
            prompt = messages[0]['content']
            mock_response = Mock()
            mock_response.choices = [Mock()]
            
            if "bug report" in prompt and "developer" in prompt:
                mock_response.choices[0].message.content = "Bug report caused developer to investigate."
            elif "developer" in prompt and "code fix" in prompt:
                mock_response.choices[0].message.content = "Developer investigation led to code fix."
            elif "code fix" in prompt and "tested" in prompt:
                mock_response.choices[0].message.content = "Code fix caused testing to occur."
            else:
                mock_response.choices[0].message.content = "No."
                
            return mock_response
        
        self.mock_llm.chat.completions.create.side_effect = mock_causality_judgment
        
        # Create embeddings for bug fixing workflow
        bug_fix_embeddings = [
            [0.9, 0.1, 0.0, 0.0],  # "bug report filed"
            [0.8, 0.2, 0.0, 0.0],  # "developer assigned" - related to bug
            [0.1, 0.9, 0.0, 0.0],  # "code fix implemented" - development action
            [0.1, 0.8, 0.1, 0.0],  # "fix tested successfully" - testing action
            [0.0, 0.1, 0.9, 0.0],  # "weather is sunny" - unrelated
        ]
        
        # Query embeddings
        query_embeddings = [
            [0.85, 0.15, 0.0, 0.0],  # "bug fix process" - should match bug-related events
            [0.05, 0.85, 0.1, 0.0],  # "development work" - should match code/testing
        ]
        
        all_embeddings = bug_fix_embeddings + query_embeddings
        self.mock_embedder.encode.side_effect = [np.array(emb) for emb in all_embeddings]
        
        import config as config_mod
        with patch.object(config_mod.Config, 'SIMILARITY_THRESHOLD', 0.5):
            memory_core = CausalMemoryCore(
                db_path=self.temp_db_path,
                llm_client=self.mock_llm,
                embedding_model=self.mock_embedder
            )
        
        # Add events
        events = [
            "Bug report filed for login issue",
            "Developer assigned to investigate",
            "Code fix implemented for login",
            "Fix tested successfully",
            "Weather is sunny today"  # Unrelated event
        ]
        
        for event in events:
            memory_core.add_event(event)
            
        # Test queries
        bug_context = memory_core.get_context("bug fix process")
        dev_context = memory_core.get_context("development work")
        
        # Bug context should focus on bug-related events
        self.assertIn("bug", bug_context.lower())
        self.assertIn("developer", bug_context.lower())
        self.assertNotIn("weather", bug_context.lower())  # Should not include unrelated events
        
        # Development context should focus on code/testing  
        self.assertIn("code", dev_context.lower())
        self.assertNotIn("weather", dev_context.lower())
        
        memory_core.close()


if __name__ == '__main__':
    unittest.main()