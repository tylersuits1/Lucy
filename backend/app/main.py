"""FastAPI app entrypoint for Lucy."""
from fastapi import FastAPI

from app.routers import chat

app = FastAPI(title="Lucy", description="Self-hosted family AI assistant")

app.include_router(chat.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
