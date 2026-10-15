import json
import os
import sqlite3
from config import MAX_HISTORY_TURNS

DB_DIR = os.path.dirname(__file__)


def _db_path():
    if "PYTEST_CURRENT_TEST" in os.environ:
        return os.path.join(DB_DIR, "..", "test_state.db")
    return os.path.join(DB_DIR, "..", "state.db")


_in_memory_test_conn = None


def _get_conn():
    global _in_memory_test_conn
    if "PYTEST_CURRENT_TEST" in os.environ:
        # Use a persistent connection to in-memory DB during pytest
        if _in_memory_test_conn is None:
            _in_memory_test_conn = sqlite3.connect(":memory:")
            with _in_memory_test_conn:
                _in_memory_test_conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_messages (
                        message_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                _in_memory_test_conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        sender_id TEXT PRIMARY KEY,
                        history_json TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        return _in_memory_test_conn

    conn = sqlite3.connect(_db_path())
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                sender_id TEXT PRIMARY KEY,
                history_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    return conn


def clear_conversation_history(sender_id=None):
    """Utility to clear conversation history for testing or resetting."""
    try:
        conn = _get_conn()
        with conn:
            if sender_id:
                conn.execute("DELETE FROM conversation_history WHERE sender_id = ?", (sender_id,))
            else:
                conn.execute("DELETE FROM conversation_history")
    except Exception as e:
        print(f"[State] Error clearing history: {e}")


def get_history(sender_id):
    """Returns this sender's history as a list of OpenAI-style messages,
    e.g. [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT history_json FROM conversation_history WHERE sender_id = ?",
            (sender_id,),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print(f"[State] Error getting history: {e}")
    return []


def _save_history(sender_id, history):
    trimmed = history[-(MAX_HISTORY_TURNS * 2):]
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO conversation_history (sender_id, history_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(sender_id) DO UPDATE SET
                    history_json = excluded.history_json,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (sender_id, json.dumps(trimmed)),
            )
    except Exception as e:
        print(f"[State] Error saving history: {e}")


def append_turn(sender_id, user_message, model_reply):
    history = get_history(sender_id)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": model_reply})
    _save_history(sender_id, history)


def append_system_note(sender_id, note_text):
    history = get_history(sender_id)
    history.append({"role": "system", "content": note_text})
    _save_history(sender_id, history)


def is_processed(message_id):
    if not message_id:
        return False
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ?",
            (str(message_id),),
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"[State] Error checking processed: {e}")
        return False


def mark_processed(message_id):
    if not message_id:
        return
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
                (str(message_id),),
            )
    except Exception as e:
        print(f"[State] Error marking processed: {e}")


def seed_processed_ids(message_ids):
    count = 0
    try:
        conn = _get_conn()
        with conn:
            for message_id in message_ids:
                if message_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
                        (str(message_id),),
                    )
                    count += 1
        print(f"[State] Seeded {count} existing message IDs as processed.")
    except Exception as e:
        print(f"[State] Error seeding processed IDs: {e}")
