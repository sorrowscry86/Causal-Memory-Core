"""
End-to-End Realistic Scenario Tests for Causal Memory Core
Tests realistic user workflows and scenarios that demonstrate the system's capabilities
"""

import pytest
import tempfile
import os
import time
import sys
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from causal_memory_core import CausalMemoryCore


class TestRealisticScenariosE2E:
    """End-to-End tests for realistic user scenarios"""
    
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
        """Mock OpenAI client with realistic responses"""
        mock_client = Mock()
        
        def mock_completion(messages, **kwargs):
            """Generate realistic causal reasoning responses"""
            context = messages[-1]['content']
            mock_response = Mock()
            mock_response.choices = [Mock()]
            
            # Simple pattern matching for realistic responses
            if "clicked" in context and "opened" in context:
                mock_response.choices[0].message.content = "The click action caused the menu/dialog to open, establishing a clear causal relationship."
            elif "typed" in context and "appeared" in context:
                mock_response.choices[0].message.content = "The typing action triggered the appearance of suggestions or results."
            elif "selected" in context and ("loaded" in context or "displayed" in context):
                mock_response.choices[0].message.content = "The selection action caused the content to be loaded and displayed."
            elif "error" in context.lower():
                mock_response.choices[0].message.content = "The error was caused by the previous action that failed."
            else:
                mock_response.choices[0].message.content = "These events appear to be causally related based on their temporal and semantic proximity."
            
            return mock_response
        
        mock_client.chat.completions.create.side_effect = mock_completion
        return mock_client
    
    @pytest.fixture 
    def mock_embedder(self):
        """Mock sentence transformer with realistic embeddings"""
        mock_embedder = Mock()
        
        def mock_encode(text):
            """Generate embeddings based on text content similarity"""
            text_lower = text.lower()
            
            # Similar embeddings for related concepts
            if "file" in text_lower or "document" in text_lower:
                base = [0.8, 0.2, 0.1, 0.1]
            elif "click" in text_lower or "button" in text_lower:
                base = [0.1, 0.8, 0.1, 0.1]
            elif "type" in text_lower or "text" in text_lower:
                base = [0.1, 0.1, 0.8, 0.1]
            elif "error" in text_lower or "fail" in text_lower:
                base = [0.1, 0.1, 0.1, 0.8]
            else:
                base = [0.5, 0.3, 0.2, 0.1]
            
            # Add small random variation to make embeddings more realistic
            import random
            variation = [random.uniform(-0.1, 0.1) for _ in range(4)]
            return [max(0, min(1, b + v)) for b, v in zip(base, variation)]
        
        mock_embedder.encode.side_effect = mock_encode
        return mock_embedder
    
    def test_e2e_document_editing_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test realistic document editing workflow scenario"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Simulate a realistic document editing session
            workflow_events = [
                "User opened the text editor application",
                "Editor window appeared on screen",
                "User clicked on 'File' menu",
                "File menu opened with options",
                "User selected 'New Document' option",
                "Blank document was created",
                "User typed 'Meeting Notes - Project Alpha'",
                "Text appeared in the document",
                "User pressed Enter to create new line",
                "Cursor moved to next line",
                "User typed the meeting agenda items",
                "Content was added to the document",
                "User clicked 'Save' button",
                "Save dialog opened",
                "User entered filename 'meeting_notes.txt'",
                "Document was saved successfully",
                "Success message appeared briefly"
            ]
            
            # Add events with small delays to simulate realistic timing
            for event in workflow_events:
                memory_core.add_event(event)
                time.sleep(0.01)  # Small delay for timestamp variation
            
            # Query about different aspects of the workflow
            queries = [
                "How did the document get created?",
                "What caused the text to appear in the document?",
                "How was the document saved?",
                "What happened when the user clicked File menu?"
            ]
            
            contexts = []
            for query in queries:
                context = memory_core.get_context(query)
                contexts.append(context)
                assert context != "No relevant context found in memory."
                assert isinstance(context, str)
                assert len(context) > 0
            
            # Verify that contexts contain relevant information
            # At least some contexts should mention key events
            all_contexts = " ".join(contexts)
            assert any(keyword in all_contexts.lower() for keyword in 
                      ["editor", "document", "file", "save", "text"])
            
        finally:
            memory_core.close()
    
    def test_e2e_software_debugging_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test realistic software debugging workflow scenario"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Simulate a debugging session
            debug_events = [
                "Developer ran the application from IDE",
                "Application started successfully",
                "Developer clicked 'Login' button",
                "Login form was submitted",
                "Error message appeared: 'Invalid credentials'",
                "Developer opened developer console",
                "Console showed network request failed with 401",
                "Developer checked the authentication code",
                "Found typo in password validation logic",
                "Developer corrected the typo in code",
                "Developer saved the code changes",
                "IDE automatically recompiled the project",
                "Developer refreshed the browser",
                "Application reloaded with new code",
                "Developer tried login again",
                "Login succeeded this time",
                "User was redirected to dashboard"
            ]
            
            for event in debug_events:
                memory_core.add_event(event)
                time.sleep(0.005)
            
            # Query about the debugging process
            debug_queries = [
                "Why did the login fail initially?",
                "How was the bug discovered?",
                "What fixed the login issue?",
                "What happened after the code was corrected?"
            ]
            
            for query in debug_queries:
                context = memory_core.get_context(query)
                assert context != "No relevant context found in memory."
                # Context should contain debugging-related information
                assert any(keyword in context.lower() for keyword in 
                          ["error", "developer", "code", "login", "typo"])
        
        finally:
            memory_core.close()
    
    def test_e2e_data_analysis_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test realistic data analysis workflow scenario"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Simulate data analysis session
            analysis_events = [
                "Analyst opened data science notebook",
                "Jupyter notebook interface loaded",
                "Analyst imported pandas and numpy libraries",
                "Import statements executed successfully",
                "Analyst loaded CSV file with sales data",
                "Data loaded into pandas DataFrame",
                "Analyst ran df.head() to preview data",
                "First 5 rows of data displayed",
                "Analyst noticed missing values in 'region' column",
                "Analyst ran df.isnull().sum() to count nulls",
                "Found 127 missing values in region column",
                "Analyst decided to fill missing values with 'Unknown'",
                "Executed fillna('Unknown') on region column",
                "Missing values were replaced successfully",
                "Analyst created pivot table by region and month",
                "Pivot table showed sales trends clearly",
                "Analyst generated visualization with matplotlib",
                "Bar chart was created and displayed",
                "Analyst exported results to Excel file",
                "Analysis results saved for presentation"
            ]
            
            for event in analysis_events:
                memory_core.add_event(event)
                time.sleep(0.003)
            
            # Query about data analysis steps
            analysis_queries = [
                "How did the analyst handle missing data?",
                "What visualization was created?",
                "How was the data initially loaded?",
                "What pattern did the analyst discover?"
            ]
            
            for query in analysis_queries:
                context = memory_core.get_context(query)
                assert context != "No relevant context found in memory."
                # Should reference data analysis activities
                assert any(keyword in context.lower() for keyword in 
                          ["data", "analyst", "pandas", "missing", "visualization"])
        
        finally:
            memory_core.close()
    
    def test_e2e_user_onboarding_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test realistic user onboarding workflow scenario"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Simulate new user onboarding
            onboarding_events = [
                "New user visited the application homepage",
                "Homepage loaded with welcome message",
                "User clicked 'Sign Up' button",
                "Registration form appeared",
                "User filled in email address",
                "User entered secure password",
                "User checked 'Agree to Terms' checkbox",
                "User clicked 'Create Account' button",
                "System validated the registration data",
                "Verification email sent to user",
                "User checked their email inbox",
                "Found verification email from system",
                "User clicked verification link",
                "Account was verified successfully",
                "User was redirected to welcome tutorial",
                "Tutorial showed key features",
                "User completed first tutorial step",
                "Progress indicator updated to 1/5",
                "User skipped remaining tutorial steps",
                "User was taken to main application dashboard",
                "Dashboard showed personalized welcome message"
            ]
            
            for event in onboarding_events:
                memory_core.add_event(event)
                time.sleep(0.002)
            
            # Query about onboarding process
            onboarding_queries = [
                "How did the user create their account?",
                "What happened after account verification?",
                "How did the user access the main application?",
                "What tutorial experience did the user have?"
            ]
            
            for query in onboarding_queries:
                context = memory_core.get_context(query)
                assert context != "No relevant context found in memory."
                assert any(keyword in context.lower() for keyword in 
                          ["user", "account", "registration", "tutorial", "verification"])
        
        finally:
            memory_core.close()
    
    def test_e2e_error_recovery_workflow(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test realistic error recovery workflow scenario"""
        memory_core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        try:
            # Simulate error and recovery scenario
            error_events = [
                "User was working on important document",
                "Document had 2 hours of unsaved changes",
                "System suddenly crashed unexpectedly",
                "Application closed without warning",
                "User tried to restart the application",
                "Application failed to start normally",
                "Error message displayed: 'Configuration corrupted'",
                "User searched for solutions online",
                "Found help article about configuration reset",
                "User backed up existing files",
                "User reset application configuration",
                "Configuration was restored to defaults",
                "User restarted application again",
                "Application started successfully this time",
                "Auto-recovery dialog appeared",
                "System found unsaved document backup",
                "User chose to recover the backup",
                "Document was restored with all changes",
                "User immediately saved the recovered document",
                "Crisis was resolved without data loss"
            ]
            
            for event in error_events:
                memory_core.add_event(event)
                time.sleep(0.001)
            
            # Query about error recovery
            recovery_queries = [
                "What caused the system to crash?",
                "How was the error resolved?",
                "Was any work lost during the crash?",
                "What recovery mechanism helped the user?"
            ]
            
            for query in recovery_queries:
                context = memory_core.get_context(query)
                assert context != "No relevant context found in memory."
                assert any(keyword in context.lower() for keyword in 
                          ["error", "crash", "recovery", "backup", "configuration"])
        
        finally:
            memory_core.close()
    
    def test_e2e_multi_session_continuity(self, temp_db_path, mock_openai_client, mock_embedder):
        """Test memory continuity across multiple sessions"""
        # Session 1: Initial work
        session1_events = [
            "User started project planning session",
            "Created new project roadmap document",
            "Added key milestones and deadlines",
            "Saved project as 'Q4_Roadmap.docx'"
        ]
        
        memory_core1 = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        for event in session1_events:
            memory_core1.add_event(event)
            time.sleep(0.01)
        
        memory_core1.close()
        
        # Session 2: Continue work (different memory core instance)
        session2_events = [
            "User reopened the project roadmap",
            "Reviewed previously created milestones",
            "Added resource allocation details",
            "Updated timeline based on team feedback"
        ]
        
        memory_core2 = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_openai_client,
            embedding_model=mock_embedder
        )
        
        for event in session2_events:
            memory_core2.add_event(event)
            time.sleep(0.01)
        
        # Query should find events from both sessions
        context = memory_core2.get_context("project roadmap development")
        assert context != "No relevant context found in memory."
        
        # Context should reference activities from both sessions
        context_lower = context.lower()
        assert any(keyword in context_lower for keyword in 
                  ["project", "roadmap", "milestone", "planning"])
        
        memory_core2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])