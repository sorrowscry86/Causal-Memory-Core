#!/usr/bin/env python3
"""
MCP Server for the Causal Memory Core
Exposes memory.add_event and memory.query tools via the Model Context Protocol
"""

import asyncio
import logging
from typing import Any, Sequence

# MCP SDK imports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from causal_memory_core import CausalMemoryCore
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("causal-memory-mcp")

# Create server instance
server = Server(Config.MCP_SERVER_NAME)

# Global memory core instance
memory_core = None

# Semantic Query Preprocessor (Week 1-2)
# Week 1: pass-through; Week 2: basic classification + semantic mapping for queries
from enum import Enum
from dataclasses import dataclass
import re

class QueryType(Enum):
    DIRECT_KEYWORD = "direct_keyword"
    CONCEPTUAL = "conceptual"
    NARRATIVE = "narrative"
    CAUSAL = "causal"
    UNKNOWN = "unknown"

@dataclass
class TranslationResult:
    text: str
    confidence: float

class QueryClassifier:
    """Lightweight rule-based classifier for Week 2."""
    DIRECT_HINTS = [
        r"\b(add|insert|create|write)[ _-]?(event|record|file|dir|directory|folder)\b",
        r"\bquery\b",
        r"\bsearch\b",
    ]
    CONCEPTUAL_HINTS = [
        r"\bwhy\b|\bhow\b|\broot cause\b|\bcontext\b",
        r"\bexplain\b|\bmeaning\b|\bconcept\b",
    ]

    def classify_query(self, query_text: str) -> QueryType:
        qt = query_text.lower()
        if any(re.search(p, qt) for p in self.DIRECT_HINTS):
            return QueryType.DIRECT_KEYWORD
        if any(re.search(p, qt) for p in self.CONCEPTUAL_HINTS):
            return QueryType.CONCEPTUAL
        # Simple narrative/causal heuristics
        if "cause" in qt or "led to" in qt or "because" in qt:
            return QueryType.CAUSAL
        return QueryType.UNKNOWN

class SemanticMapper:
    """Maps conceptual/natural language to known keywords (Week 2)."""
    SEMANTIC_MAPPINGS = {
        # category: list of known phrases/keywords to bias toward
        "file creation": [
            "file creation", "created", "write_file", "file created",
            "new file", "create file"
        ],
        "testing activities": [
            "testing", "comprehensive testing", "test", "testing outcomes",
            "e2e tests", "unit tests", "benchmark"
        ],
        "memory systems": [
            "memory", "causal memory core", "memory systems", "context", "narrative",
            "causal chain", "retrieve context"
        ],
        "directory operations": [
            "directory", "create_directory", "folder", "make folder"
        ],
        "application launch": [
            "opening application", "app opened", "launched application", "interactive mode"
        ],
        "document loading": [
            "document loaded", "file loaded", "load document", "file opened"
        ],
        "project creation": [
            "project creation", "created project", "new project"
        ],
        "workflow actions": [
            "workflow actions", "workflow", "actions", "add event", "query memory"
        ],
        "bug resolution": [
            "bug resolved", "fix applied", "patch deployed"
        ],
        "special characters": [
            "special characters", "symbols", "encoding"
        ],
        "mcp server": [
            "mcp server", "model context protocol"
        ],
        "user interactions": [
            "clicked on a file", "clicked", "open file"
        ],
    }

    def translate(self, text: str) -> TranslationResult:
        lt = text.lower()
        best_match = None
        best_score = 0.0
        for _, phrases in self.SEMANTIC_MAPPINGS.items():
            for p in phrases:
                score = self._similarity(lt, p)
                if score > best_score:
                    best_score = score
                    best_match = p
        # If no good match, return original with low confidence
        return TranslationResult(text=best_match or text, confidence=best_score)

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        # Very rough token overlap similarity for Week 2 bootstrap
        at = set(re.findall(r"\w+", a))
        bt = set(re.findall(r"\w+", b))
        if not at or not bt:
            return 0.0
        inter = len(at & bt)
        union = len(at | bt)
        return inter / union

