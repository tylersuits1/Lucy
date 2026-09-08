"""Thin wrapper around the Gemini API — replaces the local Ollama client."""
from google import genai
from google.genai import errors
from google.genai.types import GenerateContentConfig

from app.config import get_settings


class GeminiError(RuntimeError):
    """Raised when the Gemini API can't be reached or returns an error."""


def _get_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiError("GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey")
    return genai.Client(api_key=settings.gemini_api_key)


async def chat(message: str, system: str | None = None, format: str | None = None) -> str:
    """Send a single-turn message to Gemini and return its reply."""
    settings = get_settings()
    client = _get_client()

    config = GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json" if format == "json" else None,
    )

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=message,
            config=config,
        )
    except errors.APIError as exc:
        raise GeminiError(f"Gemini API request failed: {exc}") from exc

    if not response.text:
        raise GeminiError("Gemini returned an empty response.")
    return response.text
