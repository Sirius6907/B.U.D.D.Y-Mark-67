import json
import sqlite3
import chromadb
from datetime import datetime
from threading import Lock
from pathlib import Path
import sys

from memory.embeddings import get_embedding_function

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR         = get_base_dir()
MEMORY_DIR       = BASE_DIR / "memory"
SQLITE_PATH      = MEMORY_DIR / "memory.db"
CHROMA_PATH      = MEMORY_DIR / "chroma_db"
JSON_MEMORY_PATH = MEMORY_DIR / "long_term.json"
LONG_TERM_COLLECTION = "long_term_memory_v2"
LOCAL_FILES_COLLECTION = "local_files_v2"
EPISODES_COLLECTION = "task_episodes_v2"

_lock = Lock()
embedding_func = get_embedding_function()

class HybridMemory:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        
        # SQLite Setup
        self.conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                category TEXT,
                key TEXT,
                value TEXT,
                updated TEXT,
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
        self.conn.commit()

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

    def migrate_json_if_exists(self):
        if JSON_MEMORY_PATH.exists():
            print(f"[Memory] 🚚 Migrating data from {JSON_MEMORY_PATH.name}...")
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
                print(f"[Memory] ✅ Migration complete. Old file backed up to {backup_path.name}")
            except Exception as e:
                print(f"[Memory] ❌ Migration failed: {e}")

    def update_entry(self, category: str, key: str, value: str, updated: str = None, skip_save: bool = False):
        if updated is None:
            updated = datetime.now().strftime("%Y-%m-%d")
        
        with _lock:
            # Update SQLite
            self.cursor.execute(
                "INSERT OR REPLACE INTO memory (category, key, value, updated) VALUES (?, ?, ?, ?)",
                (category, key, value, updated)
            )
            if not skip_save:
                self.conn.commit()

            # Update ChromaDB
            # We use category/key as the ID
            doc_id = f"{category}/{key}"
            content = f"Category: {category}. Key: {key}. Value: {value}"
            
            # Upsert in Chroma
            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{"category": category, "key": key, "updated": updated}]
            )

    def get_all_memory(self) -> dict:
        memory_dict = {
            "identity": {},
            "preferences": {},
            "projects": {},
            "relationships": {},
            "wishes": {},
            "notes": {}
        }
        with _lock:
            self.cursor.execute("SELECT category, key, value, updated FROM memory")
            rows = self.cursor.fetchall()
            for cat, key, val, updated in rows:
                if cat not in memory_dict:
                    memory_dict[cat] = {}
                memory_dict[cat][key] = {"value": val, "updated": updated}
        return memory_dict

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
