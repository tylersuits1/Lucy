"""Text extraction from uploaded files."""
from pathlib import Path

import pytesseract
from docx import Document
from PIL import Image
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


class ExtractionError(RuntimeError):
    """Raised when text can't be extracted from a file."""


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".png", ".jpg", ".jpeg"}:
        return _extract_image(path)
    raise ExtractionError(f"Unsupported file type: {suffix or '(none)'}")


def _extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx(path: Path) -> str:
    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()


def _extract_image(path: Path) -> str:
    with Image.open(path) as image:
        return pytesseract.image_to_string(image).strip()
