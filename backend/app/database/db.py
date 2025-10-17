import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "./data/conversations.db"

#to keep memory of past conversations
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_conversation(session_id, video_id, question, answer):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, video_id, question, answer) VALUES (?, ?, ?, ?)",
            (session_id, video_id, question, answer)
        )
        conn.commit()

def get_conversation_history(session_id, limit=10):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT question, answer, created_at FROM conversations WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

def clear_session(session_id):
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        conn.commit()

# Initialize the database when this file is imported
init_db()
