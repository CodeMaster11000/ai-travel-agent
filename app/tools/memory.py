import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "travel_memory.db"


def initialize_memory() -> None:
    """Create the SQLite memory store when first used."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, memory_key)
            )
        """)


def _validate_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be empty.")
    if len(value.strip()) > 500:
        raise ValueError(f"{label} must be 500 characters or fewer.")
    return value.strip()


def save_memory(user_id: str, memory_key: str, memory_value: str) -> dict:
    """Save or update one preference for a user."""
    user_id = _validate_text(user_id, "user_id")
    memory_key = _validate_text(memory_key, "memory_key").casefold()
    memory_value = _validate_text(memory_value, "memory_value")
    initialize_memory()
    timestamp = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            INSERT INTO memories (user_id, memory_key, memory_value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, memory_key) DO UPDATE SET
                memory_value = excluded.memory_value,
                updated_at = excluded.updated_at
        """, (user_id, memory_key, memory_value, timestamp))

    return {"success": True, "message": "Memory saved.", "key": memory_key, "value": memory_value}


def get_memories(user_id: str) -> list[dict]:
    """Retrieve preferences for one user."""
    user_id = _validate_text(user_id, "user_id")
    initialize_memory()
    with sqlite3.connect(DB_FILE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT memory_key, memory_value, updated_at
            FROM memories WHERE user_id = ? ORDER BY memory_key
        """, (user_id,)).fetchall()
    return [dict(row) for row in rows]


def delete_memory(user_id: str, memory_key: str) -> dict:
    """Delete a saved preference."""
    user_id = _validate_text(user_id, "user_id")
    memory_key = _validate_text(memory_key, "memory_key").casefold()
    initialize_memory()
    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.execute(
            "DELETE FROM memories WHERE user_id = ? AND memory_key = ?",
            (user_id, memory_key),
        )
    deleted = cursor.rowcount > 0
    return {"success": deleted, "message": "Memory deleted." if deleted else "Memory not found."}


if __name__ == "__main__":
    import json
    demo_user = "demo_user"
    print(json.dumps(save_memory(demo_user, "preferred_destination", "Jaipur"), indent=2))
    print(json.dumps(get_memories(demo_user), indent=2))
    print(json.dumps(delete_memory(demo_user, "preferred_destination"), indent=2))
