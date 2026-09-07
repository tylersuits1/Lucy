"""Endpoints to trigger and check Google Drive inbox sync."""
from fastapi import APIRouter, HTTPException

from app.drive.auth import DriveAuthError
from app.drive.sync import sync_inbox
from app.rag.ollama_client import OllamaError

router = APIRouter(prefix="/drive")


@router.post("/sync")
async def post_drive_sync() -> dict:
    try:
        results = await sync_inbox()
    except DriveAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"processed": len(results), "results": results}
