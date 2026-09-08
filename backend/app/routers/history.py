"""GET /history and /history/{id} — a user's conversations and their messages."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import User, get_current_user
from app.conversations import get_conversation_for_user, get_messages, list_conversations_for_user

router = APIRouter(prefix="/history")


class ConversationSummary(BaseModel):
    id: int
    title: str
    is_shared: bool
    created_at: float


class Message(BaseModel):
    role: str
    content: str
    created_at: float


class ConversationDetail(BaseModel):
    id: int
    title: str
    is_shared: bool
    messages: list[Message]


@router.get("", response_model=list[ConversationSummary])
async def list_history(current_user: User = Depends(get_current_user)) -> list[ConversationSummary]:
    conversations = list_conversations_for_user(current_user.id)
    return [
        ConversationSummary(id=c.id, title=c.title, is_shared=c.is_shared, created_at=c.created_at)
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_history(conversation_id: int, current_user: User = Depends(get_current_user)) -> ConversationDetail:
    conversation = get_conversation_for_user(conversation_id, current_user.id)
    messages = get_messages(conversation_id)
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        is_shared=conversation.is_shared,
        messages=[Message(**m) for m in messages],
    )
