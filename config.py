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
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    
    # Search settings
    MAX_POTENTIAL_CAUSES = int(os.getenv('MAX_POTENTIAL_CAUSES', '5'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.5'))
    TIME_DECAY_HOURS = int(os.getenv('TIME_DECAY_HOURS', '24'))

    # Narrative chain settings
    MAX_CONSEQUENCE_DEPTH = int(os.getenv('MAX_CONSEQUENCE_DEPTH', '2'))

    # MCP Server settings
    MCP_SERVER_NAME = os.getenv('MCP_SERVER_NAME', 'causal-memory-core')
    MCP_SERVER_VERSION = os.getenv('MCP_SERVER_VERSION', '1.1.1')
