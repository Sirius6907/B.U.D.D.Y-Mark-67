from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DPStore:
    def __init__(self, db_path: str | Path, compatibility_memory=None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.compatibility_memory = compatibility_memory
        self._lock = Lock()
        self._memory_fallback = False
        
        try:
            self._conn = self._connect(str(self.db_path))
            self._ensure_schema()
        except Exception as e:
            print(f"[DPStore] SQLite unavailable, falling back to memory-only mode: {e}")
            self._fallback_to_memory()

    def _connect(self, db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA wal_autocheckpoint=1000;")
        return conn

    def _fallback_to_memory(self):
        self._memory_fallback = True
        try:
            self._conn = self._connect(":memory:")
            self._ensure_schema()
        except Exception as e:
            print(f"[DPStore] Could not initialize memory fallback database: {e}")

    def _execute_query(self, query: str, params: tuple = (), commit: bool = False):
        delay = 0.05
        for attempt in range(6):
            try:
                with self._lock:
                    cursor = self._conn.execute(query, params)
                    if commit:
                        self._conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if "locked" in str(e) or "busy" in str(e):
                    if attempt == 5:
                        raise
                    time.sleep(delay)
                    delay = min(delay * 2, 1.0)
                else:
                    if "corrupt" in str(e).lower() and not self._memory_fallback:
                        print(f"[DPStore] DB corrupted! Falling back to memory-only: {e}")
                        self._fallback_to_memory()
                        return self._execute_query(query, params, commit)
                    raise
            except sqlite3.DatabaseError as e:
                if "corrupt" in str(e).lower() and not self._memory_fallback:
                    print(f"[DPStore] DB corrupted! Falling back to memory-only: {e}")
                    self._fallback_to_memory()
                    return self._execute_query(query, params, commit)
                raise
            except Exception as e:
                raise

    def _ensure_schema(self) -> None:
        import hashlib
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS dp_entries (
                    normalized_goal TEXT NOT NULL,
                    intent_family TEXT NOT NULL,
                    environment_signature TEXT NOT NULL,
                    state_hash TEXT NOT NULL,
                    tool_surface TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    solution_steps TEXT NOT NULL,
                    verified_boundaries TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT NOT NULL,
                    reward_score REAL NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (
                        normalized_goal,
                        intent_family,
                        environment_signature,
                        state_hash,
                        tool_surface,
                        schema_version
                    )
                );
                CREATE INDEX IF NOT EXISTS idx_dp_prefix
                ON dp_entries(intent_family, tool_surface, environment_signature, normalized_goal);

                CREATE TABLE IF NOT EXISTS failure_patterns (
                    normalized_goal TEXT NOT NULL,
                    intent_family TEXT NOT NULL,
                    environment_signature TEXT NOT NULL,
                    tool_surface TEXT NOT NULL,
                    error_signature TEXT,
                    failure_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_failure_lookup
                ON failure_patterns(intent_family, tool_surface, environment_signature, normalized_goal);

                CREATE TABLE IF NOT EXISTS metrics_events (
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    state_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dp_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    state_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._conn.commit()

            # Check if goal_hash column exists
            cursor = self._conn.execute("PRAGMA table_info(dp_entries);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "goal_hash" not in columns:
                try:
                    self._conn.execute("ALTER TABLE dp_entries ADD COLUMN goal_hash TEXT;")
                    self._conn.commit()
                    
                    # Backfill goal_hash for existing rows
                    rows = self._conn.execute(
                        "SELECT rowid, normalized_goal, intent_family, environment_signature, state_hash, tool_surface, schema_version FROM dp_entries;"
                    ).fetchall()
                    for row in rows:
                        raw = "|".join([str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6])])
                        gh = hashlib.sha1(raw.encode("utf-8")).hexdigest()
                        self._conn.execute("UPDATE dp_entries SET goal_hash = ? WHERE rowid = ?;", (gh, row[0]))
                    self._conn.commit()
                except Exception as e:
                    print(f"[DPStore] Schema update failed: {e}")
            
            self._conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dp_goal_hash ON dp_entries(goal_hash);")
            self._conn.execute(
                """
                INSERT OR IGNORE INTO dp_checkpoints (checkpoint_id, state_payload, updated_at)
                SELECT checkpoint_id, state_payload, updated_at FROM checkpoints
                """
            )
            self._conn.commit()

    @staticmethod
    def _encode(record: dict[str, Any]) -> dict[str, Any]:
        import hashlib
        payload = dict(record)
        payload["solution_steps"] = json.dumps(record.get("solution_steps", []))
        payload["verified_boundaries"] = json.dumps(record.get("verified_boundaries", {}))
        payload["evidence"] = json.dumps(record.get("evidence", {}))
        
        if not payload.get("goal_hash"):
            raw = "|".join([
                str(payload.get("normalized_goal", "")),
                str(payload.get("intent_family", "")),
                str(payload.get("environment_signature", "")),
                str(payload.get("state_hash", "")),
                str(payload.get("tool_surface", "")),
                str(payload.get("schema_version", "dp-v2")),
            ])
            payload["goal_hash"] = hashlib.sha1(raw.encode("utf-8")).hexdigest()
        return payload

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        try:
            data = dict(row)
            data["solution_steps"] = json.loads(data.get("solution_steps") or "[]")
            data["verified_boundaries"] = json.loads(data.get("verified_boundaries") or "{}")
            data["evidence"] = json.loads(data.get("evidence") or "{}")
            return data
        except json.JSONDecodeError:
            print(f"[DPStore] Corrupted JSON fields in row skipped.")
            return None

    def upsert(self, record: dict[str, Any]) -> None:
        payload = self._encode(record)
        now = payload.get("updated_at") or _utc_now()
        created_at = payload.get("created_at") or now
        
        query = """
            INSERT INTO dp_entries (
                normalized_goal, intent_family, environment_signature, state_hash,
                tool_surface, schema_version, status, solution_steps,
                verified_boundaries, confidence, evidence, reward_score,
                use_count, created_at, updated_at, goal_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(
                normalized_goal, intent_family, environment_signature, state_hash, tool_surface, schema_version
            ) DO UPDATE SET
                status = excluded.status,
                solution_steps = excluded.solution_steps,
                verified_boundaries = excluded.verified_boundaries,
                confidence = excluded.confidence,
                evidence = excluded.evidence,
                reward_score = excluded.reward_score,
                use_count = excluded.use_count,
                updated_at = excluded.updated_at,
                goal_hash = excluded.goal_hash
        """
        params = (
            payload["normalized_goal"],
            payload["intent_family"],
            payload["environment_signature"],
            payload["state_hash"],
            payload["tool_surface"],
            payload.get("schema_version", "dp-v2"),
            payload["status"],
            payload["solution_steps"],
            payload["verified_boundaries"],
            float(payload.get("confidence", 0.0)),
            payload["evidence"],
            float(payload.get("reward_score", 0.0)),
            int(payload.get("use_count", 0)),
            created_at,
            now,
            payload["goal_hash"]
        )
        self._execute_query(query, params, commit=True)
        
        if payload.get("status") == "failed":
            self._execute_query(
                """
                INSERT INTO failure_patterns (
                    normalized_goal, intent_family, environment_signature, tool_surface,
                    error_signature, failure_payload, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["normalized_goal"],
                    payload["intent_family"],
                    payload["environment_signature"],
                    payload["tool_surface"],
                    str(payload.get("evidence", ""))[:200],
                    json.dumps(record),
                    now,
                ),
                commit=True
            )

    def lookup_exact(
        self,
        intent_family: str,
        environment_signature: str,
        state_hash: str,
        tool_surface: str,
        normalized_goal: str,
        schema_version: str = "dp-v2",
    ) -> dict[str, Any] | None:
        query = """
            SELECT * FROM dp_entries
            WHERE intent_family = ? AND environment_signature = ? AND state_hash = ?
              AND tool_surface = ? AND normalized_goal = ? AND schema_version = ?
        """
        params = (intent_family, environment_signature, state_hash, tool_surface, normalized_goal, schema_version)
        row = self._execute_query(query, params).fetchone()
        return self._decode(row)

    def lookup_prefix(
        self,
        intent_family: str,
        environment_signature: str,
        tool_surface: str,
        normalized_goal: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        prefix = f"{normalized_goal}%"
        query = """
            SELECT * FROM dp_entries
            WHERE intent_family = ? AND environment_signature = ? AND tool_surface = ?
              AND normalized_goal LIKE ?
            ORDER BY confidence DESC, use_count DESC, updated_at DESC
            LIMIT ?
        """
        params = (intent_family, environment_signature, tool_surface, prefix, limit)
        rows = self._execute_query(query, params).fetchall()
        return [self._decode(row) for row in rows]

    def lookup_related(
        self,
        intent_family: str,
        environment_signature: str,
        tool_surface: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT * FROM dp_entries
            WHERE intent_family = ? AND environment_signature = ? AND tool_surface = ?
            ORDER BY confidence DESC, use_count DESC, updated_at DESC
            LIMIT ?
        """
        params = (intent_family, environment_signature, tool_surface, limit)
        rows = self._execute_query(query, params).fetchall()
        return [self._decode(row) for row in rows]

    def lookup_negative(
        self,
        intent_family: str,
        environment_signature: str,
        tool_surface: str,
        normalized_goal: str,
    ) -> dict[str, Any] | None:
        query = """
            SELECT failure_payload
            FROM failure_patterns
            WHERE intent_family = ? AND environment_signature = ? AND tool_surface = ?
              AND normalized_goal = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """
        params = (intent_family, environment_signature, tool_surface, normalized_goal)
        row = self._execute_query(query, params).fetchone()
        return json.loads(row["failure_payload"]) if row else None

    def increment_use_count(self, record: dict[str, Any]) -> None:
        query = """
            UPDATE dp_entries
            SET use_count = use_count + 1, updated_at = ?
            WHERE normalized_goal = ? AND intent_family = ? AND environment_signature = ?
              AND state_hash = ? AND tool_surface = ? AND schema_version = ?
        """
        params = (
            _utc_now(),
            record["normalized_goal"],
            record["intent_family"],
            record["environment_signature"],
            record["state_hash"],
            record["tool_surface"],
            record.get("schema_version", "dp-v2"),
        )
        self._execute_query(query, params, commit=True)

    def update_confidence(self, record: dict[str, Any], confidence: float, reward_score: float) -> None:
        query = """
            UPDATE dp_entries
            SET confidence = ?, reward_score = ?, updated_at = ?
            WHERE normalized_goal = ? AND intent_family = ? AND environment_signature = ?
              AND state_hash = ? AND tool_surface = ? AND schema_version = ?
        """
        params = (
            confidence,
            reward_score,
            _utc_now(),
            record["normalized_goal"],
            record["intent_family"],
            record["environment_signature"],
            record["state_hash"],
            record["tool_surface"],
            record.get("schema_version", "dp-v2"),
        )
        self._execute_query(query, params, commit=True)

    def evict_stale(self, older_than: str) -> int:
        cursor = self._execute_query(
            "DELETE FROM dp_entries WHERE updated_at < ?",
            (older_than,),
            commit=True
        )
        return cursor.rowcount

    def record_metric_event(self, event_type: str, payload: dict[str, Any], created_at: str | None = None) -> None:
        self._execute_query(
            "INSERT INTO metrics_events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload), created_at or _utc_now()),
            commit=True
        )

    def save_checkpoint(self, checkpoint_id: str, state_payload: dict[str, Any]) -> None:
        query = """
            INSERT INTO dp_checkpoints (checkpoint_id, state_payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(checkpoint_id) DO UPDATE SET
                state_payload = excluded.state_payload,
                updated_at = excluded.updated_at
        """
        self._execute_query(
            query,
            (checkpoint_id, json.dumps(state_payload), _utc_now()),
            commit=True
        )

    def load_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        query = "SELECT state_payload FROM dp_checkpoints WHERE checkpoint_id = ?"
        row = self._execute_query(query, (checkpoint_id,)).fetchone()
        if row:
            try:
                return json.loads(row["state_payload"])
            except json.JSONDecodeError:
                print(f"[DPStore] Corrupted checkpoint record skipped for: {checkpoint_id}")
                return None
        return None

    def delete_stale_checkpoints(self, older_than: str) -> int:
        cursor = self._execute_query(
            "DELETE FROM dp_checkpoints WHERE updated_at < ?",
            (older_than,),
            commit=True
        )
        return cursor.rowcount

    def lookup_by_goal_hash(self, goal_hash: str) -> dict[str, Any] | None:
        query = "SELECT * FROM dp_entries WHERE goal_hash = ?"
        row = self._execute_query(query, (goal_hash,)).fetchone()
        return self._decode(row)

    def lookup_by_hash(self, goal_hash: str) -> dict[str, Any] | None:
        return self.lookup_by_goal_hash(goal_hash)

    def close(self) -> None:
        with self._lock:
            self._conn.close()
