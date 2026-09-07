"""One-off script: chunk, embed, and store every markdown note in Chroma.

Run from the backend/ directory with its venv active:
    python scripts/ingest_notes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.rag.embed import add_document


def main() -> None:
    settings = get_settings()
    notes_dir = Path(settings.data_dir) / "notes"
    note_paths = sorted(notes_dir.rglob("*.md"))

    if not note_paths:
        print(f"No markdown files found in {notes_dir}")
        return

    total_chunks = 0
    for note_path in note_paths:
        text = note_path.read_text(encoding="utf-8")
        relative_path = str(note_path.relative_to(notes_dir))
        chunk_count = add_document(relative_path, text)
        total_chunks += chunk_count
        print(f"  {relative_path}: {chunk_count} chunks")

    print(f"\nIngested {len(note_paths)} file(s), {total_chunks} chunk(s) total.")


if __name__ == "__main__":
    main()
