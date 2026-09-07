"""POST /chat — send a message to Lucy and get a response back."""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.ollama_client import OllamaError, chat as ollama_chat
from app.rag.retrieve import retrieve
from app.system.control import ServiceControlError, start_ollama, stop_ollama
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

    if command == "/kill":
        try:
            await asyncio.to_thread(stop_ollama)
        except ServiceControlError as exc:
            return f"Couldn't stop Ollama: {exc}"
        return (
            "Ollama stopped. Chat and uploads won't work until you send /start — "
            "everything else (this web app, file storage) is unaffected."
        )

    if command == "/start":
        try:
            await asyncio.to_thread(start_ollama)
        except ServiceControlError as exc:
            return f"Couldn't start Ollama: {exc}"
        return "Ollama is starting back up — give it a few seconds before asking a question."

    return None


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    command_reply = await _handle_command(request.message.strip().lower())
    if command_reply is not None:
        return ChatResponse(reply=command_reply)

    chunks = await asyncio.to_thread(retrieve, request.message)
    system_prompt = _build_system_prompt(chunks)

    try:
        reply = await ollama_chat(request.message, system=system_prompt)
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(reply=reply)
