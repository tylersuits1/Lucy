"""Thin wrapper around a local Ollama instance's chat API."""
import httpx

from app.config import get_settings


class OllamaError(RuntimeError):
    """Raised when the Ollama server can't be reached or returns an error."""


async def chat(message: str, system: str | None = None, format: str | None = None) -> str:
    """Send a single-turn chat message to the configured Ollama model and return its reply."""
    settings = get_settings()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }
    if format:
        payload["format"] = format

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{settings.ollama_host}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Failed to reach Ollama at {settings.ollama_host}: {exc}") from exc

    data = response.json()
    return data["message"]["content"]
