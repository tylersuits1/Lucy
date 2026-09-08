"""POST /chat — send a message to Lucy and get a response back."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import User, get_current_user
from app.conversations import (
    add_message,
    create_conversation,
    get_conversation_for_user,
    set_title_from_first_message,
)
from app.persona import wrap_reply
from app.rag.gemini_client import GeminiError, chat as gemini_chat
from app.rag.retrieve import retrieve
from app.system.health import get_health_summary

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    is_shared: bool = False


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int


def _build_system_prompt(chunks: list[str]) -> str | None:
    if not chunks:
        return None
    context = "\n\n".join(chunks)
    return (
        "Use the following family information to answer the question. "
        f"If it's not relevant, ignore it:\n\n{context}"
    )


async def _handle_command(command: str) -> str | None:
    """Slash commands are handled directly, never sent to the LLM, and never
    get the persona flourish — they're diagnostics, not Lucy "talking"."""
    if command == "/health":
        return await asyncio.to_thread(get_health_summary)
    return None


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest, current_user: User = Depends(get_current_user)) -> ChatResponse:
    if request.conversation_id is not None:
        conversation = get_conversation_for_user(request.conversation_id, current_user.id)
    else:
        conversation = create_conversation(current_user.id, request.is_shared)

    add_message(conversation.id, "user", request.message)

    command_reply = await _handle_command(request.message.strip().lower())
    if command_reply is not None:
        add_message(conversation.id, "assistant", command_reply)
        return ChatResponse(reply=command_reply, conversation_id=conversation.id)

    chunks = await asyncio.to_thread(retrieve, request.message)
    system_prompt = _build_system_prompt(chunks)

    try:
        reply = await gemini_chat(request.message, system=system_prompt)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    reply = wrap_reply(reply)
    add_message(conversation.id, "assistant", reply)
    if conversation.title == "New chat":
        set_title_from_first_message(conversation.id, request.message)

    return ChatResponse(reply=reply, conversation_id=conversation.id)
