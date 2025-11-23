import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from contextlib import asynccontextmanager

# This import will be patched, so it's okay that it's not a real module
from src.api_server import app, lifespan
from src.causal_memory_core import CausalMemoryCore


@pytest.fixture
def mock_memory_core():
    """Fixture to create a mock CausalMemoryCore instance."""
    mock = MagicMock(spec=CausalMemoryCore)
    mock.conn = MagicMock()
    return mock


@pytest.fixture
def client(mock_memory_core):
    """Fixture to create a TestClient with a mocked CausalMemoryCore."""

    @asynccontextmanager
    async def override_lifespan(app):
        """Override lifespan manager to inject the mock."""
        from src import api_server
        api_server.memory_core = mock_memory_core
        yield
        api_server.memory_core = None

    app.router.lifespan_context = override_lifespan

    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["name"] == "Causal Memory Core API"
    assert "version" in json_response
    assert "endpoints" in json_response


def test_health_check_healthy(client):
    """Test the health check endpoint when the database is connected."""
    response = client.get("/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["database_connected"] is True


def test_health_check_unhealthy(mock_memory_core):
    """Test the health check endpoint when the database is not connected."""
    mock_memory_core.conn = None

    @asynccontextmanager
    async def override_lifespan(app):
        from src import api_server
        api_server.memory_core = mock_memory_core
        yield
        api_server.memory_core = None

    app.router.lifespan_context = override_lifespan

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["status"] == "unhealthy"
        assert json_response["database_connected"] is False


def test_add_event_success(client, mock_memory_core):
    """Test successful event addition."""
    response = client.post("/events", json={"effect_text": "Test event"})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert json_response["message"] == "Event added successfully"
    mock_memory_core.add_event.assert_called_once_with("Test event")


def test_add_event_no_memory_core(client):
    """Test adding an event when the memory core is not initialized."""
    with patch("src.api_server.memory_core", None):
        response = client.post("/events", json={"effect_text": "Test event"})
        assert response.status_code == 503
        assert response.json()["detail"] == "Memory core not initialized"


def test_add_event_error(client, mock_memory_core):
    """Test error handling when adding an event."""
    mock_memory_core.add_event.side_effect = Exception("Test error")
    response = client.post("/events", json={"effect_text": "Test event"})
    assert response.status_code == 500
    assert "Error adding event" in response.json()["detail"]


@patch.dict(os.environ, {"API_KEY": "test-key"})
def test_add_event_with_auth_success(client, mock_memory_core):
    """Test successful event addition with API key authentication."""
    response = client.post(
        "/events",
        json={"effect_text": "Test event"},
        headers={"x-api-key": "test-key"},
    )
    assert response.status_code == 200
    mock_memory_core.add_event.assert_called_once_with("Test event")


@patch.dict(os.environ, {"API_KEY": "test-key"})
def test_add_event_with_auth_failure(client):
    """Test failed event addition with incorrect API key."""
    response = client.post(
        "/events",
        json={"effect_text": "Test event"},
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401


@patch("src.api_server.CausalMemoryCore")
@pytest.mark.asyncio
async def test_lifespan_startup_error(mock_causal_memory_core):
    """Test the lifespan context manager with a startup error."""
    mock_causal_memory_core.side_effect = Exception("Test error")
    with pytest.raises(Exception, match="Test error"):
        async with lifespan(app):
            pass


@patch("src.api_server.CausalMemoryCore")
@pytest.mark.asyncio
async def test_lifespan_shutdown_error(mock_causal_memory_core):
    """Test the lifespan context manager with a shutdown error."""
    mock_instance = MagicMock()
    mock_instance.close.side_effect = Exception("Test error")
    mock_causal_memory_core.return_value = mock_instance
    with pytest.raises(Exception, match="Test error"):
        async with lifespan(app):
            pass

@patch("src.api_server.CausalMemoryCore")
@pytest.mark.asyncio
async def test_lifespan_shutdown_success(mock_causal_memory_core):
    """Test the lifespan context manager with a successful shutdown."""
    mock_instance = MagicMock()
    mock_causal_memory_core.return_value = mock_instance
    async with lifespan(app):
        pass
    mock_instance.close.assert_called_once()


@patch("src.api_server.uvicorn.run")
def test_main_run(mock_uvicorn_run):
    """Test the main run block."""
    import runpy
    import sys

    # Run the module and capture the globals
    module_globals = runpy.run_module("src.api_server", run_name="__main__")

    # Get the app object from the module's globals
    app = module_globals["app"]

    mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", port=8000)


def test_get_stats_success(client, mock_memory_core):
    """Test successful retrieval of memory statistics."""
    mock_memory_core.conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(10,))),
        MagicMock(fetchone=MagicMock(return_value=(5,))),
    ]
    response = client.get("/stats")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["total_events"] == 10
    assert json_response["linked_events"] == 5
    assert json_response["orphan_events"] == 5


def test_get_stats_no_memory_core(client):
    """Test getting stats when the memory core is not initialized."""
    with patch("src.api_server.memory_core", None):
        response = client.get("/stats")
        assert response.status_code == 503
        assert response.json()["detail"] == "Memory core not initialized"


def test_get_stats_error(client, mock_memory_core):
    """Test error handling when getting stats."""
    mock_memory_core.conn.execute.side_effect = Exception("Test error")
    response = client.get("/stats")
    assert response.status_code == 500
    assert "Error getting stats" in response.json()["detail"]


def test_query_memory_success(client, mock_memory_core):
    """Test successful memory query."""
    mock_memory_core.query.return_value = "Test narrative"
    response = client.post("/query", json={"query": "Test query"})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert json_response["narrative"] == "Test narrative"
    mock_memory_core.query.assert_called_once_with("Test query")


def test_query_memory_no_memory_core(client):
    """Test querying memory when the memory core is not initialized."""
    with patch("src.api_server.memory_core", None):
        response = client.post("/query", json={"query": "Test query"})
        assert response.status_code == 503
        assert response.json()["detail"] == "Memory core not initialized"


def test_query_memory_error(client, mock_memory_core):
    """Test error handling when querying memory."""
    mock_memory_core.query.side_effect = Exception("Test error")
    response = client.post("/query", json={"query": "Test query"})
    assert response.status_code == 500
    assert "Error processing query" in response.json()["detail"]


@patch.dict(os.environ, {"API_KEY": "test-key"})
def test_query_memory_with_auth_success(client, mock_memory_core):
    """Test successful memory query with API key authentication."""
    mock_memory_core.query.return_value = "Test narrative"
    response = client.post(
        "/query",
        json={"query": "Test query"},
        headers={"x-api-key": "test-key"},
    )
    assert response.status_code == 200
    mock_memory_core.query.assert_called_once_with("Test query")


@patch.dict(os.environ, {"API_KEY": "test-key"})
def test_query_memory_with_auth_failure(client):
    """Test failed memory query with incorrect API key."""
    response = client.post(
        "/query",
        json={"query": "Test query"},
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401
