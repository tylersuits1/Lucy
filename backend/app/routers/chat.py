"""POST /chat — send a message to Lucy and get a response back."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.ollama_client import OllamaError, chat as ollama_chat

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await ollama_chat(request.message)
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(reply=reply)
