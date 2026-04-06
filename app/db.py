"""Lightweight SQLite helpers for chat thread & message persistence."""

import sqlite3
from app.config import settings

DB_PATH = settings.SQLITE_DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create threads & messages tables if they don't exist."""
    conn = _conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL DEFAULT 'New Chat',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id   TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
            role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);
        """
    )
    conn.close()


def create_thread(thread_id: str, title: str = "New Chat"):
    conn = _conn()
    conn.execute("INSERT INTO threads (id, title) VALUES (?, ?)", (thread_id, title))
    conn.commit()
    conn.close()


def list_threads():
    conn = _conn()
    rows = conn.execute("SELECT id, title, created_at FROM threads ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_thread(thread_id: str):
    conn = _conn()
    row = conn.execute("SELECT id, title, created_at FROM threads WHERE id = ?", (thread_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_thread_title(thread_id: str, title: str):
    conn = _conn()
    conn.execute("UPDATE threads SET title = ? WHERE id = ?", (title, thread_id))
    conn.commit()
    conn.close()


def delete_thread(thread_id: str):
    conn = _conn()
    conn.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    conn.commit()
    conn.close()


def save_message(thread_id: str, role: str, content: str):
    conn = _conn()
    conn.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content),
    )
    conn.commit()
    conn.close()


def get_messages(thread_id: str):
    conn = _conn()
    rows = conn.execute(
        "SELECT id, thread_id, role, content, created_at FROM messages WHERE thread_id = ? ORDER BY created_at ASC",
        (thread_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
