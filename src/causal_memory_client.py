"""
Causal Memory Client Library
Version: 1.1.2
Author: Beatrice (via VoidCat RDC)

A production-ready Python client for interacting with the Causal Memory Core API.
Supports both synchronous and asynchronous operations via httpx.
"""

import os
import logging
from typing import Optional, Dict, Any, List

import httpx
from pydantic import BaseModel, Field

# Configure logging - allowing external configuration
logger = logging.getLogger("causal-memory-client")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Data Models ---

class EventRequest(BaseModel):
    """Payload for adding an event."""
    effect_text: str = Field(..., description="Description of the event/effect to record")

class EventResponse(BaseModel):
    """Response after adding an event."""
    status: str
    event_id: str
    timestamp: str
    causal_links_detected: int = 0

class QueryRequest(BaseModel):
    """Payload for querying context."""
    query: str = Field(..., description="The topic or question to investigate")

class QueryResponse(BaseModel):
    """Response containing causal narrative."""
    query: str
    narrative: str
    related_events: List[Dict[str, Any]] = []

# --- Synchronous Client Implementation ---

class CausalMemoryClient:
    """
    Synchronous client for the Causal Memory Core REST API.
    """

    DEFAULT_URL = "https://causal-memory-core-production.up.railway.app"

    def __init__(
        self, 
        base_url: Optional[str] = None, 
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        Initialize the client.
        
        Args:
            base_url: API endpoint (defaults to Railway production URL or CMC_API_URL env var)
            api_key: Optional authentication token (if configured on server)
            timeout: Request timeout in seconds
        """
        self.base_url = (
            base_url 
            or os.getenv("CMC_API_URL") 
            or self.DEFAULT_URL
        ).rstrip("/")
        
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        self.timeout = timeout
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VoidCat-CMC-Client/1.1.2"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )
        
        logger.debug(f"Causal Memory Client initialized against {self.base_url}")

    def check_health(self) -> Dict[str, Any]:
        """Check if the API is alive."""
        try:
            response = self.client.get("/")
            # Handle plain text response from Railway or JSON
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("text/plain"):
                    return {"status": "healthy", "message": response.text}
                return response.json()
            response.raise_for_status()
            return {"status": "unknown"}
        except httpx.HTTPError as e:
            logger.error(f"Health check failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def add_event(self, text: str) -> EventResponse:
        """Record a new event in the memory core."""
        if not text or not text.strip():
            raise ValueError("Event text cannot be empty.")

        payload = EventRequest(effect_text=text).model_dump()
        
        try:
            # Assumes REST endpoints exposed by the server
            response = self.client.post("/events", json=payload)
            response.raise_for_status()
            data = response.json()
            return EventResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to add event: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def query(self, query_text: str) -> QueryResponse:
        """Retrieve causal context for a given query."""
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty.")

        payload = QueryRequest(query=query_text).model_dump()
        
        try:
            response = self.client.post("/query", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return QueryResponse(
                query=data.get("query", query_text),
                narrative=data.get("context") or data.get("narrative", "No context found."),
                related_events=data.get("related_events", [])
            )
        except httpx.HTTPError as e:
            logger.error(f"Query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


# --- Asynchronous Client Implementation ---

class AsyncCausalMemoryClient:
    """
    Asynchronous client for the Causal Memory Core REST API.
    """

    DEFAULT_URL = CausalMemoryClient.DEFAULT_URL

    def __init__(
        self, 
        base_url: Optional[str] = None, 
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        Initialize the async client.
        
        Args:
            base_url: API endpoint (defaults to Railway production URL or CMC_API_URL env var)
            api_key: Optional authentication token (if configured on server)
            timeout: Request timeout in seconds
        """
        self.base_url = (
            base_url 
            or os.getenv("CMC_API_URL") 
            or self.DEFAULT_URL
        ).rstrip("/")
        
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        self.timeout = timeout
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VoidCat-CMC-AsyncClient/1.1.2"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )
        
        logger.debug(f"Async Causal Memory Client initialized against {self.base_url}")

    async def check_health(self) -> Dict[str, Any]:
        """Check if the API is alive asynchronously."""
        try:
            response = await self.client.get("/")
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("text/plain"):
                    return {"status": "healthy", "message": response.text}
                return response.json()
            response.raise_for_status()
            return {"status": "unknown"}
        except httpx.HTTPError as e:
            logger.error(f"Async health check failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    async def add_event(self, text: str) -> EventResponse:
        """Record a new event asynchronously."""
        if not text or not text.strip():
            raise ValueError("Event text cannot be empty.")

        payload = EventRequest(effect_text=text).model_dump()
        
        try:
            response = await self.client.post("/events", json=payload)
            response.raise_for_status()
            data = response.json()
            return EventResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Async failed to add event: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    async def query(self, query_text: str) -> QueryResponse:
        """Retrieve causal context asynchronously."""
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty.")

        payload = QueryRequest(query=query_text).model_dump()
        
        try:
            response = await self.client.post("/query", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return QueryResponse(
                query=data.get("query", query_text),
                narrative=data.get("context") or data.get("narrative", "No context found."),
                related_events=data.get("related_events", [])
            )
        except httpx.HTTPError as e:
            logger.error(f"Async query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
