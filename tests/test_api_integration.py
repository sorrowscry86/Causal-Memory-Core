import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
import sys

# Ensure root is in path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_server import app

@pytest.fixture
def client():
    """Create a test client with a real (but mocked internals) CausalMemoryCore."""

    # Patch the initialization methods to avoid external dependencies
    with patch('src.causal_memory_core.CausalMemoryCore._initialize_embedder') as mock_init_embedder, \
         patch('src.causal_memory_core.CausalMemoryCore._initialize_llm') as mock_init_llm:

        # Mock Embedder
        mock_embedder_instance = MagicMock()
        # Return a list of floats for encoding
        mock_embedder_instance.encode.return_value = [0.1] * 4
        mock_init_embedder.return_value = mock_embedder_instance

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm_instance.chat.completions.create.return_value.choices[0].message.content = "No."
        mock_init_llm.return_value = mock_llm_instance

        # Use in-memory DB
        os.environ["DB_PATH"] = ":memory:"

        with TestClient(app) as test_client:
            yield test_client

        # Cleanup
        if "DB_PATH" in os.environ:
            del os.environ["DB_PATH"]

def test_post_query_valid_request_returns_200(client):
    """POST /query with valid request returns 200 OK."""
    # First add an event
    client.post("/events", json={"effect_text": "Test event"})
    # Then query it
    response = client.post("/query", json={"query": "test"})
    assert response.status_code == 200
    assert "success" in response.json()
    assert response.json()["success"] is True

def test_post_query_returns_narrative(client):
    """POST /query response includes narrative field."""
    client.post("/events", json={"effect_text": "Test event"})
    response = client.post("/query", json={"query": "test"})
    assert "narrative" in response.json()
    assert isinstance(response.json()["narrative"], str)

def test_post_query_empty_query_returns_422(client):
    """POST /query with empty query string returns 422 (Pydantic validation)."""
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422

def test_post_query_whitespace_query_returns_400(client):
    """POST /query with whitespace-only query returns 400."""
    response = client.post("/query", json={"query": "   "})
    assert response.status_code == 400

def test_post_query_invalid_json_returns_422(client):
    """POST /query with invalid JSON returns 422."""
    response = client.post("/query", content="not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
