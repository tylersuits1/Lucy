"""LLM-based classification of extracted document text."""
import json

from app.rag.gemini_client import chat

CLASSIFY_SYSTEM_PROMPT = (
    "You are a document filing assistant. Given the text of a document, respond with a JSON "
    'object with exactly these keys: "category" (a short lowercase folder name like '
    '"receipts", "medical", "school", "insurance", "manuals", or "other"), "tags" (a list of '
    '1-5 short lowercase keyword strings), "summary" (one or two sentences), and "filename" '
    "(a short descriptive lowercase name with hyphens instead of spaces, no extension). "
    "Respond with ONLY the JSON object, no other text."
)

# Keeps token usage (and cost) bounded per document.
MAX_INPUT_CHARS = 6000


class ClassificationError(RuntimeError):
    """Raised when the model's response can't be parsed as a valid classification."""


async def classify(text: str) -> dict:
    reply = await chat(text[:MAX_INPUT_CHARS], system=CLASSIFY_SYSTEM_PROMPT, format="json")
    try:
        result = json.loads(reply)
    except json.JSONDecodeError as exc:
        raise ClassificationError(f"Model did not return valid JSON: {reply!r}") from exc

    for key in ("category", "tags", "summary", "filename"):
        if key not in result:
            raise ClassificationError(f"Model response missing '{key}': {result!r}")
    return result
