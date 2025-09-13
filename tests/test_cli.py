"""
Unit tests for the CLI module
"""

import unittest
import tempfile
import os
import sys
import io
import argparse
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import cli
from src.causal_memory_core import CausalMemoryCore


class TestCLI(unittest.TestCase):
    """Test suite for the CLI functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary database path
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        # Remove the empty file, let DuckDB create it
        os.unlink(self.temp_db_path)
        
        # Mock memory core for testing
        self.mock_memory_core = Mock(spec=CausalMemoryCore)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up the temporary database
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_add_event_command_success(self):
        """Test successful event addition through CLI command"""
        # Redirect stdout to capture output
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.add_event_command(self.mock_memory_core, "Test event")
        
        # Verify memory core was called
        self.mock_memory_core.add_event.assert_called_once_with("Test event")
        
        # Verify output
        output = captured_output.getvalue()
        self.assertIn("✅ Event added: Test event", output)

    def test_add_event_command_error(self):
        """Test error handling in add_event_command"""
        # Configure mock to raise an exception
        error_msg = "Database error"
        self.mock_memory_core.add_event.side_effect = Exception(error_msg)
        
        # Redirect stdout to capture output
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.add_event_command(self.mock_memory_core, "Test event")
        
        # Verify error message
        output = captured_output.getvalue()
        self.assertIn("❌ Error adding event: Database error", output)

    def test_query_command_success(self):
        """Test successful query through CLI command"""
        # Configure mock to return test context
        test_context = ("Initially: User clicked a button → "
                       "This led to: File opened")
        self.mock_memory_core.get_context.return_value = test_context
        
        # Redirect stdout to capture output
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.query_command(self.mock_memory_core, "How did the file open?")
        
        # Verify memory core was called
        expected_query = "How did the file open?"
        self.mock_memory_core.get_context.assert_called_once_with(expected_query)
        
        # Verify output
        output = captured_output.getvalue()
        self.assertIn("📖 Context for 'How did the file open?':", output)
        self.assertIn(test_context, output)

    def test_query_command_error(self):
        """Test error handling in query_command"""
        # Configure mock to raise an exception
        error_msg = "Query error"
        self.mock_memory_core.get_context.side_effect = Exception(error_msg)
        
        # Redirect stdout to capture output
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.query_command(self.mock_memory_core, "test query")
        
        # Verify error message
        output = captured_output.getvalue()
        self.assertIn("❌ Error querying memory: Query error", output)

    @patch('builtins.input')
    def test_interactive_mode_add_command(self, mock_input):
        """Test add command in interactive mode"""
        # Simulate user input sequence: add command, then quit
        mock_input.side_effect = ["add Test interactive event", "quit"]
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify add_event was called
        expected_event = "Test interactive event"
        self.mock_memory_core.add_event.assert_called_once_with(expected_event)
        
        # Verify welcome message was displayed
        output = captured_output.getvalue()
        self.assertIn("🧠 Causal Memory Core - Interactive Mode", output)

    @patch('builtins.input')
    def test_interactive_mode_query_command(self, mock_input):
        """Test query command in interactive mode"""
        # Configure mock to return test context
        test_context = "Test context response"
        self.mock_memory_core.get_context.return_value = test_context
        
        # Simulate user input sequence: query command, then quit
        mock_input.side_effect = ["query test query", "quit"]
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify get_context was called
        self.mock_memory_core.get_context.assert_called_once_with("test query")
        
        # Verify output contains context
        output = captured_output.getvalue()
        self.assertIn(test_context, output)

    @patch('builtins.input')
    def test_interactive_mode_help_command(self, mock_input):
        """Test help command in interactive mode"""
        # Simulate user input: help command, then quit
        mock_input.side_effect = ["help", "quit"]
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify help text is displayed
        output = captured_output.getvalue()
        self.assertIn("Commands:", output)
        self.assertIn("add <event>", output)
        self.assertIn("query <text>", output)

    @patch('builtins.input')
    def test_interactive_mode_empty_input(self, mock_input):
        """Test handling of empty input in interactive mode"""
        # Simulate user input: empty string, then quit
        mock_input.side_effect = ["", "   ", "quit"]
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify no commands were executed (only quit)
        self.mock_memory_core.add_event.assert_not_called()
        self.mock_memory_core.get_context.assert_not_called()

    @patch('builtins.input')
    def test_interactive_mode_invalid_command(self, mock_input):
        """Test handling of invalid commands in interactive mode"""
        # Simulate user input: invalid command, then quit
        mock_input.side_effect = ["invalid command", "add", "query", "quit"]
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify error messages are displayed
        output = captured_output.getvalue()
        self.assertIn("❌ Invalid command", output)

    @patch('builtins.input')
    def test_interactive_mode_keyboard_interrupt(self, mock_input):
        """Test handling of KeyboardInterrupt (Ctrl+C) in interactive mode"""
        # Simulate KeyboardInterrupt
        mock_input.side_effect = KeyboardInterrupt()
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify goodbye message
        output = captured_output.getvalue()
        self.assertIn("👋 Goodbye!", output)

    @patch('builtins.input')
    def test_interactive_mode_eof_error(self, mock_input):
        """Test handling of EOFError in interactive mode"""
        # Simulate EOFError
        mock_input.side_effect = EOFError()
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify goodbye message
        output = captured_output.getvalue()
        self.assertIn("👋 Goodbye!", output)

    @patch('builtins.input')
    def test_interactive_mode_case_insensitive_commands(self, mock_input):
        """Test that interactive commands are case insensitive"""
        # Test various case combinations
        mock_input.side_effect = [
            "ADD test event 1",
            "Query test query 1",
            "HELP",
            "H",
            "QUIT"
        ]
        
        # Configure mock
        self.mock_memory_core.get_context.return_value = "test response"
        
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            cli.interactive_mode(self.mock_memory_core)
        
        # Verify commands were executed despite case differences
        self.mock_memory_core.add_event.assert_called_once_with("test event 1")
        expected_query = "test query 1"
        self.mock_memory_core.get_context.assert_called_once_with(expected_query)
        
        # Verify help was shown
        output = captured_output.getvalue()
        self.assertIn("Commands:", output)

    @patch('builtins.input')
    def test_interactive_mode_quit_aliases(self, mock_input):
        """Test that all quit aliases work in interactive mode"""
        quit_commands = ["quit", "exit", "q"]
        
        for quit_cmd in quit_commands:
            mock_input.side_effect = [quit_cmd]
            
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.interactive_mode(self.mock_memory_core)
            
            # Should exit cleanly without error messages
            output = captured_output.getvalue()
            self.assertNotIn("❌", output)

    def test_argument_parser_setup(self):
        """Test that the argument parser is set up correctly"""
        # Create parser like in main()
        parser = argparse.ArgumentParser(
            description="Causal Memory Core CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument('--add', '-a', help='Add an event to memory')
        parser.add_argument('--query', '-q', help='Query memory for context')
        parser.add_argument('--interactive', '-i', action='store_true',
                           help='Run in interactive mode')
        db_help = 'Path to database file (overrides config)'
        parser.add_argument('--db-path', help=db_help)
        
        # Test parsing various argument combinations
        args = parser.parse_args(['--add', 'test event'])
        self.assertEqual(args.add, 'test event')
        self.assertIsNone(args.query)
        self.assertFalse(args.interactive)
        
        args = parser.parse_args(['-q', 'test query'])
        self.assertEqual(args.query, 'test query')
        self.assertIsNone(args.add)
        
        args = parser.parse_args(['--interactive'])
        self.assertTrue(args.interactive)
        
        args = parser.parse_args(['--db-path', 'custom.db'])
        self.assertEqual(args.db_path, 'custom.db')

    @patch.dict('os.environ', {}, clear=True)
    @patch('cli.load_dotenv')  # Mock load_dotenv to prevent loading .env file
    @patch('sys.exit')
    @patch('cli.CausalMemoryCore')
    def test_main_missing_api_key(self, mock_memory_core_class, mock_exit, mock_load_dotenv):
        """Test main function behavior when API key is missing"""
        # Make sys.exit raise SystemExit for testing
        mock_exit.side_effect = SystemExit(1)
        
        # Simulate missing API key
        with patch('sys.argv', ['cli.py', '--add', 'test event']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                with self.assertRaises(SystemExit):
                    cli.main()
        
        # Verify error message and exit
        output = captured_output.getvalue()
        self.assertIn("❌ Error: OPENAI_API_KEY not found", output)
        mock_exit.assert_called_with(1)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('sys.exit')
    @patch('cli.CausalMemoryCore')
    def test_main_memory_core_init_error(self, mock_memory_core_class,
                                        mock_exit):
        """Test main function behavior when memory core initialization fails"""
        # Configure mock to raise exception
        mock_memory_core_class.side_effect = Exception("Init error")
        
        # Make sys.exit raise SystemExit for testing
        mock_exit.side_effect = SystemExit(1)
        
        with patch('sys.argv', ['cli.py', '--add', 'test event']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                with self.assertRaises(SystemExit):
                    cli.main()
        
        # Verify error message and exit
        output = captured_output.getvalue()
        self.assertIn("❌ Error initializing memory core: Init error", output)
        mock_exit.assert_called_with(1)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    def test_main_add_event_flow(self, mock_memory_core_class):
        """Test complete main function flow for add event"""
        mock_memory_instance = Mock()
        mock_memory_core_class.return_value = mock_memory_instance
        
        with patch('sys.argv', ['cli.py', '--add', 'Test CLI event']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify initialization and event addition
        mock_memory_core_class.assert_called_once_with(db_path=None)
        expected_event = 'Test CLI event'
        mock_memory_instance.add_event.assert_called_once_with(expected_event)
        mock_memory_instance.close.assert_called_once()
        
        output = captured_output.getvalue()
        self.assertIn("✅ Causal Memory Core initialized", output)
        self.assertIn("✅ Event added: Test CLI event", output)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    def test_main_query_flow(self, mock_memory_core_class):
        """Test complete main function flow for query"""
        mock_memory_instance = Mock()
        mock_memory_instance.get_context.return_value = "Test context response"
        mock_memory_core_class.return_value = mock_memory_instance
        
        with patch('sys.argv', ['cli.py', '--query', 'Test query']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify initialization and query
        mock_memory_core_class.assert_called_once_with(db_path=None)
        mock_memory_instance.get_context.assert_called_once_with('Test query')
        mock_memory_instance.close.assert_called_once()
        
        output = captured_output.getvalue()
        self.assertIn("📖 Context for 'Test query':", output)
        self.assertIn("Test context response", output)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    @patch('builtins.input')
    def test_main_interactive_flow(self, mock_input, mock_memory_core_class):
        """Test complete main function flow for interactive mode"""
        mock_memory_instance = Mock()
        mock_memory_core_class.return_value = mock_memory_instance
        mock_input.side_effect = ['quit']
        
        with patch('sys.argv', ['cli.py', '--interactive']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify initialization and cleanup
        mock_memory_core_class.assert_called_once_with(db_path=None)
        mock_memory_instance.close.assert_called_once()
        
        output = captured_output.getvalue()
        self.assertIn("🧠 Causal Memory Core - Interactive Mode", output)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    def test_main_custom_db_path(self, mock_memory_core_class):
        """Test main function with custom database path"""
        mock_memory_instance = Mock()
        mock_memory_core_class.return_value = mock_memory_instance
        
        test_argv = ['cli.py', '--db-path', 'custom.db', '--add', 'test']
        with patch('sys.argv', test_argv):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify custom db path was used
        mock_memory_core_class.assert_called_once_with(db_path='custom.db')

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    def test_main_no_command_shows_help(self, mock_memory_core_class):
        """Test that main shows help when no command is provided"""
        mock_memory_instance = Mock()
        mock_memory_core_class.return_value = mock_memory_instance
        
        with patch('sys.argv', ['cli.py']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify help is displayed
        output = captured_output.getvalue()
        self.assertIn("usage:", output)
        self.assertIn("Causal Memory Core CLI", output)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('cli.CausalMemoryCore')
    def test_main_cleanup_on_exception(self, mock_memory_core_class):
        """Test that memory core is properly closed even if an exception occurs"""
        mock_memory_instance = Mock()
        mock_memory_instance.add_event.side_effect = Exception("Test error")
        mock_memory_core_class.return_value = mock_memory_instance
        
        with patch('sys.argv', ['cli.py', '--add', 'test event']):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                cli.main()
        
        # Verify cleanup still occurred
        mock_memory_instance.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()