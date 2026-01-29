"""SQLite Deterministic Vault backend.

Features
--------
- CRUD for facts, episodes and documents
- Full provenance metadata for facts
- Audit trail table
- Search via SQLite FTS5 when available, with LIKE fallback

This backend is designed to be usable in production (file-backed DB) and for
unit tests (in-memory).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence

from ..core.exceptions import BackendError, NotFound, ValidationError
from ..core.types import Policy, SearchHit, Sensitivity
from ..core.utils import stable_json_dumps, utcnow
from .base import StorageBackend


def _json(obj: Any) -> str:
    return stable_json_dumps(obj if obj is not None else {})


@dataclass(slots=True)
class SQLiteDVConfig:
    """SQLite DV configuration."""

    pragmas: Mapping[str, Any] | None = None


class SQLiteDeterministicVault(StorageBackend):
    """Deterministic Vault implemented with SQLite.

    Parameters
    ----------
    db_path:
        Path to SQLite database. Use ":memory:" for ephemeral DBs.
    config:
        Optional configuration.
    """

    def __init__(self, db_path: str = ":memory:", config: SQLiteDVConfig | None = None) -> None:
        self.db_path = db_path
        self.config = config or SQLiteDVConfig()
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._apply_pragmas()
        self._init_schema()
        self._fts_enabled = self._try_enable_fts5()

    @property
    def fts_enabled(self) -> bool:
        return bool(self._fts_enabled)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _apply_pragmas(self) -> None:
        pragmas = dict(self.config.pragmas or {})
        # Reasonable defaults for a local file-based DB; safe for in-memory too.
        pragmas.setdefault("foreign_keys", 1)
        pragmas.setdefault("journal_mode", "WAL")
        pragmas.setdefault("synchronous", "NORMAL")
        with self._conn:
            for k, v in pragmas.items():
                try:
                    self._conn.execute(f"PRAGMA {k}={json.dumps(v) if isinstance(v, str) else v}")
                except Exception:
                    # Ignore unsupported pragmas for portability.
                    continue

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    event TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    ref TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_created ON episodes(created_at)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_created ON documents(created_at)")

    def _try_enable_fts5(self) -> bool:
        """Try to enable FTS5. Returns True if available."""
        try:
            with self._conn:
                self._conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS fts_records USING fts5(
                        kind,
                        ref,
                        content,
                        tags,
                        tokenize='porter'
                    )
                    """
                )
                self._conn.execute("CREATE INDEX IF NOT EXISTS idx_fts_ref ON fts_records(ref)")
            return True
        except Exception:
            return False

    def _fts_upsert(self, *, kind: str, ref: str, content: str, tags: Sequence[str] | None = None) -> None:
        if not self._fts_enabled:
            return
        tags_s = " ".join(tags or [])
        with self._conn:
            # Remove previous entries for deterministic updates.
            self._conn.execute("DELETE FROM fts_records WHERE ref=?", (ref,))
            self._conn.execute(
                "INSERT INTO fts_records(kind, ref, content, tags) VALUES (?, ?, ?, ?)",
                (kind, ref, content, tags_s),
            )

    def append_audit(self, action: str, ref: str, policy: Policy, details: Mapping[str, Any] | None = None) -> None:
        """Append an audit trail row."""
        with self._conn:
            self._conn.execute(
                "INSERT INTO audit(ts, action, ref, policy, details_json) VALUES (?, ?, ?, ?, ?)",
                (str(utcnow()), action, ref, policy.value, _json(details)),
            )

    def write_episodic(
        self,
        event: str,
        meta: Mapping[str, Any] | None = None,
        *,
        policy: Policy = Policy.AUDITABLE,
        sensitivity: Sensitivity = Sensitivity.LOW,
    ) -> str:
        if not event:
            raise ValidationError("event must be non-empty")
        eid = str(uuid.uuid4())
        ref = f"episode:{eid}"
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO episodes(id, event, meta_json, policy, sensitivity, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (eid, event, _json(meta), policy.value, sensitivity.value, str(utcnow())),
            )
        self._fts_upsert(kind="episode", ref=ref, content=event, tags=(meta or {}).get("tags") if isinstance(meta, dict) else None)
        self.append_audit("write_episodic", ref, policy, {"sensitivity": sensitivity.value})
        return eid

    def write_fact(
        self,
        key: str,
        value: Any,
        provenance: Mapping[str, Any] | None = None,
        *,
        policy: Policy = Policy.USER_CONFIRMED,
        sensitivity: Sensitivity = Sensitivity.MEDIUM,
    ) -> str:
        if not key:
            raise ValidationError("key must be non-empty")
        now = str(utcnow())
        ref = f"fact:{key}"
        meta = {"tags": (provenance or {}).get("tags", []) if isinstance(provenance, dict) else []}
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO facts(key, value_json, provenance_json, meta_json, policy, sensitivity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    provenance_json=excluded.provenance_json,
                    meta_json=excluded.meta_json,
                    policy=excluded.policy,
                    sensitivity=excluded.sensitivity,
                    updated_at=excluded.updated_at
                """,
                (key, _json(value), _json(provenance), _json(meta), policy.value, sensitivity.value, now, now),
            )
        self._fts_upsert(kind="fact", ref=ref, content=f"{key}: {stable_json_dumps(value)}", tags=meta.get("tags") or [])
        self.append_audit("write_fact", ref, policy, {"sensitivity": sensitivity.value})
        return key

    def write_document(
        self,
        content: str,
        meta: Mapping[str, Any] | None = None,
        *,
        policy: Policy = Policy.AUDITABLE,
        sensitivity: Sensitivity = Sensitivity.LOW,
    ) -> str:
        if not content:
            raise ValidationError("content must be non-empty")
        did = str(uuid.uuid4())
        ref = f"doc:{did}"
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO documents(id, content, meta_json, policy, sensitivity, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (did, content, _json(meta), policy.value, sensitivity.value, str(utcnow())),
            )
        tags = (meta or {}).get("tags") if isinstance(meta, dict) else None
        self._fts_upsert(kind="doc", ref=ref, content=content, tags=tags)
        self.append_audit("write_document", ref, policy, {"sensitivity": sensitivity.value})
        return did

    def read_exact(self, ref: str) -> Mapping[str, Any]:
        kind, key = self._parse_ref(ref)
        with self._lock:
            if kind == "fact":
                row = self._conn.execute("SELECT * FROM facts WHERE key=?", (key,)).fetchone()
                if row is None:
                    raise NotFound(ref)
                return {
                    "kind": "fact",
                    "key": row["key"],
                    "value": json.loads(row["value_json"]),
                    "provenance": json.loads(row["provenance_json"]),
                    "meta": json.loads(row["meta_json"]),
                    "policy": row["policy"],
                    "sensitivity": row["sensitivity"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            if kind == "episode":
                row = self._conn.execute("SELECT * FROM episodes WHERE id=?", (key,)).fetchone()
                if row is None:
                    raise NotFound(ref)
                return {
                    "kind": "episode",
                    "id": row["id"],
                    "event": row["event"],
                    "meta": json.loads(row["meta_json"]),
                    "policy": row["policy"],
                    "sensitivity": row["sensitivity"],
                    "created_at": row["created_at"],
                }
            if kind == "doc":
                row = self._conn.execute("SELECT * FROM documents WHERE id=?", (key,)).fetchone()
                if row is None:
                    raise NotFound(ref)
                return {
                    "kind": "doc",
                    "id": row["id"],
                    "content": row["content"],
                    "meta": json.loads(row["meta_json"]),
                    "policy": row["policy"],
                    "sensitivity": row["sensitivity"],
                    "created_at": row["created_at"],
                }
        raise ValidationError(f"Unknown ref: {ref}")

    def search(self, query: str, *, limit: int = 20) -> list[SearchHit]:
        if not query:
            return []
        limit = max(1, int(limit))
        with self._lock:
            if self._fts_enabled:
                try:
                    rows = self._conn.execute(
                        """
                        SELECT kind, ref, bm25(fts_records) AS score,
                               snippet(fts_records, 2, '[', ']', '…', 12) AS snip
                        FROM fts_records
                        WHERE fts_records MATCH ?
                        ORDER BY score ASC
                        LIMIT ?
                        """,
                        (query, limit),
                    ).fetchall()
                    # Lower bm25 is better. Convert to a higher-is-better score.
                    hits: list[SearchHit] = []
                    for r in rows:
                        bm25 = float(r["score"]) if r["score"] is not None else 0.0
                        score = float(1.0 / (1.0 + max(0.0, bm25)))
                        hits.append(SearchHit(kind=str(r["kind"]), ref=str(r["ref"]), score=score, snippet=str(r["snip"] or "")))
                    return hits
                except sqlite3.OperationalError:
                    # Bad FTS syntax → fallback to LIKE.
                    pass

            # LIKE fallback
            q = f"%{query}%"
            hits: list[SearchHit] = []
            # facts
            for r in self._conn.execute("SELECT key, value_json FROM facts WHERE key LIKE ? OR value_json LIKE ? LIMIT ?", (q, q, limit)).fetchall():
                snippet = f"{r['key']}: {r['value_json'][:200]}"
                hits.append(SearchHit(kind="fact", ref=f"fact:{r['key']}", score=0.1, snippet=snippet))
                if len(hits) >= limit:
                    return hits
            # episodes
            for r in self._conn.execute("SELECT id, event FROM episodes WHERE event LIKE ? LIMIT ?", (q, limit)).fetchall():
                hits.append(SearchHit(kind="episode", ref=f"episode:{r['id']}", score=0.1, snippet=str(r['event'][:200])))
                if len(hits) >= limit:
                    return hits
            # documents
            for r in self._conn.execute("SELECT id, content FROM documents WHERE content LIKE ? LIMIT ?", (q, limit)).fetchall():
                hits.append(SearchHit(kind="doc", ref=f"doc:{r['id']}", score=0.1, snippet=str(r['content'][:200])))
                if len(hits) >= limit:
                    return hits
            return hits

    def delete(self, ref: str) -> bool:
        kind, key = self._parse_ref(ref)
        with self._lock, self._conn:
            if kind == "fact":
                row = self._conn.execute("SELECT policy FROM facts WHERE key=?", (key,)).fetchone()
                if row is None:
                    return False
                if row["policy"] == Policy.PROTECTED.value:
                    raise ValidationError("Cannot delete PROTECTED fact")
                self._conn.execute("DELETE FROM facts WHERE key=?", (key,))
            elif kind == "episode":
                row = self._conn.execute("SELECT policy FROM episodes WHERE id=?", (key,)).fetchone()
                if row is None:
                    return False
                if row["policy"] == Policy.PROTECTED.value:
                    raise ValidationError("Cannot delete PROTECTED episode")
                self._conn.execute("DELETE FROM episodes WHERE id=?", (key,))
            elif kind == "doc":
                row = self._conn.execute("SELECT policy FROM documents WHERE id=?", (key,)).fetchone()
                if row is None:
                    return False
                if row["policy"] == Policy.PROTECTED.value:
                    raise ValidationError("Cannot delete PROTECTED doc")
                self._conn.execute("DELETE FROM documents WHERE id=?", (key,))
            else:
                raise ValidationError(f"Unknown kind: {kind}")

            if self._fts_enabled:
                self._conn.execute("DELETE FROM fts_records WHERE ref=?", (ref,))

        self.append_audit("delete", ref, Policy.AUDITABLE, {})
        return True

    def delete_episode(self, episode_id: str) -> bool:
        """Convenience method for deleting episodes."""
        return self.delete(f"episode:{episode_id}")

    def load_recent_episodes(self, *, window_seconds: int) -> list[Mapping[str, Any]]:
        window_seconds = max(1, int(window_seconds))
        # SQLite timestamps are stored as strings; we use lexical ordering for ISO.
        # For simplicity we fetch all and filter in Python.
        with self._lock:
            rows = self._conn.execute("SELECT * FROM episodes ORDER BY created_at DESC LIMIT 1000").fetchall()
            out: list[Mapping[str, Any]] = []
            now = utcnow()
            for r in rows:
                try:
                    ts = r["created_at"]
                    # Best-effort parse: datetime.fromisoformat handles +00:00; our stored uses str(datetime)
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts)
                    age = (now - dt).total_seconds()
                except Exception:
                    age = float("inf")
                if age <= window_seconds:
                    out.append({
                        "id": r["id"],
                        "event": r["event"],
                        "meta": json.loads(r["meta_json"]),
                        "policy": r["policy"],
                        "sensitivity": r["sensitivity"],
                        "created_at": r["created_at"],
                    })
            return out

    @staticmethod
    def _parse_ref(ref: str) -> tuple[str, str]:
        if ":" not in ref:
            raise ValidationError("ref must be like 'fact:KEY' or 'episode:ID' or 'doc:ID'")
        kind, key = ref.split(":", 1)
        kind = kind.strip().lower()
        if kind == "facts":
            kind = "fact"
        if kind == "episodes":
            kind = "episode"
        if kind == "documents":
            kind = "doc"
        if kind not in {"fact", "episode", "doc"}:
            raise ValidationError(f"Unknown ref kind: {kind}")
        return kind, key
