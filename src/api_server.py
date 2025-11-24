"""HTTP/REST API Server for Causal Memory Core.

Provides web and mobile access to the memory system with:
- RESTful endpoints for adding events and querying memory
- CORS support for web applications
- Health check endpoints
- OpenAPI documentation
- Authentication support (optional)
"""

from __future__ import annotations

import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .causal_memory_core import CausalMemoryCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global memory instance
memory_core: Optional[CausalMemoryCore] = None

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)


# Request/Response Models
class AddEventRequest(BaseModel):
    """Request model for adding a new event."""
    effect_text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Description of the event (max 10,000 characters)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "effect_text": "User clicked the save button"
            }
        }


class AddEventResponse(BaseModel):
    """Response model for adding an event."""
    success: bool
    message: str


class QueryRequest(BaseModel):
    """Request model for querying memory."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query (max 1,000 characters)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What happened after the user clicked save?"
            }
        }


class QueryResponse(BaseModel):
    """Response model for query results."""
    narrative: str
    success: bool


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    database_connected: bool


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global memory_core

    # Startup
    logger.info("Starting Causal Memory Core API Server...")
    try:
        db_path = os.getenv("DB_PATH", "causal_memory.db")
        memory_core = CausalMemoryCore(db_path=db_path)
        logger.info(f"Memory core initialized with database: {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize memory core: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Causal Memory Core API Server...")
    if memory_core:
        try:
            memory_core.close()
            logger.info("Memory core closed successfully")
        except Exception as e:
            logger.error(f"Error closing memory core: {e}")
            raise


# Create FastAPI application
app = FastAPI(
    title="Causal Memory Core API",
    description="REST API for accessing causal memory system across platforms",
    version="1.1.1",
    lifespan=lifespan
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for web and mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional API key authentication
def verify_api_key(x_api_key: Optional[str]):
    """Verify API key if authentication is enabled."""
    required_key = os.getenv("API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Causal Memory Core API",
        "version": "1.1.1",
        "description": "REST API for causal memory system",
        "endpoints": {
            "health": "/health",
            "add_event": "/events (POST)",
            "query": "/query (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    database_connected = memory_core is not None and memory_core.conn is not None

    return HealthResponse(
        status="healthy" if database_connected else "unhealthy",
        version="1.1.1",
        database_connected=database_connected
    )


@app.post("/events", response_model=AddEventResponse)
@limiter.limit("60/minute")  # 60 events per minute per IP
async def add_event(
    request_obj: Request,
    request: AddEventRequest,
    authenticated: Optional[str] = Header(None, include_in_schema=False, alias="x-api-key")
):
    """Add a new event to memory.

    Rate limit: 60 requests per minute per IP address.

    The system will automatically:
    1. Generate semantic embeddings
    2. Find potential causal relationships
    3. Link to previous events if causally related
    4. Store in the database
    """
    if os.getenv("API_KEY"):
        verify_api_key(authenticated)

    if not memory_core:
        raise HTTPException(status_code=503, detail="Memory core not initialized")

    try:
        logger.info(f"Adding event: {request.effect_text[:100]}...")
        memory_core.add_event(request.effect_text)
        logger.info("Event added successfully")

        return AddEventResponse(
            success=True,
            message="Event added successfully"
        )
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding event: {str(e)}")


@app.post("/query", response_model=QueryResponse)
@limiter.limit("120/minute")  # 120 queries per minute per IP
async def query_memory(
    request_obj: Request,
    request: QueryRequest,
    authenticated: Optional[str] = Header(None, include_in_schema=False, alias="x-api-key")
):
    """Query memory and retrieve causal narrative.

    Rate limit: 120 requests per minute per IP address.

    The system will:
    1. Find the most relevant event to your query
    2. Trace back through causal chains to find root causes
    3. Follow forward to find consequences
    4. Return a narrative explaining the causal story
    """
    if os.getenv("API_KEY"):
        verify_api_key(authenticated)

    if not memory_core:
        raise HTTPException(status_code=503, detail="Memory core not initialized")

    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        narrative = memory_core.query(request.query)
        logger.info("Query processed successfully")

        return QueryResponse(
            narrative=narrative,
            success=True
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/stats", response_model=dict)
async def get_stats():
    """Get memory statistics."""
    if not memory_core or not memory_core.conn:
        raise HTTPException(status_code=503, detail="Memory core not initialized")

    try:
        result = memory_core.conn.execute("SELECT COUNT(*) FROM events").fetchone()
        total_events = result[0] if result else 0

        result = memory_core.conn.execute(
            "SELECT COUNT(*) FROM events WHERE cause_id IS NOT NULL"
        ).fetchone()
        linked_events = result[0] if result else 0

        return {
            "total_events": total_events,
            "linked_events": linked_events,
            "orphan_events": total_events - linked_events
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
