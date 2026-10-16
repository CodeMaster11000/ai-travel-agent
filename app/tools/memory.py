### FILE: app/tools/memory.py
"""Thread-safe SQLite persistent memory store with WAL enabled."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from app.config import MEMORY_DB_FILE

# FIX B5: Ensure WAL mode and busy timeout to prevent 'database is locked' errors.
def get_db_connection(db_path: Path = MEMORY_DB_FILE) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_memory(db_path: Path = MEMORY_DB_FILE) -> None:
    """Initialize memories schema if not present."""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, memory_key)
            )
        """)
        conn.commit()


def _validate_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be empty.")
    if len(value.strip()) > 500:
        raise ValueError(f"{label} must be 500 characters or fewer.")
    return value.strip()


def save_memory(user_id: str, memory_key: str, memory_value: str, db_path: Path = MEMORY_DB_FILE) -> dict:
    """Save or update a persistent user preference."""
    clean_user = _validate_text(user_id, "user_id")
    clean_key = _validate_text(memory_key, "memory_key").casefold()
    clean_val = _validate_text(memory_value, "memory_value")
    
    initialize_memory(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_db_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO memories (user_id, memory_key, memory_value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, memory_key) DO UPDATE SET
                memory_value = excluded.memory_value,
                updated_at = excluded.updated_at
        """, (clean_user, clean_key, clean_val, timestamp))
        conn.commit()

    return {"success": True, "message": "Memory saved.", "key": clean_key, "value": clean_val}


def get_memories(user_id: str, db_path: Path = MEMORY_DB_FILE) -> list[dict]:
    """Retrieve all preferences stored for a specific traveler."""
    clean_user = _validate_text(user_id, "user_id")
    initialize_memory(db_path)
    with get_db_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT memory_key, memory_value, updated_at
            FROM memories WHERE user_id = ? ORDER BY memory_key
        """, (clean_user,)).fetchall()
    return [dict(row) for row in rows]


def delete_memory(user_id: str, memory_key: str, db_path: Path = MEMORY_DB_FILE) -> dict:
    """Remove a preference key for a traveler."""
    clean_user = _validate_text(user_id, "user_id")
    clean_key = _validate_text(memory_key, "memory_key").casefold()
    initialize_memory(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM memories WHERE user_id = ? AND memory_key = ?",
            (clean_user, clean_key),
        )
        conn.commit()
    deleted = cursor.rowcount > 0
    return {"success": deleted, "message": "Memory deleted." if deleted else "Memory not found."}