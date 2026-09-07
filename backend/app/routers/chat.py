"""POST /chat — send a message to Lucy and get a response back."""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.ollama_client import OllamaError, chat as ollama_chat
from app.rag.retrieve import retrieve

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


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    chunks = await asyncio.to_thread(retrieve, request.message)
    system_prompt = _build_system_prompt(chunks)

    try:
        reply = await ollama_chat(request.message, system=system_prompt)
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(reply=reply)
