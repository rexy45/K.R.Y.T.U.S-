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
def _get_connection():
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    # Always ensure table exists (IF NOT EXISTS handles idempotency)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            due_at TEXT NOT NULL,
            delivered INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reminders_due_delivered
        ON reminders(due_at, delivered)
    """)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    with _get_connection() as conn:
        pass  # Ensures table exists
    _log_info("database_initialized")


def set_reminder(minutes_from_now: int, message: str) -> dict[str, Any]:
    try:
        due_at = datetime.now().replace(microsecond=0).isoformat()
        due_at_dt = datetime.fromisoformat(due_at)
        due_at_dt = due_at_dt.replace(second=0, microsecond=0)
        from datetime import timedelta
        due_at_dt = due_at_dt + timedelta(minutes=minutes_from_now)
        due_at_str = due_at_dt.isoformat()

        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (message, due_at, delivered) VALUES (?, ?, 0)",
                (message, due_at_str)
            )
            reminder_id = cursor.lastrowid
            conn.commit()

        _log_info("reminder_set", reminder_id=reminder_id, due_at=due_at_str)
        return {"success": True, "reminder_id": reminder_id, "due_at": due_at_str, "message": "Reminder set"}
    except Exception as e:
        _log_error("reminder_set_failed", error=str(e))
        return {"success": False, "error": str(e)}


def get_pending_reminders() -> list[dict[str, Any]]:
    now = datetime.now().replace(microsecond=0).isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, message, due_at FROM reminders WHERE due_at <= ? AND delivered = 0 ORDER BY due_at",
            (now,)
        )
        rows = cursor.fetchall()

    return [{"id": row["id"], "message": row["message"], "due_at": row["due_at"]} for row in rows]


def mark_reminder_delivered(reminder_id: int) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reminders SET delivered = 1 WHERE id = ? AND delivered = 0",
            (reminder_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_all_reminders() -> list[dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, message, due_at, delivered, created_at FROM reminders ORDER BY due_at")
        rows = cursor.fetchall()

    return [dict(row) for row in rows]
