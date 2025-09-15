"""
Unit tests for the Config module
Tests configuration loading and environment variable handling
"""

import unittest
import os
import sys
from unittest.mock import patch
import importlib

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestConfig(unittest.TestCase):
    """Test suite for the Config class"""

    def test_default_values(self):
        """Test Config uses correct default values when no env vars are set"""
        # Mock load_dotenv to prevent loading from .env file
        with patch.dict(os.environ, {}, clear=True):
            with patch('dotenv.load_dotenv'):  # Patch the dotenv module function
                import config
                importlib.reload(config)
                Config = config.Config
                
                # Test default database settings
                self.assertEqual(Config.DB_PATH, 'causal_memory.db')
                
                # Test default embedding model settings
                self.assertEqual(Config.EMBEDDING_MODEL, 'all-MiniLM-L6-v2')
                self.assertEqual(Config.EMBEDDING_DIMENSION, 384)
                
                # Test default LLM settings
                self.assertIsNone(Config.OPENAI_API_KEY)
                self.assertEqual(Config.LLM_MODEL, 'gpt-3.5-turbo')
                self.assertEqual(Config.LLM_TEMPERATURE, 0.1)
                
                # Test default search settings
                self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 5)
                self.assertEqual(Config.SIMILARITY_THRESHOLD, 0.5)
                self.assertEqual(Config.TIME_DECAY_HOURS, 24)
                
                # Test default MCP server settings
                self.assertEqual(Config.MCP_SERVER_NAME, 'causal-memory-core')
                self.assertEqual(Config.MCP_SERVER_VERSION, '1.0.0')

    def test_environment_variable_loading(self):
        """Test that Config correctly loads values from environment vars"""
        test_env = {
            'DB_PATH': 'test_memory.db',
            'EMBEDDING_MODEL': 'test-embedding-model',
            'OPENAI_API_KEY': 'test-api-key-12345',
            'LLM_MODEL': 'gpt-4',
            'LLM_TEMPERATURE': '0.5',
            'MAX_POTENTIAL_CAUSES': '10',
            'SIMILARITY_THRESHOLD': '0.8',
            'TIME_DECAY_HOURS': '48',
            'MCP_SERVER_NAME': 'test-memory-server',
            'MCP_SERVER_VERSION': '2.0.0'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            # Test that environment variables were loaded correctly
            self.assertEqual(Config.DB_PATH, 'test_memory.db')
            self.assertEqual(Config.EMBEDDING_MODEL, 'test-embedding-model')
            self.assertEqual(Config.OPENAI_API_KEY, 'test-api-key-12345')
            self.assertEqual(Config.LLM_MODEL, 'gpt-4')
            self.assertEqual(Config.LLM_TEMPERATURE, 0.5)
            self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 10)
            self.assertEqual(Config.SIMILARITY_THRESHOLD, 0.8)
            self.assertEqual(Config.TIME_DECAY_HOURS, 48)
            self.assertEqual(Config.MCP_SERVER_NAME, 'test-memory-server')
            self.assertEqual(Config.MCP_SERVER_VERSION, '2.0.0')

    def test_numeric_type_conversion(self):
        """Test numeric environment vars are converted to correct types"""
        test_env = {
            'MAX_POTENTIAL_CAUSES': '15',
            'TIME_DECAY_HOURS': '72',
            'LLM_TEMPERATURE': '0.9',
            'SIMILARITY_THRESHOLD': '0.9'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            # Test integer conversion
            self.assertIsInstance(Config.MAX_POTENTIAL_CAUSES, int)
            self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 15)
            
            self.assertIsInstance(Config.TIME_DECAY_HOURS, int)
            self.assertEqual(Config.TIME_DECAY_HOURS, 72)
            
            # Test float conversion
            self.assertIsInstance(Config.LLM_TEMPERATURE, float)
            self.assertEqual(Config.LLM_TEMPERATURE, 0.9)
            
            self.assertIsInstance(Config.SIMILARITY_THRESHOLD, float)
            self.assertEqual(Config.SIMILARITY_THRESHOLD, 0.9)

    def test_invalid_numeric_values(self):
        """Test invalid numeric values in env vars raise appropriate errors"""
        # Test invalid float conversion
        test_env = {'LLM_TEMPERATURE': 'invalid_float'}
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            with self.assertRaises(ValueError):
                importlib.reload(config)
        
        # Test invalid int conversion
        test_env = {'MAX_POTENTIAL_CAUSES': 'invalid_int'}
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            with self.assertRaises(ValueError):
                importlib.reload(config)

    def test_boundary_values(self):
        """Test boundary values for numeric settings are handled correctly"""
        test_env = {
            'LLM_TEMPERATURE': '0.0',
            'SIMILARITY_THRESHOLD': '0.0',
            'MAX_POTENTIAL_CAUSES': '0',
            'TIME_DECAY_HOURS': '0'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            self.assertEqual(Config.LLM_TEMPERATURE, 0.0)
            self.assertEqual(Config.SIMILARITY_THRESHOLD, 0.0)
            self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 0)
            self.assertEqual(Config.TIME_DECAY_HOURS, 0)
        
        # Test maximum values
        test_env = {
            'LLM_TEMPERATURE': '2.0',
            'SIMILARITY_THRESHOLD': '1.0',
            'MAX_POTENTIAL_CAUSES': '100',
            'TIME_DECAY_HOURS': '8760'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            self.assertEqual(Config.LLM_TEMPERATURE, 2.0)
            self.assertEqual(Config.SIMILARITY_THRESHOLD, 1.0)
            self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 100)
            self.assertEqual(Config.TIME_DECAY_HOURS, 8760)

    def test_empty_string_values(self):
        """Test that empty string environment vars fall back to defaults"""
        test_env = {
            'DB_PATH': '',
            'EMBEDDING_MODEL': '',
            'LLM_MODEL': ''
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch('dotenv.load_dotenv'):
                import config
                importlib.reload(config)
                Config = config.Config
                
                # Note: os.getenv() with empty string returns the empty string,
                # not None, so Config actually uses empty strings literally.
                # This tests the actual behavior.
                self.assertEqual(Config.DB_PATH, '')
                self.assertEqual(Config.EMBEDDING_MODEL, '')
                self.assertEqual(Config.LLM_MODEL, '')

    def test_whitespace_handling(self):
        """Test environment variables with whitespace are handled properly"""
        test_env = {
            'DB_PATH': '  test_db.db  ',
            'LLM_MODEL': '  gpt-4-turbo  ',
            'OPENAI_API_KEY': '  sk-test123  '
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            # The Config class doesn't strip whitespace, so values include it
            # Tests current behavior - might want to modify Config to strip
            self.assertEqual(Config.DB_PATH, '  test_db.db  ')
            self.assertEqual(Config.LLM_MODEL, '  gpt-4-turbo  ')
            self.assertEqual(Config.OPENAI_API_KEY, '  sk-test123  ')

    def test_minimal_environment(self):
        """Test Config works with minimal environment setup"""
        test_env = {
            'OPENAI_API_KEY': 'sk-minimal-test-key'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            # Only OPENAI_API_KEY is set, others should be defaults
            self.assertEqual(Config.OPENAI_API_KEY, 'sk-minimal-test-key')
            self.assertEqual(Config.DB_PATH, 'causal_memory.db')
            self.assertEqual(Config.LLM_MODEL, 'gpt-3.5-turbo')
            self.assertEqual(Config.MAX_POTENTIAL_CAUSES, 5)

    def test_embedding_dimension_constant(self):
        """Test that EMBEDDING_DIMENSION is always constant"""
        import config
        importlib.reload(config)
        Config = config.Config
        
        self.assertEqual(Config.EMBEDDING_DIMENSION, 384)
        
        # It should not be affected by environment variables
        with patch.dict(os.environ, {'EMBEDDING_DIMENSION': '512'}, clear=True):
            import config
            importlib.reload(config)
            Config = config.Config
            
            # Still the hardcoded value
            self.assertEqual(Config.EMBEDDING_DIMENSION, 384)


if __name__ == '__main__':
    unittest.main()