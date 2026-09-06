import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from krytus.config import config

logger = logging.getLogger(__name__)

def _log_info(msg: str, **kwargs):
    logger.info(msg, extra=kwargs)

def _log_error(msg: str, **kwargs):
    logger.error(msg, extra=kwargs)


@contextmanager
def _get_memory_connection():
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


def init_memory_database() -> None:
    with _get_memory_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                note TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_topic ON memories(topic)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)
        """)
        conn.commit()
    _log_info("memory_database_initialized")


def save_memory(topic: str, note: str) -> dict[str, Any]:
    try:
        init_memory_database()
        timestamp = datetime.now().isoformat()
        content = f"Topic: {topic}\nNote: {note}"
        
        with _get_memory_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memories (topic, note, content, timestamp) VALUES (?, ?, ?, ?)",
                (topic, note, content, timestamp)
            )
            conn.commit()

        _log_info("memory_saved", topic=topic)
        return {"success": True, "message": f"Memory saved under topic '{topic}'"}
    except Exception as e:
        _log_error("memory_save_failed", topic=topic, error=str(e))
        return {"success": False, "error": str(e)}


def recall_memory(query: str, n_results: int = 3) -> dict[str, Any]:
    try:
        init_memory_database()
        # Split query into words and search for any of them
        words = query.lower().split()
        if not words:
            return {"success": True, "memories": []}
        
        # Build a query that matches any of the words
        like_clauses = " OR ".join(["content LIKE ?"] * len(words))
        search_terms = [f"%{word}%" for word in words]
        
        with _get_memory_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT topic, note, content, timestamp FROM memories WHERE {like_clauses} ORDER BY timestamp DESC LIMIT ?",
                (*search_terms, n_results)
            )
            rows = cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "content": row["content"],
                "topic": row["topic"],
                "timestamp": row["timestamp"],
            })

        _log_info("memory_recalled", query=query, count=len(memories))
        return {"success": True, "memories": memories}
    except Exception as e:
        _log_error("memory_recall_failed", query=query, error=str(e))
        return {"success": False, "error": str(e)}


def get_recent_memories(n_results: int = 5) -> dict[str, Any]:
    try:
        init_memory_database()
        
        with _get_memory_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT topic, note, content, timestamp FROM memories ORDER BY timestamp DESC LIMIT ?",
                (n_results,)
            )
            rows = cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "content": row["content"],
                "topic": row["topic"],
                "timestamp": row["timestamp"],
            })

        _log_info("recent_memories_fetched", count=len(memories))
        return {"success": True, "memories": memories}
    except Exception as e:
        _log_error("recent_memories_failed", error=str(e))
        return {"success": False, "error": str(e)}
