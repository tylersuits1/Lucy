"""POST /chat — send a message to Lucy and get a response back."""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.gemini_client import GeminiError, chat as gemini_chat
from app.rag.retrieve import retrieve
from app.system.health import get_health_summary

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _build_system_prompt(chunks: list[str]) -> str | None:
    if not chunks:
        return None
    context = "\n\n".join(chunks)
    return (
        "Use the following family information to answer the question. "
        f"If it's not relevant, ignore it:\n\n{context}"
    )


async def _handle_command(command: str) -> str | None:
    """Slash commands are handled directly, never sent to the LLM."""
    if command == "/health":
        return await asyncio.to_thread(get_health_summary)
    return None


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    command_reply = await _handle_command(request.message.strip().lower())
    if command_reply is not None:
        return ChatResponse(reply=command_reply)

    chunks = await asyncio.to_thread(retrieve, request.message)
    system_prompt = _build_system_prompt(chunks)

    try:
        reply = await gemini_chat(request.message, system=system_prompt)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(reply=reply)
