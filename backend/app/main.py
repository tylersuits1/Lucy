"""FastAPI app entrypoint for Lucy."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat

app = FastAPI(title="Lucy", description="Self-hosted family AI assistant")

# Wildcard CORS is fine here: the backend is never exposed beyond the
# Tailscale network, so there's no public origin to defend against.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
