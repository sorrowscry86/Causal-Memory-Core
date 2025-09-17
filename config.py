import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the Causal Memory Core"""
    
    # Database settings
    DB_PATH = os.getenv('DB_PATH', 'causal_memory.db')
    
    # Embedding model settings
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2
    
    # LLM settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    
    # Search settings
    MAX_POTENTIAL_CAUSES = int(os.getenv('MAX_POTENTIAL_CAUSES', '5'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.5'))
    TIME_DECAY_HOURS = int(os.getenv('TIME_DECAY_HOURS', '24'))
    
    # MCP Server settings
    MCP_SERVER_NAME = os.getenv('MCP_SERVER_NAME', 'causal-memory-core')
    MCP_SERVER_VERSION = os.getenv('MCP_SERVER_VERSION', '1.1.1')

    # Preprocessor settings (Week 1 - pass-through)
    # Feature flag to enable the semantic query preprocessing layer
    PREPROCESSOR_ENABLED = os.getenv('PREPROCESSOR_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    # Fail-open behavior: on any preprocessor error, fall back to direct core access
    PREPROCESSOR_FAIL_OPEN = os.getenv('PREPROCESSOR_FAIL_OPEN', 'true').lower() in ('1', 'true', 'yes')
    # Minimum confidence to apply semantic translation (Week 2)
    PREPROCESSOR_CONFIDENCE_THRESHOLD = float(os.getenv('PREPROCESSOR_CONFIDENCE_THRESHOLD', '0.6'))
    # Enable debug tool exposure in MCP to inspect metrics (disabled by default)
    PREPROCESSOR_DEBUG_ENABLED = os.getenv('PREPROCESSOR_DEBUG_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    # Limit for recent translations stored in memory
    PREPROCESSOR_METRICS_RECENT_LIMIT = int(os.getenv('PREPROCESSOR_METRICS_RECENT_LIMIT', '50'))

    # Week 3 skeleton: suggestions (disabled by default)
    PREPROCESSOR_SUGGESTIONS_ENABLED = os.getenv('PREPROCESSOR_SUGGESTIONS_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    PREPROCESSOR_SUGGESTION_TOP_K = int(os.getenv('PREPROCESSOR_SUGGESTION_TOP_K', '3'))
