"""
End-to-End Tests for Causal Memory Core CLI
Tests complete user workflows through the command-line interface
"""

import pytest
import tempfile
import os
import subprocess
import sys
import json
from unittest.mock import patch, Mock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCausalMemoryCoreCLIE2E:
    """End-to-End tests for the CLI interface"""
    
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
    def cli_env(self):
        """Set up environment for CLI testing"""
        env = os.environ.copy()
        # Ensure we have required env vars for CLI
        env['OPENAI_API_KEY'] = 'test-key-for-mocking'
        return env
    
    def run_cli_command(self, args, env, cwd=None):
        """Helper to run CLI commands in-process using cli.main(argv).
        Returns an object with returncode, stdout, stderr.
        """
        import io
        import contextlib
        from types import SimpleNamespace
        from cli import main as cli_main
        
        stdout_buf = io.StringIO()
        env = {**env, 'CMC_SKIP_DOTENV': '1'}
        with patch.dict(os.environ, env, clear=True):
            with contextlib.redirect_stdout(stdout_buf):
                code = cli_main(args)
        return SimpleNamespace(returncode=code, stdout=stdout_buf.getvalue(), stderr="")
    
    @patch('src.causal_memory_core.CausalMemoryCore')
    def test_e2e_cli_add_event(self, mock_memory_core_class, temp_db_path, cli_env):
        """Test adding an event via CLI"""
        # Mock the memory core
        mock_instance = Mock()
        mock_memory_core_class.return_value = mock_instance
        
        # Run CLI command to add event
        result = self.run_cli_command([
            '--add', 'User clicked the save button',
            '--db-path', temp_db_path
        ], cli_env)
        
        # Verify command succeeded
        assert result.returncode == 0
        assert 'Event added:' in result.stdout
        assert 'User clicked the save button' in result.stdout
        
        # Verify memory core was called correctly
        mock_memory_core_class.assert_called_once()
        mock_instance.add_event.assert_called_once_with('User clicked the save button')
        mock_instance.close.assert_called_once()
    
    @patch('src.causal_memory_core.CausalMemoryCore')
    def test_e2e_cli_query_memory(self, mock_memory_core_class, temp_db_path, cli_env):
        """Test querying memory via CLI"""
        # Mock the memory core
        mock_instance = Mock()
        mock_instance.get_context.return_value = "Initially, User opened the application."
        mock_memory_core_class.return_value = mock_instance
        
        # Run CLI command to query
        result = self.run_cli_command([
            '--query', 'application opening',
            '--db-path', temp_db_path
        ], cli_env)
        
        # Verify command succeeded
        assert result.returncode == 0
        assert 'Context for' in result.stdout
        assert 'application opening' in result.stdout
        # Narrative now starts with 'Initially,'
        assert 'Initially,' in result.stdout
        
        # Verify memory core was called correctly
        mock_memory_core_class.assert_called_once()
        mock_instance.get_context.assert_called_once_with('application opening')
        mock_instance.close.assert_called_once()
    
    def test_e2e_cli_help(self, cli_env):
        """Test CLI help display"""
        # Capture help via parse_args(['-h']) which prints help and exits in argparse.
        # Here we simulate by importing parse_args and printing help indirectly through main with no args.
        result = self.run_cli_command([], cli_env)
        
        # Verify help is displayed
        assert result.returncode == 0
        assert 'Causal Memory Core CLI' in result.stdout or 'usage:' in result.stdout
        assert '--add' in result.stdout
        assert '--query' in result.stdout
        assert '--interactive' in result.stdout
    
    def test_e2e_cli_no_args(self, cli_env):
        """Test CLI behavior when no arguments provided"""
        result = self.run_cli_command([], cli_env)
        
        # Should display help when no args provided
        assert result.returncode == 0
        assert 'usage:' in result.stdout or 'Causal Memory Core CLI' in result.stdout
    
    @patch('src.causal_memory_core.CausalMemoryCore')
    def test_e2e_cli_error_handling(self, mock_memory_core_class, temp_db_path, cli_env):
        """Test CLI error handling"""
        # Mock the memory core to raise an exception
        mock_memory_core_class.side_effect = Exception("Database connection failed")
        
        # Run CLI command
        result = self.run_cli_command([
            '--add', 'Some event',
            '--db-path', temp_db_path
        ], cli_env)
        
        # Verify error is handled gracefully
        assert result.returncode == 1
        assert 'Error initializing memory core' in result.stdout or 'Error initializing memory core' in result.stderr
    
    def test_e2e_cli_missing_api_key(self, temp_db_path):
        """Test CLI behavior when OpenAI API key is missing"""
        env = os.environ.copy()
        # Remove API key
        if 'OPENAI_API_KEY' in env:
            del env['OPENAI_API_KEY']
        
        result = self.run_cli_command([
            '--add', 'Some event'
        ], env)
        
        # Should fail with API key error
        assert result.returncode == 1
        assert 'OPENAI_API_KEY not found' in result.stdout or 'OPENAI_API_KEY not found' in result.stderr
    
    @patch('src.causal_memory_core.CausalMemoryCore')
    @patch('builtins.input')
    def test_e2e_cli_interactive_mode(self, mock_input, mock_memory_core_class, temp_db_path, cli_env):
        """Test interactive mode workflow"""
        # Mock the memory core
        mock_instance = Mock()
        mock_instance.get_context.return_value = "Found relevant context"
        mock_memory_core_class.return_value = mock_instance
        
        # Mock user input sequence
        mock_input.side_effect = [
            'add User started the application',
            'query application startup',
            'help',
            'quit'
        ]
        
        # Run interactive mode
        result = self.run_cli_command([
            '--interactive',
            '--db-path', temp_db_path
        ], cli_env)
        
        # Verify interactive mode started
        assert result.returncode == 0
        assert 'Interactive Mode' in result.stdout
        
        # Verify memory core operations were called
        mock_instance.add_event.assert_called()
        mock_instance.get_context.assert_called()
    
    @patch('src.causal_memory_core.CausalMemoryCore')
    def test_e2e_cli_workflow_sequence(self, mock_memory_core_class, temp_db_path, cli_env):
        """Test a complete workflow sequence: add events -> query -> verify results"""
        # Mock the memory core with different responses
        mock_instance = Mock()
        mock_memory_core_class.return_value = mock_instance
        
        # Step 1: Add first event
        mock_instance.get_context.return_value = "No relevant context found in memory."
        
        result1 = self.run_cli_command([
            '--add', 'User opened file browser',
            '--db-path', temp_db_path
        ], cli_env)
        assert result1.returncode == 0
        assert 'Event added:' in result1.stdout
        
        # Step 2: Add second event
        result2 = self.run_cli_command([
            '--add', 'User selected a document file',
            '--db-path', temp_db_path
        ], cli_env)
        assert result2.returncode == 0
        assert 'Event added:' in result2.stdout
        
        # Step 3: Query for context
        mock_instance.get_context.return_value = "Initially: User opened file browser\\nThis led to: User selected a document file"
        
        result3 = self.run_cli_command([
            '--query', 'file selection process',
            '--db-path', temp_db_path
        ], cli_env)
        assert result3.returncode == 0
        assert 'Context for' in result3.stdout
        
        # Verify all operations were called
        assert mock_instance.add_event.call_count == 2
        mock_instance.get_context.assert_called()
    
    def test_e2e_cli_special_characters(self, temp_db_path, cli_env):
        """Test CLI handling of special characters in arguments"""
        with patch('src.causal_memory_core.CausalMemoryCore') as mock_memory_core_class:
            mock_instance = Mock()
            mock_memory_core_class.return_value = mock_instance
            
            # Test with special characters
            special_event = "User typed: Hello, World! (with symbols: @#$%^&*)"
            
            result = self.run_cli_command([
                '--add', special_event,
                '--db-path', temp_db_path
            ], cli_env)
            
            assert result.returncode == 0
            mock_instance.add_event.assert_called_once_with(special_event)
    
    def test_e2e_cli_long_arguments(self, temp_db_path, cli_env):
        """Test CLI with very long event descriptions"""
        with patch('src.causal_memory_core.CausalMemoryCore') as mock_memory_core_class:
            mock_instance = Mock()
            mock_memory_core_class.return_value = mock_instance
            
            # Create a long event description
            long_event = "User performed a very complex operation that involved " + "many different steps " * 20
            
            result = self.run_cli_command([
                '--add', long_event,
                '--db-path', temp_db_path
            ], cli_env)
            
            assert result.returncode == 0
            mock_instance.add_event.assert_called_once_with(long_event)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])