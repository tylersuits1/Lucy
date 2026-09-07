"""POST /upload — extract, classify, and file away an uploaded document."""
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.ingestion.classify import ClassificationError, classify
from app.ingestion.extract import ExtractionError, extract_text
from app.ingestion.organize import organize
from app.rag.ollama_client import OllamaError

router = APIRouter()


class UploadResponse(BaseModel):
    category: str
    filename: str
    tags: list[str]
    summary: str
    chunks_ingested: int


@router.post("/upload", response_model=UploadResponse)
async def post_upload(file: UploadFile = File(...)) -> UploadResponse:
    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        text = extract_text(tmp_path)
        if not text.strip():
            raise ExtractionError("Could not extract any text from this file.")
        classification = await classify(text)
        result = organize(tmp_path, file.filename or tmp_path.name, classification, text)
    except ExtractionError as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ClassificationError, OllamaError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return UploadResponse(
        category=result["category"],
        filename=result["filename"],
        tags=result["tags"],
        summary=result["summary"],
        chunks_ingested=result["chunks_ingested"],
    )
