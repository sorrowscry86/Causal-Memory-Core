# 📚 Causal Memory Core API Documentation

## 🎯 Overview

The Causal Memory Core API provides a comprehensive interface for storing, retrieving, and analyzing causal relationships between events. This document covers all public APIs, including the Python SDK, REST API, and MCP integration.

## 🐍 Python SDK

### Core Classes

#### CausalMemoryCore

The main interface for interacting with the memory system.

```python
from src.memory_core import CausalMemoryCore, MemoryConfig

# Initialize with default configuration
memory = CausalMemoryCore()

# Initialize with custom configuration
config = MemoryConfig(
    database_path="custom_memory.db",
    openai_model="gpt-4",
    causal_threshold=0.8
)
memory = CausalMemoryCore(config)
```

### Event Management

#### add_event()

Stores a new event and analyzes its causal relationships.

```python
def add_event(
    self,
    description: str,
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> EventID
```

**Parameters:**
- `description` (str): Human-readable description of the event
- `timestamp` (Optional[datetime]): When the event occurred (defaults to now)
- `metadata` (Optional[Dict[str, Any]]): Additional structured data

**Returns:**
- `EventID`: Unique identifier for the stored event

**Example:**
```python
# Basic event addition
event_id = memory.add_event("User logged into the system")

# Event with timestamp
from datetime import datetime
event_id = memory.add_event(
    "Database backup completed",
    timestamp=datetime(2025, 9, 15, 10, 30),
    metadata={"backup_size": "2.5GB", "duration": "5min"}
)
```

**Raises:**
- `ValueError`: If description is empty or invalid
- `StorageError`: If database operation fails
- `ProcessingError`: If causal analysis fails

#### get_event()

Retrieves a specific event by its ID.

```python
def get_event(self, event_id: EventID) -> Optional[Event]
```

**Parameters:**
- `event_id` (EventID): Unique identifier of the event

**Returns:**
- `Optional[Event]`: Event object or None if not found

**Example:**
```python
event = memory.get_event("evt_12345")
if event:
    print(f"Event: {event.description}")
    print(f"Timestamp: {event.timestamp}")
```
### Context Retrieval

#### query()

Query memory and retrieve causal narrative.

```python
def query(self, query_text: str) -> str
```

**Parameters:**
- `query_text` (str): Natural language query about context

**Returns:**
- `str`: Narrative string explaining the causal chain leading to the most relevant event.

**Example:**
```python
# Basic context query
narrative = memory.query("user authentication issues")

print(narrative)
# Output: "Initially, User login failed. This led to Account locked."
```

#### get_context()

Backward compatibility wrapper for query().

```python
def get_context(self, query_text: str) -> str
```

**Parameters:**
- `query_text` (str): Natural language query about context

**Returns:**
- `str`: Narrative explaining causal chain (same as query())

#### search_events()

Performs semantic search across stored events.

```python
def search_events(
    self,
    query: str,
    limit: int = 10,
    similarity_threshold: float = 0.7,
    include_metadata: bool = False
) -> List[SearchResult]
```

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum number of results
- `similarity_threshold` (float): Minimum similarity score (0.0-1.0)
- `include_metadata` (bool): Include event metadata in results

**Returns:**
- `List[SearchResult]`: List of matching events with similarity scores

**Example:**
```python
# Basic search
results = memory.search_events("login failures")

# Advanced search with high precision
results = memory.search_events(
    "authentication timeout",
    limit=5,
    similarity_threshold=0.9,
    include_metadata=True
)

for result in results:
    print(f"Event: {result.event.description}")
    print(f"Similarity: {result.similarity_score:.2f}")
```

### Causal Analysis

#### analyze_causality()

Analyzes causal relationships between specific events.

```python
def analyze_causality(
    self,
    source_event_id: EventID,
    target_event_id: EventID
) -> Optional[CausalRelationship]
```

**Parameters:**
- `source_event_id` (EventID): ID of the potential cause event
- `target_event_id` (EventID): ID of the potential effect event

**Returns:**
- `Optional[CausalRelationship]`: Causal relationship or None

**Example:**
```python
relationship = memory.analyze_causality("evt_123", "evt_456")
if relationship:
    print(f"Relationship type: {relationship.type}")
    print(f"Confidence: {relationship.confidence:.2f}")
    print(f"Reasoning: {relationship.reasoning}")
```

#### get_causal_chain()

Retrieves the complete causal chain for an event.

```python
def get_causal_chain(
    self,
    event_id: EventID,
    direction: str = "both",
    max_depth: int = 5
) -> CausalChain
```

**Parameters:**
- `event_id` (EventID): Starting event ID
- `direction` (str): "backward", "forward", or "both"
- `max_depth` (int): Maximum traversal depth

**Returns:**
- `CausalChain`: Complete causal chain with relationships

**Example:**
```python
chain = memory.get_causal_chain(
    "evt_123",
    direction="backward",
    max_depth=3
)

print(f"Root causes: {len(chain.root_events)}")
print(f"Total relationships: {len(chain.relationships)}")
```
## 🌐 REST API

The REST API provides HTTP access to core functionality.

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication

