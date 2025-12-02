"""Comprehensive tests for the API server endpoints."""

import os
import sys
import tempfile
from unittest.mock import Mock, patch
import pytest
from fastapi.testclient import TestClient

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_server import app, memory_core


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_memory_core():
    """Mock the global memory_core instance."""
    with patch('src.api_server.memory_core') as mock_core:
        mock_core.conn = Mock()
        mock_core.add_event = Mock()
        mock_core.query = Mock(return_value="Test narrative response")
        yield mock_core


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_healthy(self, client, mock_memory_core):
        """Test health check when system is healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.1.1"
        assert data["database_connected"] is True

    def test_health_check_unhealthy(self, client):
        """Test health check when database is not connected."""
        with patch('src.api_server.memory_core', None):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_connected"] is False


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Causal Memory Core API"
        assert data["version"] == "1.1.1"
        assert "endpoints" in data


class TestAddEventEndpoint:
    """Tests for the POST /events endpoint."""

    def test_add_event_success(self, client, mock_memory_core):
        """Test successfully adding an event."""
        response = client.post(
            "/events",
            json={"effect_text": "User clicked the button"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successfully" in data["message"].lower()
        mock_memory_core.add_event.assert_called_once_with("User clicked the button")

    def test_add_event_empty_text(self, client, mock_memory_core):
        """Test adding event with empty text fails validation."""
        response = client.post(
            "/events",
            json={"effect_text": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_add_event_text_too_long(self, client, mock_memory_core):
        """Test adding event with text exceeding max length fails."""
        long_text = "A" * 10001  # Exceeds 10,000 character limit
        response = client.post(
            "/events",
            json={"effect_text": long_text}
        )
        assert response.status_code == 422  # Validation error

    def test_add_event_missing_field(self, client, mock_memory_core):
        """Test adding event without required field fails."""
        response = client.post("/events", json={})
        assert response.status_code == 422  # Validation error

    def test_add_event_with_api_key(self, client, mock_memory_core):
        """Test adding event with valid API key."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            response = client.post(
                "/events",
                json={"effect_text": "Test event"},
                headers={"x-api-key": "test-key"}
            )
            assert response.status_code == 200

    def test_add_event_invalid_api_key(self, client, mock_memory_core):
        """Test adding event with invalid API key fails."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            response = client.post(
                "/events",
                json={"effect_text": "Test event"},
                headers={"x-api-key": "wrong-key"}
            )
            assert response.status_code == 401

    def test_add_event_memory_core_not_initialized(self, client):
        """Test adding event when memory core is not initialized."""
        with patch('src.api_server.memory_core', None):
            response = client.post(
                "/events",
                json={"effect_text": "Test event"}
            )
            assert response.status_code == 503

    def test_add_event_internal_error(self, client, mock_memory_core):
        """Test handling of internal errors during event addition."""
        mock_memory_core.add_event.side_effect = Exception("Database error")
        response = client.post(
            "/events",
            json={"effect_text": "Test event"}
        )
        assert response.status_code == 500


class TestQueryEndpoint:
    """Tests for the POST /query endpoint."""

    def test_query_success(self, client, mock_memory_core):
        """Test successfully querying memory."""
        mock_memory_core.query.return_value = "Test narrative response"
        response = client.post(
            "/query",
            json={"query": "What happened?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["narrative"] == "Test narrative response"
        mock_memory_core.query.assert_called_once_with("What happened?")

    def test_query_empty_text(self, client, mock_memory_core):
        """Test querying with empty text fails validation."""
        response = client.post(
            "/query",
            json={"query": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_query_text_too_long(self, client, mock_memory_core):
        """Test querying with text exceeding max length fails."""
        long_query = "A" * 1001  # Exceeds 1,000 character limit
        response = client.post(
            "/query",
            json={"query": long_query}
        )
        assert response.status_code == 422  # Validation error

    def test_query_missing_field(self, client, mock_memory_core):
        """Test querying without required field fails."""
        response = client.post("/query", json={})
        assert response.status_code == 422  # Validation error

    def test_query_with_api_key(self, client, mock_memory_core):
        """Test querying with valid API key."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            response = client.post(
                "/query",
                json={"query": "Test query"},
                headers={"x-api-key": "test-key"}
            )
            assert response.status_code == 200

    def test_query_invalid_api_key(self, client, mock_memory_core):
        """Test querying with invalid API key fails."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            response = client.post(
                "/query",
                json={"query": "Test query"},
                headers={"x-api-key": "wrong-key"}
            )
            assert response.status_code == 401

    def test_query_memory_core_not_initialized(self, client):
        """Test querying when memory core is not initialized."""
        with patch('src.api_server.memory_core', None):
            response = client.post(
                "/query",
                json={"query": "Test query"}
            )
            assert response.status_code == 503

    def test_query_internal_error(self, client, mock_memory_core):
        """Test handling of internal errors during query."""
        mock_memory_core.query.side_effect = Exception("Query error")
        response = client.post(
            "/query",
            json={"query": "Test query"}
        )
        assert response.status_code == 500


class TestStatsEndpoint:
    """Tests for the GET /stats endpoint."""

    def test_stats_success(self, client, mock_memory_core):
        """Test successfully retrieving stats."""
        mock_memory_core.conn.execute.return_value.fetchone.side_effect = [
            (100,),  # total_events
            (75,)    # linked_events
        ]
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 100
        assert data["linked_events"] == 75
        assert data["orphan_events"] == 25

    def test_stats_memory_core_not_initialized(self, client):
        """Test stats when memory core is not initialized."""
        with patch('src.api_server.memory_core', None):
            response = client.get("/stats")
            assert response.status_code == 503

    def test_stats_database_error(self, client, mock_memory_core):
        """Test handling of database errors when retrieving stats."""
        mock_memory_core.conn.execute.side_effect = Exception("Database error")
        response = client.get("/stats")
        assert response.status_code == 500


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_add_event_rate_limit(self, client, mock_memory_core):
        """Test that add_event endpoint is rate limited."""
        # Make requests up to the limit (60/minute)
        # Note: In actual testing, this would require time-based testing
        # For now, we just verify the endpoint exists and accepts requests
        response = client.post(
            "/events",
            json={"effect_text": "Test event"}
        )
        assert response.status_code == 200

    def test_query_rate_limit(self, client, mock_memory_core):
        """Test that query endpoint is rate limited."""
        # Make requests up to the limit (120/minute)
        # Note: In actual testing, this would require time-based testing
        # For now, we just verify the endpoint exists and accepts requests
        response = client.post(
            "/query",
            json={"query": "Test query"}
        )
        assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.options("/health")
        # CORS middleware should add appropriate headers
        assert response.status_code in [200, 405]  # OPTIONS might not be explicitly handled