_classifier = QueryClassifier()
_mapper = SemanticMapper()

# In-memory metrics (Week 2)
_metrics = {
    "total_calls": 0,
    "total_query_calls": 0,
    "total_event_calls": 0,
    "classifications": {qt.value: 0 for qt in QueryType},
    "translations_applied": 0,
    "translations_rejected": 0,
    "errors": 0,
    "recent": []  # list of dicts {mode, input, output, qtype, confidence}
}

def _record_metric(entry: dict) -> None:
    try:
        # Bound list size to avoid memory growth
        _metrics["recent"].append(entry)
        limit = max(0, Config.PREPROCESSOR_METRICS_RECENT_LIMIT)
        if len(_metrics["recent"]) > limit:
            _metrics["recent"] = _metrics["recent"][-limit:]
    except Exception:
        # Metrics must never interfere with flow
        pass


def preprocess_input(text: str, mode: str) -> str:
    """
    Week 1-2 preprocessor with fail-open behavior.
    - mode: 'add_event' or 'query'
    Behavior:
      - Disabled: returns text unchanged
      - Enabled:
        - add_event: pass-through (Week 2 focuses on queries)
        - query: classify and attempt semantic translation, apply if above threshold
    """
    try:
        _metrics["total_calls"] += 1
        if not Config.PREPROCESSOR_ENABLED:
            return text

        if mode == "add_event":
            _metrics["total_event_calls"] += 1
            return text  # Preserve event integrity

        if mode == "query":
            _metrics["total_query_calls"] += 1
            qtype = _classifier.classify_query(text)
            _metrics["classifications"][qtype.value] += 1
            if qtype == QueryType.DIRECT_KEYWORD:
                _record_metric({"mode": mode, "input": text, "output": text, "qtype": qtype.value, "confidence": None})
                return text  # keep successful direct patterns as-is
            # For conceptual/causal/unknown, try translation
            result = _mapper.translate(text)
            if result.confidence >= Config.PREPROCESSOR_CONFIDENCE_THRESHOLD:
                _metrics["translations_applied"] += 1
                logger.debug(f"Preprocessor translated query: '{text}' -> '{result.text}' (conf={result.confidence:.2f})")
                _record_metric({"mode": mode, "input": text, "output": result.text, "qtype": qtype.value, "confidence": result.confidence})
                return result.text
            _metrics["translations_rejected"] += 1
            logger.debug(f"Preprocessor kept original (low confidence={result.confidence:.2f})")
            _record_metric({"mode": mode, "input": text, "output": text, "qtype": qtype.value, "confidence": result.confidence})
            return text

        return text
    except Exception as e:
        logger.warning(f"Preprocessor error in mode={mode}: {e}")
        if Config.PREPROCESSOR_FAIL_OPEN:
            return text
        raise

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    tools = [
        types.Tool(
            name="add_event",
            description="Add a new event to the causal memory system. The system will automatically determine causal relationships with previous events using semantic similarity and LLM reasoning, creating links that enable narrative chain reconstruction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "effect": {
                        "type": "string",
                        "description": "Description of the event that occurred (the effect). Should be a clear, concise statement from the agent's perspective. The system will analyze this against recent events to detect causal relationships."
                    }
                },
                "required": ["effect"]
            }
        ),
        types.Tool(
            name="query",
            description="Query the causal memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for in memory. Can be a question, topic, or description of an event. The system will return the complete causal narrative leading to the most relevant event."
                    }
                },
                "required": ["query"]
            }
        )
    ]

    # Optionally expose debug tool for preprocessor metrics
    if Config.PREPROCESSOR_ENABLED and Config.PREPROCESSOR_DEBUG_ENABLED:
        tools.append(
            types.Tool(
                name="preprocessor_debug_metrics",
                description="Inspect in-memory metrics for the semantic preprocessor (counts and recent translations).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            )
        )

    # Week 3 skeleton: suggestions tool
    if Config.PREPROCESSOR_SUGGESTIONS_ENABLED:
        tools.append(
            types.Tool(
                name="preprocessor_suggestions",
                description="Suggest likely query keywords or categories based on input text using lightweight semantic mapping.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Free-form text to analyze for suggested query terms/categories."
                        },
                        "top_k": {
                            "type": "number",
                            "description": "Number of suggestions to return (default from config)."
                        }
                    },
                    "required": ["text"],
                    "additionalProperties": False
                }
            )
        )

    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool calls"""
    global memory_core
    
    # Initialize memory core if not already done
    if memory_core is None:
        try:
            memory_core = CausalMemoryCore()
            logger.info("Causal Memory Core initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Causal Memory Core: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error initializing Causal Memory Core: {str(e)}"
            )]
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "add_event":
            effect = arguments.get("effect")
            if not effect:
                return [types.TextContent(
                    type="text",
                    text="Error: 'effect' parameter is required"
                )]
            
            # Week 1: route through pass-through preprocessor (fail-open)
            effect_processed = preprocess_input(effect, "add_event")
            memory_core.add_event(effect_processed)
            logger.info(f"Added event to memory: {effect_processed}")
            return [types.TextContent(
                type="text",
                text=f"Successfully added event to memory: {effect_processed}"
            )]
            
        elif name == "query":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            # Week 1: route through pass-through preprocessor (fail-open)
            query_processed = preprocess_input(query, "query")
            context = memory_core.get_context(query_processed)
            logger.info(f"Retrieved context for query: {query_processed}")
            return [types.TextContent(
                type="text",
                text=context
            )]
            
        elif name == "preprocessor_debug_metrics" and Config.PREPROCESSOR_ENABLED and Config.PREPROCESSOR_DEBUG_ENABLED:
            # Safe snapshot of metrics to avoid mutation during serialization
            try:
                snapshot = {
                    "total_calls": _metrics.get("total_calls", 0),
                    "total_query_calls": _metrics.get("total_query_calls", 0),
                    "total_event_calls": _metrics.get("total_event_calls", 0),
                    "classifications": dict(_metrics.get("classifications", {})),
                    "translations_applied": _metrics.get("translations_applied", 0),
                    "translations_rejected": _metrics.get("translations_rejected", 0),
                    "errors": _metrics.get("errors", 0),
                    "recent": list(_metrics.get("recent", [])),
                }
            except Exception:
                snapshot = {"error": "Failed to capture metrics snapshot"}
            return [types.TextContent(type="text", text=str(snapshot))]

        elif name == "preprocessor_suggestions" and Config.PREPROCESSOR_SUGGESTIONS_ENABLED:
            text = arguments.get("text") if isinstance(arguments, dict) else None
            if not text:
                return [types.TextContent(type="text", text="Error: 'text' parameter is required")]
            try:
                top_k = arguments.get("top_k") if isinstance(arguments, dict) else None
                try:
                    k = int(top_k) if top_k is not None else int(Config.PREPROCESSOR_SUGGESTION_TOP_K)
                except Exception:
                    k = int(Config.PREPROCESSOR_SUGGESTION_TOP_K)
                # Produce simple ranked suggestions by mapping similarity over phrases
                lt = text.lower()
                scored = []
                for cat, phrases in SemanticMapper.SEMANTIC_MAPPINGS.items():
                    for p in phrases:
                        score = SemanticMapper._similarity(lt, p)
                        if score > 0:
                            scored.append((score, cat, p))
                scored.sort(key=lambda x: x[0], reverse=True)
                out = [
                    {"category": cat, "phrase": phrase, "score": round(float(score), 3)}
                    for score, cat, phrase in scored[:k]
                ]
                return [types.TextContent(type="text", text=str(out))]
            except Exception as e:
                logger.error(f"Suggestions error: {e}")
                return [types.TextContent(type="text", text="[]")]

        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        # Increment error metric but preserve fail-open response
        try:
            _metrics["errors"] += 1
        except Exception:
            pass
        logger.error(f"Error executing {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main entry point for the MCP server"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=Config.MCP_SERVER_NAME,
                server_version=Config.MCP_SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
