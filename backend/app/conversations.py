"""Conversation/message persistence shared by the /chat and /history routers.

Conversations are private to their owner by default; a conversation
flagged `is_shared` is visible to every user (the household "family
thread" case) rather than just the person who started it.
"""
from dataclasses import dataclass

from fastapi import HTTPException

from app.db import cursor, now


@dataclass
class Conversation:
    id: int
    owner_user_id: int
    is_shared: bool
    title: str
    created_at: float


def create_conversation(owner_user_id: int, is_shared: bool, title: str = "New chat") -> Conversation:
    with cursor() as cur:
        cur.execute(
            "INSERT INTO conversations (owner_user_id, is_shared, title, created_at) VALUES (?, ?, ?, ?)",
            (owner_user_id, int(is_shared), title, now()),
        )
        return Conversation(cur.lastrowid, owner_user_id, is_shared, title, now())


def _row_to_conversation(row) -> Conversation:
    return Conversation(row["id"], row["owner_user_id"], bool(row["is_shared"]), row["title"], row["created_at"])


def get_conversation_for_user(conversation_id: int, user_id: int) -> Conversation:
    """Fetch a conversation, enforcing that the user may see it (owns it, or it's shared)."""
    with cursor() as cur:
        row = cur.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation = _row_to_conversation(row)
    if not conversation.is_shared and conversation.owner_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    return conversation


def list_conversations_for_user(user_id: int) -> list[Conversation]:
    """A user's own conversations plus every shared one, newest first."""
    with cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM conversations WHERE owner_user_id = ? OR is_shared = 1 ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [_row_to_conversation(row) for row in rows]


def add_message(conversation_id: int, role: str, content: str) -> None:
    with cursor() as cur:
        cur.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, now()),
        )


def get_messages(conversation_id: int) -> list[dict]:
    with cursor() as cur:
        rows = cur.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"], "created_at": row["created_at"]} for row in rows]


def set_title_from_first_message(conversation_id: int, message: str) -> None:
    title = message.strip().splitlines()[0][:60] if message.strip() else "New chat"
    with cursor() as cur:
        cur.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
