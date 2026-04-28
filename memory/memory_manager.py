import json
import sqlite3
import time
import chromadb
from datetime import datetime, timezone
from threading import Lock
from pathlib import Path
import sys

from memory.embeddings import get_embedding_function
from memory.consolidator import MemoryConsolidator
from memory.dp_store import DPStore
from memory.profiles import ProfileManager
from memory.schema import (
    MemoryTier, MemorySensitivity,
    PERSIST_TIERS, PROFILE_TIERS, NEVER_PERSIST_TIERS,
    SECRET_SENSITIVITY, PromotionRule, DEFAULT_PROMOTION_RULES,
)
from buddy_logging import get_logger

logger = get_logger("memory.manager")

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR         = get_base_dir()
MEMORY_DIR       = BASE_DIR / "memory"
SQLITE_PATH      = MEMORY_DIR / "memory.db"
CHROMA_PATH      = MEMORY_DIR / "chroma_db"
JSON_MEMORY_PATH = MEMORY_DIR / "long_term.json"
PROFILES_DIR = MEMORY_DIR / "profiles"
LONG_TERM_COLLECTION = "long_term_memory_v2"
LOCAL_FILES_COLLECTION = "local_files_v2"
EPISODES_COLLECTION = "task_episodes_v2"

_lock = Lock()
embedding_func = get_embedding_function()


# ── Session Memory (in-memory only, dies with process) ──────
class SessionMemory:
    """In-memory store for session-scoped facts. Never persisted."""

    def __init__(self):
        self._store: dict[str, dict[str, str]] = {}
        self._lock = Lock()

    def set(self, category: str, key: str, value: str) -> None:
        with self._lock:
            self._store.setdefault(category, {})[key] = value

    def get(self, category: str, key: str) -> str | None:
        with self._lock:
            return self._store.get(category, {}).get(key)

    def get_all(self) -> dict[str, dict[str, str]]:
        with self._lock:
            return {c: dict(entries) for c, entries in self._store.items()}

    def delete(self, category: str, key: str) -> bool:
        with self._lock:
            cat = self._store.get(category)
            if cat and key in cat:
                del cat[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# ── Ephemeral Secret Store (TTL-based, never on disk) ───────
class EphemeralStore:
    """In-memory store for secrets with automatic expiration."""

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}  # key -> (value, expires_at)
        self._lock = Lock()

    def set(self, key: str, value: str, ttl_seconds: float = 300.0) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl_seconds)

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def purge_expired(self) -> int:
        """Remove expired entries, return count purged."""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
            return len(expired)


