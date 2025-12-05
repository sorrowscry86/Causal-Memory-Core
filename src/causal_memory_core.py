from __future__ import annotations

"""Causal Memory Core v1.1.2 with soft-link fallback and narrative recall."""

import atexit
import logging
import os
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional

import duckdb
import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import Config
except ImportError:
    import config as config_mod
    Config = config_mod.Config


@dataclass
class Event:
    event_id: int
    timestamp: datetime
    effect_text: str
    embedding: List[float]
    cause_id: Optional[int] = None
    relationship_text: Optional[str] = None


class CausalMemoryCore:
    def __init__(
        self,
        db_path: Optional[str] = None,
        llm_client: Any | None = None,
        embedding_model: Any | None = None,
        embedding_model_name: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
        max_potential_causes: Optional[int] = None,
        time_decay_hours: Optional[int] = None,
        max_consequence_depth: Optional[int] = None,
        embedding_cache_size: int = 1000,
    ) -> None:
        self.config = Config()
        self.db_path = db_path or self.config.DB_PATH
        self.embedding_model_name = embedding_model_name or self.config.EMBEDDING_MODEL
        self.similarity_threshold = (
            similarity_threshold if similarity_threshold is not None
            else self.config.SIMILARITY_THRESHOLD
        )
        self.soft_link_threshold = 0.85
        self.max_potential_causes = (
            max_potential_causes if max_potential_causes is not None
            else self.config.MAX_POTENTIAL_CAUSES
        )
        self.time_decay_hours = (
            time_decay_hours if time_decay_hours is not None
            else self.config.TIME_DECAY_HOURS
        )
        self.max_consequence_depth = (
            max_consequence_depth if max_consequence_depth is not None
            else getattr(self.config, 'MAX_CONSEQUENCE_DEPTH', 2)
        )
        self.llm_model = self.config.LLM_MODEL
        self.llm_temperature = self.config.LLM_TEMPERATURE

        self._embedding_cache: OrderedDict[str, List[float]] = OrderedDict()
        self._embedding_cache_size = embedding_cache_size

        self.conn: duckdb.DuckDBPyConnection = duckdb.connect(self.db_path)
        self._initialize_database()

        self.llm = llm_client or self._initialize_llm()
        self.embedder = embedding_model or self._initialize_embedder()

        atexit.register(self.close)

    def _initialize_database(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                effect_text VARCHAR NOT NULL,
                embedding DOUBLE[] NOT NULL,
                cause_id INTEGER,
                relationship_text VARCHAR
            )
            """
        )
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        try:
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS events_seq START 1")
        except Exception:
            pass
        self.conn.execute("CREATE TABLE IF NOT EXISTS _events_seq (val INTEGER)")
        if not self.conn.execute("SELECT COUNT(*) FROM _events_seq").fetchone()[0]:
            self.conn.execute("INSERT INTO _events_seq VALUES (1)")
        try:
            self.conn.execute("INSTALL vss")
            self.conn.execute("LOAD vss")
        except Exception:
            pass

    def _initialize_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            try:
                from openai import OpenAI as OpenAIClient
                return OpenAIClient(base_url=base_url, api_key=api_key or "not-needed")
            except Exception:
                logger.warning("Failed to instantiate OpenAI v1 client with base_url, falling back.")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set to issue causal judgments")
        try:
            import openai as _openai
            _openai.api_key = api_key
            if base_url and hasattr(_openai, "base_url"):
                try:
                    setattr(_openai, "base_url", base_url)
                except Exception:
                    pass
            return _openai
        except Exception:
            from openai import OpenAI as OpenAIClient
            return OpenAIClient(api_key=api_key)

    def _initialize_embedder(self) -> SentenceTransformer:
        return SentenceTransformer(self.embedding_model_name)

    def _get_cached_embedding(self, text: str) -> List[float]:
        if text in self._embedding_cache:
            self._embedding_cache.move_to_end(text)
            return self._embedding_cache[text]
        encoded = self.embedder.encode(text)
        embedding = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)
        self._embedding_cache[text] = embedding
        if len(self._embedding_cache) > self._embedding_cache_size:
            self._embedding_cache.popitem(last=False)
        return embedding

    def add_event(self, effect_text: str) -> None:
        if not effect_text or not effect_text.strip():
            raise ValueError("effect_text cannot be empty")
        embedding = self._get_cached_embedding(effect_text)
        potential_causes = self._find_potential_causes(embedding, effect_text)

        cause_id: Optional[int] = None
        relationship_text: Optional[str] = None

        for cause, score in potential_causes:
            relationship = self._judge_causality(cause, effect_text)
            if relationship:
                cause_id = cause.event_id
                relationship_text = relationship
                break
            if score >= self.soft_link_threshold:
                cause_id = cause.event_id
                relationship_text = "Sequential workflow step detected via high semantic correlation"
                logger.info("Soft link enforced (score %.3f) for event %s", score, cause.event_id)
                break

        self._insert_event(effect_text, embedding, cause_id, relationship_text)

    def query(self, query_text: str) -> str:
        if not query_text or not query_text.strip():
            raise ValueError("query_text cannot be empty")
        query_embedding = self._get_cached_embedding(query_text)
        anchor = self._find_most_relevant_event(query_embedding)
        if not anchor:
            return "No relevant context found in memory."
        chain = self._build_causal_chain(anchor)

        consequences: List[Event] = []
        frontier = anchor
        for _ in range(self.max_consequence_depth):
            row = self.conn.execute(
                "SELECT event_id, timestamp, effect_text, embedding, cause_id, relationship_text "
                "FROM events WHERE cause_id = ? ORDER BY timestamp ASC LIMIT 1",
                [frontier.event_id],
            ).fetchone()
            if not row:
                break
            child = Event(*row)
            if child.event_id in {ev.event_id for ev in chain}:
                break
            consequences.append(child)
            frontier = child

        return self._format_chain_as_narrative(chain + consequences)

    def get_context(self, query_text: str) -> str:
        return self.query(query_text)

    def _find_potential_causes(
        self,
        embedding: List[float],
        effect_text: str,
    ) -> List[tuple[Event, float]]:
        threshold_time = datetime.now() - timedelta(hours=self.time_decay_hours)
        rows = self.conn.execute(
            "SELECT event_id, timestamp, effect_text, embedding, cause_id, relationship_text "
            "FROM events WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 50",
            [threshold_time],
        ).fetchall()
        if not rows:
            return []
        candidates: List[tuple[Event, float]] = []
        eff_np = np.array(embedding, dtype=float)
        for row in rows:
            emb = np.array(row[3], dtype=float)
            if row[2] == effect_text:
                continue
            denom = np.linalg.norm(eff_np) * np.linalg.norm(emb)
            if denom == 0:
                continue
            sim = float(np.dot(eff_np, emb) / denom)
            if sim >= self.similarity_threshold:
                candidates.append((Event(*row), sim))
        candidates.sort(key=lambda pair: (pair[1], pair[0].timestamp), reverse=True)
        return candidates[: self.max_potential_causes]

    def _judge_causality(self, cause_event: Event, effect_text: str) -> Optional[str]:
        if not self.llm:
            return None
        prompt = (
            "Consider these two sequential events:\n"
            f"1. \"{cause_event.effect_text}\"\n"
            f"2. \"{effect_text}\"\n\n"
            "Are these steps part of the same workflow? If so, describe the causal link in one sentence. "
            "If not, respond with 'No.'"
        )
        try:
            response = self.llm.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_temperature,
                max_tokens=120,
            )
            text = str(response.choices[0].message.content).strip()
            if text.lower().startswith("no"):
                return None
            return text
        except Exception as exc:
            logger.warning("LLM causality check failed: %s", exc)
            return None

    def _reserve_event_id(self) -> int:
        row = self.conn.execute("SELECT val FROM _events_seq").fetchone()
        if row:
            next_id = row[0]
            self.conn.execute("UPDATE _events_seq SET val = val + 1")
            return next_id
        next_id = int(datetime.now().timestamp() * 1000)
        self.conn.execute("INSERT INTO _events_seq VALUES (?)", [next_id + 1])
        return next_id

    def _insert_event(
        self,
        effect_text: str,
        embedding: List[float],
        cause_id: Optional[int],
        relationship_text: Optional[str],
    ) -> None:
        event_id = self._reserve_event_id()
        self.conn.execute(
            "INSERT INTO events (event_id, timestamp, effect_text, embedding, cause_id, relationship_text) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [event_id, datetime.now(), effect_text, embedding, cause_id, relationship_text],
        )

    def _get_event_by_id(self, event_id: int) -> Optional[Event]:
        row = self.conn.execute(
            "SELECT event_id, timestamp, effect_text, embedding, cause_id, relationship_text "
            "FROM events WHERE event_id = ?",
            [event_id],
        ).fetchone()
        return Event(*row) if row else None

    def _find_most_relevant_event(self, embedding: List[float]) -> Optional[Event]:
        rows = self.conn.execute(
            "SELECT event_id, timestamp, effect_text, embedding, cause_id, relationship_text FROM events"
        ).fetchall()
        best_sim = -1.0
        best_event: Optional[Event] = None
        query_vec = np.array(embedding, dtype=float)
        for row in rows:
            emb = np.array(row[3], dtype=float)
            denom = np.linalg.norm(query_vec) * np.linalg.norm(emb)
            if denom == 0:
                continue
            sim = float(np.dot(query_vec, emb) / denom)
            newer = best_event and row[1] > best_event.timestamp
            if (sim > best_sim) or (sim == best_sim and newer):
                best_sim = sim
                best_event = Event(*row)
        if best_event and best_sim >= self.similarity_threshold:
            return best_event
        return None

    def _build_causal_chain(self, anchor: Event) -> List[Event]:
        chain: List[Event] = [anchor]
        visited = {anchor.event_id}
        current = anchor
        while current.cause_id is not None:
            cause = self._get_event_by_id(current.cause_id)
            if not cause or cause.event_id in visited:
                break
            chain.insert(0, cause)
            visited.add(cause.event_id)
            current = cause
        return chain

    def _format_chain_as_narrative(self, chain: List[Event]) -> str:
        if not chain:
            return "No causal chain found."
        narrative = f"Initially, {chain[0].effect_text}."
        periodic = []
        for idx, event in enumerate(chain[1:], start=1):
            rel = f" ({event.relationship_text})" if event.relationship_text else ""
            if idx == 1:
                periodic.append(f"This led to {event.effect_text}{rel}.")
            else:
                periodic.append(f"Which in turn caused {event.effect_text}{rel}.")
        if periodic:
            narrative += " " + " ".join(periodic)
        return narrative

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def __del__(self):
        self.close()
