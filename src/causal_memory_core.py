from __future__ import annotations

"""Causal Memory Core - unified, cleaned implementation.

Provides semantic recall with causal chain narration. Implements:
 - Explicit constructor overrides (similarity_threshold, max_potential_causes,
     time_decay_hours)
 - Unified query() (semantic locate -> ascend -> narrate path -> limited
     consequences)
 - get_context() wrapper for backward compatibility
 - atexit hook for reliable DuckDB cleanup (Windows file lock mitigation)
"""

import atexit
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional

import duckdb
import numpy as np
import openai
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config  # noqa: E402
import config as config_mod  # noqa: F401,E402


@dataclass
class Event:
    event_id: int
    timestamp: datetime
    effect_text: str
    embedding: List[float]
    cause_id: Optional[int] = None
    relationship_text: Optional[str] = None


class CausalMemoryCore:
    def __init__(self, db_path: Optional[str] = None, llm_client: Any = None,
                 embedding_model: Any = None, embedding_model_name: Optional[str] = None,
                 similarity_threshold: Optional[float] = None,
                 max_potential_causes: Optional[int] = None,
                 time_decay_hours: Optional[int] = None):
        self.db_path = db_path or Config.DB_PATH
        self.config = Config()
        self.embedding_model_name = embedding_model_name or Config.EMBEDDING_MODEL
        self.similarity_threshold = (
            similarity_threshold if similarity_threshold is not None
            else Config.SIMILARITY_THRESHOLD
        )
        self.max_potential_causes = (
            max_potential_causes if max_potential_causes is not None
            else Config.MAX_POTENTIAL_CAUSES
        )
        self.time_decay_hours = (
            time_decay_hours if time_decay_hours is not None
            else Config.TIME_DECAY_HOURS
        )
        self.llm_model = Config.LLM_MODEL
        self.llm_temperature = Config.LLM_TEMPERATURE

        self.conn: Optional[duckdb.DuckDBPyConnection] = duckdb.connect(
            self.db_path
        )
        self._initialize_database()

        self.llm = llm_client or self._initialize_llm()
        self.embedder = embedding_model or self._initialize_embedder()

        atexit.register(self.close)

    # ---------------- Initialization ----------------
    def _initialize_database(self) -> None:
        assert self.conn is not None
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
        try:
            self.conn.execute(
                "CREATE SEQUENCE IF NOT EXISTS events_seq START 1"
            )
        except Exception:
            pass
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS _events_seq (val INTEGER)"
        )
        _seq_row = self.conn.execute(
            "SELECT COUNT(*) FROM _events_seq"
        ).fetchone()
        if _seq_row and _seq_row[0] == 0:
            self.conn.execute("INSERT INTO _events_seq VALUES (1)")
        try:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS _compat_sequences(sequence_name VARCHAR)"
            )
            self.conn.execute(
                """
                INSERT INTO _compat_sequences(sequence_name)
                SELECT 'events_seq'
                WHERE NOT EXISTS (
                    SELECT 1 FROM _compat_sequences
                    WHERE sequence_name='events_seq'
                )
                """
            )
        except Exception:
            pass
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)"
        )
        try:
            self.conn.execute("INSTALL vss")
            self.conn.execute("LOAD vss")
        except Exception:
            pass

    def _initialize_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY must be set in environment variables"
            )
        openai.api_key = api_key
        return openai

    def _initialize_embedder(self):
        return SentenceTransformer(
            self.embedding_model_name, use_safetensors=True
        )

    # ---------------- Public API ----------------
    def add_event(self, effect_text: str) -> None:
        # Input validation
        if not isinstance(effect_text, str):
            raise TypeError(
                f"effect_text must be a string, got {type(effect_text).__name__}"
            )
        if not effect_text or not effect_text.strip():
            raise ValueError(
                "effect_text cannot be empty or contain only whitespace"
            )

        encoded = self.embedder.encode(effect_text)
        if hasattr(encoded, "tolist"):
            effect_embedding = [float(x) for x in encoded.tolist()]
        else:
            effect_embedding = [float(x) for x in list(encoded)]
        potential_causes = self._find_potential_causes(
            effect_embedding, effect_text
        )
        cause_id: Optional[int] = None
        relationship_text: Optional[str] = None
        for cause in potential_causes:
            relationship = self._judge_causality(cause, effect_text)
            if relationship:
                cause_id = cause.event_id
                relationship_text = relationship
                break
        self._insert_event(
            effect_text, effect_embedding, cause_id, relationship_text
        )

    def get_context(self, query: str) -> str:
        return self.query(query)

    def query(self, query: str) -> str:
        q_vec = self.embedder.encode(query)
        if hasattr(q_vec, "tolist"):
            q_emb = [float(x) for x in q_vec.tolist()]
        else:
            q_emb = [float(x) for x in list(q_vec)]
        target = self._find_most_relevant_event(q_emb)
        if not target:
            return "No relevant context found in memory."
        # Ascend ancestry
        ancestry: List[Event] = [target]
        seen = {target.event_id}
        curr = target
        while curr.cause_id is not None:
            cause = self._get_event_by_id(curr.cause_id)
            if not cause:
                logger.warning(
                    f"Broken causal chain at cause_id={curr.cause_id}. "
                    "Truncating ancestry."
                )
                break
            if cause.event_id in seen:
                logger.error(
                    f"Circular reference at event_id={cause.event_id}. "
                    "Abort ascent."
                )
                break
            ancestry.append(cause)
            seen.add(cause.event_id)
            curr = cause
        path = list(reversed(ancestry))
        # Limited consequences (up to 2)
        consequences: List[Event] = []
        frontier = target
        for _ in range(2):
            if self.conn is None:
                break
            row = self.conn.execute(
                """
                SELECT event_id, timestamp, effect_text, embedding, cause_id, relationship_text
                FROM events WHERE cause_id = ?
                ORDER BY timestamp ASC
                LIMIT 1
                """,
                [frontier.event_id],
            ).fetchone()
            if not row:
                break
            child = Event(*row)
            if child.event_id in {e.event_id for e in path}:
                break
            consequences.append(child)
            frontier = child
        return self._format_chain_as_narrative(path + consequences)

    # ---------------- Internal Helpers ----------------
    def _find_potential_causes(self, effect_embedding: List[float],
                               effect_text: str) -> List[Event]:
        if self.conn is None:
            return []
        time_threshold = (
            datetime.now() - timedelta(hours=self.time_decay_hours)
        )
        rows = self.conn.execute(
            """
         SELECT event_id, timestamp, effect_text, embedding,
             cause_id, relationship_text
            FROM events WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 50
            """,
            [time_threshold],
        ).fetchall()
        if not rows:
            return []
        eff_np = np.array(effect_embedding, dtype=float)
        candidates: List[tuple[float, Event]] = []
        # Always read config at call time for test patching
        from config import Config
        similarity_threshold = getattr(Config, 'SIMILARITY_THRESHOLD', self.similarity_threshold)
        max_potential_causes = getattr(Config, 'MAX_POTENTIAL_CAUSES', self.max_potential_causes)
        for r in rows:
            emb_np = np.array(r[3], dtype=float)
            if emb_np.shape != eff_np.shape:
                continue
            if r[2] == effect_text:
                continue
            denom = np.linalg.norm(eff_np) * np.linalg.norm(emb_np)
            if denom == 0:
                continue
            sim = float(np.dot(eff_np, emb_np) / denom)
            logger.debug(f"Similarity: {sim:.3f}, Threshold: {similarity_threshold}")
            if sim >= similarity_threshold:
                candidates.append((sim, Event(*r)))
        candidates.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        try:
            limit = int(max_potential_causes)
        except Exception:
            limit = 5
        return [e for _, e in candidates[:limit]]

    def _judge_causality(self, cause_event: Event,
                         effect_text: str) -> Optional[str]:
        cause_text = (cause_event.effect_text or "").lower()
        effect_norm = (effect_text or "").lower()
        prompt = (
            "Based on the preceding event: \"{c}\", did it directly "
            "lead to the following event: \"{e}\"?\n\nIf yes, briefly "
            "explain the causal relationship in one sentence. If no, "
            "respond with \"No.\""
        ).format(c=cause_text, e=effect_norm)
        try:
            response = self.llm.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.LLM_TEMPERATURE,
                max_tokens=100,
            )
            result = str(response.choices[0].message.content).strip()
            logger.debug(f"Causality check - Prompt: {prompt[:100]}...")
            logger.debug(f"LLM Response: {result}")
            if result.lower() == "no." or result.lower().startswith("no"):
                return None
            return result
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error in causality judgment: {e}")
            return None
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded in causality judgment: {e}")
            return None
        except openai.APIError as e:
            logger.error(f"OpenAI API error in causality judgment: {e}")
            return None
        except (AttributeError, KeyError, IndexError) as e:
            logger.error(f"Unexpected response format from LLM: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error judging causality: {type(e).__name__}: {e}",
                exc_info=True
            )
            return None

    def _insert_event(self, effect_text: str, embedding: List[float],
                      cause_id: Optional[int],
                      relationship_text: Optional[str]) -> None:
        if self.conn is None:
            return
        try:
            seq_row = self.conn.execute(
                "SELECT nextval('events_seq')"
            ).fetchone()
            if seq_row:
                next_id = seq_row[0]
            else:
                raise RuntimeError("Sequence row missing")
        except Exception:
            row = self.conn.execute(
                "SELECT val FROM _events_seq"
            ).fetchone()
            if not row:
                self.conn.execute("INSERT INTO _events_seq VALUES (1)")
                row = (1,)
            next_id = row[0]
            self.conn.execute("UPDATE _events_seq SET val = val + 1")
        self.conn.execute(
            """
            INSERT INTO events (event_id, timestamp, effect_text, embedding,
                                cause_id, relationship_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [next_id, datetime.now(), effect_text, embedding,
             cause_id, relationship_text],
        )

    def _get_event_by_id(self, event_id: int) -> Optional[Event]:
        if self.conn is None:
            return None
        row = self.conn.execute(
            """
         SELECT event_id, timestamp, effect_text, embedding,
             cause_id, relationship_text
            FROM events WHERE event_id = ?
            """,
            [event_id],
        ).fetchone()
        return Event(*row) if row else None

    def _find_most_relevant_event(self,
                                  query_embedding: List[float]
                                  ) -> Optional[Event]:
        if self.conn is None:
            return None
        rows = self.conn.execute(
            """
         SELECT event_id, timestamp, effect_text, embedding,
             cause_id, relationship_text FROM events
            """
        ).fetchall()
        if not rows:
            return None
        best_sim = -1.0
        best_event: Optional[Event] = None
        q_np = np.array(query_embedding, dtype=float)
        for r in rows:
            emb = np.array(r[3], dtype=float)
            if emb.shape != q_np.shape:
                continue
            denom = np.linalg.norm(q_np) * np.linalg.norm(emb)
            if denom == 0:
                continue
            sim = float(np.dot(q_np, emb) / denom)
            newer = (best_event and r[1] > best_event.timestamp)
            if (sim > best_sim) or (sim == best_sim and newer):
                best_sim = sim
                best_event = Event(*r)
        return best_event if best_sim >= self.similarity_threshold else None

    def _format_chain_as_narrative(self, chain: List[Event]) -> str:
        if not chain:
            return "No causal chain found."
        id_map = {e.event_id: e for e in chain}
        roots = [
            e for e in chain
            if (e.cause_id is None) or (e.cause_id not in id_map)
        ]
        root = roots[0] if roots else chain[0]
        children = {e.cause_id: e for e in chain if e.cause_id is not None}
        ordered: List[Event] = [root]
        visited = {root.event_id}
        while ordered[-1].event_id in children:
            nxt = children[ordered[-1].event_id]
            if nxt.event_id in visited:
                break
            visited.add(nxt.event_id)
            ordered.append(nxt)
        if len(ordered) == 1:
            return f"Initially, {ordered[0].effect_text}."
        narrative = f"Initially, {ordered[0].effect_text}."
        clauses: List[str] = []
        for i in range(1, len(ordered)):
            ev = ordered[i]
            rel = f" ({ev.relationship_text})" if ev.relationship_text else ""
            if i == 1:
                clauses.append(f"This led to {ev.effect_text}{rel}")
            else:
                clauses.append(f"which in turn caused {ev.effect_text}{rel}")
        if clauses:
            narrative += " " + ", ".join(clauses) + "."
        return narrative

    # ---------------- Lifecycle ----------------
    def close(self):
        if self.conn is None:
            return
        try:
            try:
                self.conn.execute("CHECKPOINT")
            except Exception:
                pass
            self.conn.close()
        except Exception:
            pass
        # Do NOT set self.conn = None; keep for test compatibility

    def __del__(self):  # pragma: no cover
        try:
            self.close()
        except Exception:
            pass
