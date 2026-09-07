"""FastAPI app entrypoint for Lucy."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.drive.sync import sync_inbox
from app.routers import chat, drive, upload

logger = logging.getLogger("lucy.drive")


async def _drive_poll_loop() -> None:
    settings = get_settings()
    if not settings.drive_inbox_folder_id:
        return

    while True:
        try:
            await sync_inbox()
        except Exception:
            logger.exception("Drive sync failed; will retry next interval")
        await asyncio.sleep(settings.drive_poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_drive_poll_loop())
    yield
    task.cancel()


app = FastAPI(title="Lucy", description="Self-hosted family AI assistant", lifespan=lifespan)

# Wildcard CORS is fine here: the backend is never exposed beyond the
# Tailscale network, so there's no public origin to defend against.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(drive.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