```http
Authorization: Bearer your-api-key
Content-Type: application/json
```

### Endpoints

#### POST /events

Create a new event.

**Request:**
```json
{
  "description": "User completed registration",
  "timestamp": "2025-09-15T10:30:00Z",
  "metadata": {
    "user_id": "user_123",
    "source": "web_app"
  }
}
```

**Response:**
```json
{
  "event_id": "evt_789",
  "status": "created",
  "causal_links_detected": 2
}
```

#### GET /events/{event_id}

Retrieve a specific event.

**Response:**
```json
{
  "event_id": "evt_789",
  "description": "User completed registration",
  "timestamp": "2025-09-15T10:30:00Z",
  "metadata": {
    "user_id": "user_123",
    "source": "web_app"
  },
  "causal_links": [
    {
      "related_event_id": "evt_788",
      "relationship_type": "causal_successor",
      "confidence": 0.85
    }
  ]
}
```

#### POST /query

Retrieve causal context for a query.

**Request:**
```json
{
  "query": "registration process issues"
}
```

**Response:**
```json
{
  "narrative": "Initially, User completed registration...",
  "success": true
}
```

#### POST /search

Search events semantically.

**Request:**
```json
{
  "query": "authentication failures",
  "limit": 10,
  "similarity_threshold": 0.7,
  "include_metadata": true
}
```

**Response:**
```json
{
  "results": [
    {
      "event": {
        "event_id": "evt_456",
        "description": "Login attempt failed for user",
        "timestamp": "2025-09-15T09:15:00Z"
      },
      "similarity_score": 0.89,
      "rank": 1
    }
  ],
  "total_results": 1,
  "query_time_ms": 156
}
```
## 🔌 MCP Integration

The Model Context Protocol integration allows seamless use with compatible AI systems.

### MCP Server Setup

```bash
# Start MCP server
python src/mcp_server.py --port 8080 --host localhost
```

### Available Tools

#### add_event

Store a new event in the memory system.

**Schema:**
```json
{
  "name": "add_event",
  "description": "Add a new event to the causal memory system",
  "inputSchema": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "Event description"
      },
      "timestamp": {
        "type": "string",
        "format": "date-time",
        "description": "When the event occurred"
      },
      "metadata": {
        "type": "object",
        "description": "Additional event metadata"
      }
    },
    "required": ["description"]
  }
}
```

#### query

Retrieve causal context for analysis.

**Schema:**
```json
{
  "name": "query",
  "description": "Query the causal memory system for relevant context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "max_events": {
        "type": "integer",
        "default": 10,
        "description": "Maximum events to return"
      }
    },
    "required": ["query"]
  }
}
```

## 📊 Data Types

### Event

```python
@dataclass
class Event:
    """Represents a stored event."""
    id: EventID
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]
    causal_links: List[str]  # Related event IDs
```

### CausalRelationship

```python
@dataclass
class CausalRelationship:
    """Represents a causal relationship between events."""
    source_event_id: EventID
    target_event_id: EventID
    relationship_type: CausalType
    confidence: float
    temporal_gap: float  # Seconds between events
    reasoning: str
```

### ContextResponse

```python
@dataclass
class ContextResponse:
    """Response from context query."""
    events: List[Event]
    causal_relationships: List[CausalRelationship]
    narrative: str
    confidence: float
    query_time_ms: int
    total_events_considered: int
```

## 🔧 Configuration

### MemoryConfig

```python
@dataclass
class MemoryConfig:
    """Configuration for the memory system."""
    
    # Database settings
    database_path: str = "memory.db"
    connection_pool_size: int = 10
    
    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    
    # Causal analysis settings
    causal_threshold: float = 0.7
    max_temporal_gap_hours: int = 24
    
    # Performance settings
    embedding_cache_size: int = 10000
    batch_size: int = 100
    max_context_length: int = 2000
```

## ⚠️ Error Handling

### Exception Types

```python
class MemoryError(Exception):
    """Base exception for memory system errors."""

class ValidationError(MemoryError):
    """Raised when input validation fails."""

class StorageError(MemoryError):
    """Raised when database operations fail."""

class ProcessingError(MemoryError):
    """Raised when event processing fails."""
```

### Error Response Format (REST API)

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Event description cannot be empty",
    "code": "INVALID_INPUT",
    "details": {
      "field": "description",
      "value": ""
    }
  },
  "request_id": "req_12345",
  "timestamp": "2025-09-15T10:30:00Z"
}
```

## 📈 Rate Limits

### API Rate Limits

| Endpoint | Rate Limit | Burst Limit |
|----------|------------|-------------|
| POST /events | 100/minute | 200/minute |
| POST /context | 50/minute | 100/minute |
| POST /search | 200/minute | 400/minute |
| GET /events/* | 500/minute | 1000/minute |

### Resource Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Event description | 10,000 chars | Maximum length |
| Metadata size | 1MB | Per event |
| Query length | 1,000 chars | Search queries |
| Context window | 50 events | Maximum returned |

---

This API documentation provides comprehensive coverage of all available interfaces and usage patterns for the Causal Memory Core system.