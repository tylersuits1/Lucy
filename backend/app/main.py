"""FastAPI app entrypoint for Lucy."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import get_connection
from app.routers import auth, chat, history, upload

app = FastAPI(title="Lucy", description="Self-hosted family AI assistant")

# Wildcard CORS is fine here: real access control is the JWT on every
# request, not the request's origin, and there's no cookie-based session
# to protect against CSRF.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(history.router)


@app.on_event("startup")
async def on_startup() -> None:
    if not get_settings().jwt_secret:
        raise RuntimeError("JWT_SECRET must be set in .env before starting Lucy")
    get_connection()  # creates the SQLite schema if it doesn't exist yet


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