class HybridMemory:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)

        # ── Tier-specific stores ──
        self.session_memory = SessionMemory()
        self.ephemeral_store = EphemeralStore()
        self.promotion_rules: list[PromotionRule] = list(DEFAULT_PROMOTION_RULES)

        # SQLite Setup
        self.conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                category TEXT,
                key TEXT,
                value TEXT,
                updated TEXT,
                tier TEXT DEFAULT 'long_term',
                sensitivity TEXT DEFAULT 'normal',
                times_confirmed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT '',
                PRIMARY KEY (category, key)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_episodes (
                plan_id TEXT PRIMARY KEY,
                goal TEXT,
                timestamp TEXT,
                success BOOLEAN,
                nodes_summary TEXT,
                learned_lesson TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dp_subproblems (
                dp_key TEXT PRIMARY KEY,
                intent_family TEXT,
                surface TEXT,
                environment_signature TEXT,
                goal_hash TEXT,
                normalized_goal TEXT,
                solution_type TEXT,
                solution_payload TEXT,
                status TEXT,
                confidence REAL,
                verified_count INTEGER,
                last_completed_step INTEGER,
                artifacts TEXT,
                evidence TEXT,
                last_used_at TEXT,
                created_at TEXT,
                stale_after TEXT,
                negative_reason TEXT,
                reuse_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

        # ── Migrate tier columns if missing ──
        self._migrate_tier_columns()

        self.dp_store = DPStore(SQLITE_PATH)
        self.profile_manager = ProfileManager(PROFILES_DIR)
        self.consolidator = MemoryConsolidator(self.profile_manager)

        # ChromaDB Setup
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.chroma_client.get_or_create_collection(
            name=LONG_TERM_COLLECTION,
            embedding_function=embedding_func
        )

        # Local Files Collection (RAG)
        self.local_files_collection = self.chroma_client.get_or_create_collection(
            name=LOCAL_FILES_COLLECTION,
            embedding_function=embedding_func
        )

        # Episodic Memory (Task Experience)
        self.episodes_collection = self.chroma_client.get_or_create_collection(
            name=EPISODES_COLLECTION,
            embedding_function=embedding_func
        )

        # Run migration if needed
        self.migrate_json_if_exists()

    # ── Schema migration ─────────────────────────────────
    def _migrate_tier_columns(self) -> None:
        """Add tier/sensitivity/times_confirmed/created_at columns if missing."""
        try:
            cols = {row[1] for row in self.conn.execute("PRAGMA table_info(memory)").fetchall()}
            migrations = [
                ("tier", "TEXT DEFAULT 'long_term'"),
                ("sensitivity", "TEXT DEFAULT 'normal'"),
                ("times_confirmed", "INTEGER DEFAULT 0"),
                ("created_at", "TEXT DEFAULT ''"),
            ]
            for col_name, col_def in migrations:
                if col_name not in cols:
                    self.conn.execute(f"ALTER TABLE memory ADD COLUMN {col_name} {col_def}")
                    logger.info("Migrated memory table: added column %s", col_name)
            self.conn.commit()
        except Exception as exc:
            logger.warning("Tier column migration skipped: %s", exc)

    def migrate_json_if_exists(self):
        with _lock:
            if JSON_MEMORY_PATH.exists():
                logger.info("🚚 Migrating data from %s...", JSON_MEMORY_PATH.name)
                try:
                    data = json.loads(JSON_MEMORY_PATH.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        for category, items in data.items():
                            if not isinstance(items, dict): continue
                            for key, entry in items.items():
                                val = entry.get("value") if isinstance(entry, dict) else entry
                                updated = entry.get("updated", datetime.now().strftime("%Y-%m-%d")) if isinstance(entry, dict) else datetime.now().strftime("%Y-%m-%d")
                                if val:
                                    self.update_entry(category, key, val, updated, skip_save=True)
                        self.conn.commit()
                    
                        # Backup and remove old JSON
                        backup_path = JSON_MEMORY_PATH.with_suffix(".json.bak")
                        JSON_MEMORY_PATH.rename(backup_path)
                        logger.info("✅ Migration complete. Old file backed up to %s", backup_path.name)
                except Exception as e:
                    logger.error("❌ Migration failed: %s", e)

    def update_entry(
        self,
        category: str,
        key: str,
        value: str,
        updated: str = None,
        skip_save: bool = False,
        tier: MemoryTier = MemoryTier.LONG_TERM,
        sensitivity: MemorySensitivity = MemorySensitivity.NORMAL,
    ):
        if updated is None:
            updated = datetime.now().strftime("%Y-%m-%d")

        # ── SECRET sensitivity: never persist ──
        if sensitivity == SECRET_SENSITIVITY:
            self.ephemeral_store.set(f"{category}/{key}", value, ttl_seconds=300.0)
            logger.debug("SECRET entry %s/%s stored ephemerally only", category, key)
            return

        # ── SESSION tier: in-memory only ──
        if tier == MemoryTier.SESSION:
            self.session_memory.set(category, key, value)
            return

        # ── EPHEMERAL tier: TTL store, no disk ──
        if tier == MemoryTier.EPHEMERAL:
            self.ephemeral_store.set(f"{category}/{key}", value, ttl_seconds=300.0)
            return

        # ── PREFERENCE / LONG_TERM: persist to SQLite + ChromaDB ──
        now_iso = datetime.now().isoformat()
        with _lock:
            # Check if entry exists to preserve times_confirmed
            existing = self.cursor.execute(
                "SELECT times_confirmed FROM memory WHERE category = ? AND key = ?",
                (category, key),
            ).fetchone()
            prev_confirmed = existing[0] if existing else 0

            self.cursor.execute(
                "INSERT OR REPLACE INTO memory "
                "(category, key, value, updated, tier, sensitivity, times_confirmed, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM memory WHERE category = ? AND key = ?), ?))",
                (category, key, value, updated, tier.value, sensitivity.value,
                 prev_confirmed + 1, category, key, now_iso),
            )
            if not skip_save:
                self.conn.commit()

            # Update ChromaDB
            doc_id = f"{category}/{key}"
            content = f"Category: {category}. Key: {key}. Value: {value}"
            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{"category": category, "key": key, "updated": updated, "tier": tier.value}],
            )

            # ── Profile writes gated by tier ──
            if tier in PROFILE_TIERS:
                try:
                    self.profile_manager.update_user(category, key, value)
                except Exception as exc:
                    logger.debug("Profile update failed for %s/%s: %s", category, key, exc)

    def get_all_memory(self) -> dict:
        memory_dict = {
            "identity": {},
            "preferences": {},
            "projects": {},
            "relationships": {},
            "wishes": {},
            "notes": {},
        }
        with _lock:
            self.cursor.execute("SELECT category, key, value, updated FROM memory")
            rows = self.cursor.fetchall()
            for cat, key, val, updated in rows:
                if cat not in memory_dict:
                    memory_dict[cat] = {}
                memory_dict[cat][key] = {"value": val, "updated": updated}
        return memory_dict

    # ── Tier-aware queries ────────────────────────────────
    def get_session_context(self) -> dict[str, dict[str, str]]:
        """Return session-only facts (never persisted)."""
        return self.session_memory.get_all()

    def get_ephemeral(self, key: str) -> str | None:
        """Retrieve an ephemeral secret (returns None if expired)."""
        return self.ephemeral_store.get(key)

    def store_ephemeral(self, key: str, value: str, ttl_seconds: float = 300.0) -> None:
        """Store a secret with automatic expiration. Never written to disk."""
        self.ephemeral_store.set(key, value, ttl_seconds)

    def get_entries_by_tier(self, tier: MemoryTier) -> list[dict]:
        """Get all persisted entries for a given tier."""
        with _lock:
            rows = self.cursor.execute(
                "SELECT category, key, value, updated, tier, sensitivity, times_confirmed "
                "FROM memory WHERE tier = ?",
                (tier.value,),
            ).fetchall()
            return [
                {
                    "category": r[0], "key": r[1], "value": r[2],
                    "updated": r[3], "tier": r[4], "sensitivity": r[5],
                    "times_confirmed": r[6],
                }
                for r in rows
            ]

    def promote_if_eligible(self) -> list[tuple[str, str, str, str]]:
        """
        Check all entries against promotion rules and upgrade tier if eligible.
        Returns list of (category, key, old_tier, new_tier) for promoted entries.
        """
        promoted: list[tuple[str, str, str, str]] = []
        with _lock:
            for rule in self.promotion_rules:
                sql = (
                    "SELECT category, key, tier, times_confirmed, created_at "
                    "FROM memory WHERE tier = ?"
                )
                rows = self.cursor.execute(sql, (rule.from_tier.value,)).fetchall()
                for cat, key, current_tier, confirmed, created_at in rows:
                    # Check category filter
                    if rule.requires_categories and cat not in rule.requires_categories:
                        continue
                    # Check confirmation threshold
                    if confirmed < rule.min_confirmations:
                        continue
                    # Check age
                    if created_at:
                        try:
                            created = datetime.fromisoformat(created_at)
                            age_hours = (datetime.now() - created).total_seconds() / 3600.0
                            if age_hours < rule.min_age_hours:
                                continue
                        except (ValueError, TypeError):
                            pass  # can't parse, allow promotion
                    # Promote
                    self.cursor.execute(
                        "UPDATE memory SET tier = ? WHERE category = ? AND key = ?",
                        (rule.to_tier.value, cat, key),
                    )
                    promoted.append((cat, key, current_tier, rule.to_tier.value))
            if promoted:
                self.conn.commit()
                logger.info("Promoted %d memory entries", len(promoted))
        return promoted


    def delete_entry(self, category: str, key: str):
        with _lock:
            self.cursor.execute("DELETE FROM memory WHERE category = ? AND key = ?", (category, key))
            self.conn.commit()
            doc_id = f"{category}/{key}"
            try:
                self.collection.delete(ids=[doc_id])
            except:
                pass

    def search_semantic(self, query: str, n_results: int = 5):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def search_local_files(self, query: str, n_results: int = 5):
        results = self.local_files_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def save_episode(self, episode_data: dict):
        plan_id = episode_data.get("plan_id")
        goal = episode_data.get("goal")
        timestamp = episode_data.get("timestamp", datetime.now().isoformat())
        success = episode_data.get("success", False)
        nodes_summary = json.dumps(episode_data.get("nodes_summary", []))
        learned_lesson = episode_data.get("learned_lesson", "")

        with _lock:
            self.cursor.execute(
                "INSERT OR REPLACE INTO task_episodes (plan_id, goal, timestamp, success, nodes_summary, learned_lesson) VALUES (?, ?, ?, ?, ?, ?)",
                (plan_id, goal, timestamp, success, nodes_summary, learned_lesson)
            )
            self.conn.commit()

            # Add to Chroma for semantic search
            content = f"Task Goal: {goal}. Success: {success}. Lesson: {learned_lesson}"
            self.episodes_collection.upsert(
                ids=[plan_id],
                documents=[content],
                metadatas=[{"plan_id": plan_id, "success": success, "timestamp": timestamp}]
            )

    def search_episodes(self, query: str, n_results: int = 3):
        return self.episodes_collection.query(
            query_texts=[query],
            n_results=n_results
        )

    def get_user_profile(self) -> str:
        return self.profile_manager.load_user_context()

    def get_soul_profile(self) -> str:
        return self.profile_manager.load_soul_context()

    def update_heartbeat(self, status: dict) -> None:
        self.profile_manager.write_heartbeat(status)

    def consolidate(self) -> None:
        facts: dict[str, dict[str, str]] = {}
        for category, entries in self.get_all_memory().items():
            normalized_entries: dict[str, str] = {}
            for key, value in entries.items():
                if isinstance(value, dict):
                    normalized_entries[key] = str(value.get("value", ""))
                else:
                    normalized_entries[key] = str(value)
            if normalized_entries:
                facts[category] = normalized_entries
        self.consolidator.consolidate(facts)

    def save_dp_entry(self, record: dict):
        self.dp_store.upsert(
            {
                "normalized_goal": record.get("normalized_goal", ""),
                "intent_family": record.get("intent_family", ""),
                "environment_signature": record.get("environment_signature", ""),
                "state_hash": record.get("state_hash", record.get("goal_hash", "")),
                "tool_surface": record.get("tool_surface", record.get("surface", "generic")),
                "schema_version": record.get("schema_version", "dp-v2"),
                "status": record.get("status", ""),
                "solution_steps": record.get("solution_steps")
                or record.get("solution_payload", {}).get("steps")
                or record.get("solution_payload", {}).get("nodes")
                or [],
                "verified_boundaries": record.get("verified_boundaries")
                or {
                    "solution_type": record.get("solution_type", "task_plan"),
                    "last_completed_step": record.get("last_completed_step", 0),
                },
                "confidence": float(record.get("confidence", 1.0)),
                "evidence": record.get("evidence", {}),
                "reward_score": float(record.get("reward_score", 0.0)),
                "use_count": int(record.get("use_count", record.get("reuse_count", 0))),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at", record.get("last_used_at")),
            }
        )

    def get_dp_entry(self, dp_key: str):
        return self.dp_store.lookup_by_goal_hash(dp_key)

    def find_dp_candidates(self, intent_family: str, surface: str, environment_signature: str, limit: int = 10):
        return self.dp_store.lookup_related(intent_family, environment_signature, surface, limit)

    def bump_dp_usage(self, dp_key: str, last_used_at: str, reuse_count: int):
        record = self.get_dp_entry(dp_key)
        if record is None:
            return
        self.dp_store.increment_use_count(record)

    @staticmethod
    def _decode_dp_row(row):
        return {
            "dp_key": row[0],
            "intent_family": row[1],
            "surface": row[2],
            "environment_signature": row[3],
            "goal_hash": row[4],
            "normalized_goal": row[5],
            "solution_type": row[6],
            "solution_payload": json.loads(row[7] or "{}"),
            "status": row[8],
            "confidence": row[9],
            "verified_count": row[10],
            "last_completed_step": row[11],
            "artifacts": json.loads(row[12] or "{}"),
            "evidence": json.loads(row[13] or "{}"),
            "last_used_at": row[14],
            "created_at": row[15],
            "stale_after": row[16],
            "negative_reason": row[17],
            "reuse_count": row[18],
        }

# Initialize Singleton
_hybrid_memory = None

def get_memory():
    global _hybrid_memory
    if _hybrid_memory is None:
        _hybrid_memory = HybridMemory()
    return _hybrid_memory

def load_memory() -> dict:
    return get_memory().get_all_memory()

def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    
    mem = get_memory()
    
    def recursive_update(updates, current_cat=None):
        for key, value in updates.items():
            if value is None: continue
            
            if current_cat is None:
                # Top level is category
                if isinstance(value, dict):
                    recursive_update(value, key)
            else:
                # key is the memory key, current_cat is the category
                if isinstance(value, dict) and "value" not in value:
                    # Nested dict, but we'll flatten it or handle as sub-category?
                    # Original code supported deep nesting, but let's stick to category/key
                    # for the DB. If it's a dict without "value", we treat it as a sub-key prefix.
                    for sub_k, sub_v in value.items():
                        recursive_update({f"{key}_{sub_k}": sub_v}, current_cat)
                else:
                    new_val = value["value"] if isinstance(value, dict) else value
                    updated = value.get("updated") if isinstance(value, dict) else None
                    mem.update_entry(current_cat, key, str(new_val), updated)

    recursive_update(memory_update)
    return load_memory()

def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    lines = []
    
    # We can use the memory dict provided or fetch directly from DB.
    # To keep it consistent with format_memory_for_prompt signature:
    
    identity  = memory.get("identity", {})
    id_fields = ["name", "age", "birthday", "city", "job", "language", "school", "nationality"]
    for field in id_fields:
        entry = identity.get(field)
        if entry:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"{field.title()}: {val}")
    for key, entry in identity.items():
        if key in id_fields:
            continue
        val = entry.get("value") if isinstance(entry, dict) else entry
        if val:
            lines.append(f"{key.replace('_', ' ').title()}: {val}")

    sections = [
        ("preferences", "Preferences:"),
        ("projects", "Active Projects / Goals:"),
        ("relationships", "People in their life:"),
        ("wishes", "Wishes / Plans / Wants:"),
        ("notes", "Other notes:")
    ]

    for cat_key, title in sections:
        items = memory.get(cat_key, {})
        if items:
            lines.append("")
            lines.append(title)
            for key, entry in list(items.items()):
                val = entry.get("value") if isinstance(entry, dict) else entry
                if val:
                    # Don't repeat title if it's already descriptive
                    lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    if not lines:
        return ""

    header = "[HYBRID MEMORY ENGINE — Contextually Retrieved Facts]\n"
    result = header + "\n".join(lines)
    
    # Since we use DB now, we can afford slightly larger prompts if needed,
    # but let's keep it reasonable.
    if len(result) > 4000:
        result = result[:3997] + "…"

    return result + "\n"

def remember(key: str, value: str, category: str = "notes") -> str:
    update_memory({category: {key: value}})
    return f"Remembered: {category}/{key} = {value}"

def forget(key: str, category: str = "notes") -> str:
    get_memory().delete_entry(category, key)
    return f"Forgotten: {category}/{key}"

forget_memory = forget

# Semantic search helper for use in other parts of the system
def semantic_search(query: str, n: int = 5):
    return get_memory().search_semantic(query, n)

def search_local_files(query: str, n: int = 5):
    return get_memory().search_local_files(query, n)
