import sqlite3
from pathlib import Path
from uuid import uuid4


# ---------------------------------------
# Database
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "chat_history.db"


# ---------------------------------------
# Connection
# ---------------------------------------

def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------
# Initialize database
# ---------------------------------------

def init_chat_history():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
        )
        """
    )

    connection.commit()

    connection.close()


# ---------------------------------------
# Conversations
# ---------------------------------------

def create_conversation() -> str:

    conversation_id = str(uuid4())

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO conversations (id)
        VALUES (?)
        """,
        (conversation_id,),
    )

    connection.commit()

    connection.close()

    return conversation_id


def conversation_exists(
    conversation_id: str,
) -> bool:

    connection = get_connection()

    result = connection.execute(
        """
        SELECT id
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    ).fetchone()

    connection.close()

    return result is not None


# ---------------------------------------
# Messages
# ---------------------------------------

def add_message(
    conversation_id: str,
    role: str,
    content: str,
):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO messages (
            conversation_id,
            role,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
        ),
    )

    connection.commit()

    connection.close()


def get_messages(
    conversation_id: str,
):

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,),
    ).fetchall()

    connection.close()

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]