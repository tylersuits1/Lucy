"""Remove a note, its Chroma index entries, and any file it references.

Deleting a note file by hand isn't enough — Chroma keeps its embedded
chunks until told otherwise, so it stays searchable/answerable via chat
even after the file is gone. This removes both, plus the original
uploaded file the note points to (if any).

Run from the backend/ directory with the venv active:
    python scripts/remove_note.py <path-relative-to-data/notes>

Examples:
    python scripts/remove_note.py placeholder.md
    python scripts/remove_note.py household/garage-code.md
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.rag.embed import remove_document


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/remove_note.py <path-relative-to-data/notes>")
        return

    relative_path = sys.argv[1]
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    note_path = data_dir / "notes" / relative_path

    if note_path.exists():
        text = note_path.read_text(encoding="utf-8")
        match = re.search(r"^- File: (.+)$", text, re.MULTILINE)
        if match:
            referenced_file = data_dir / match.group(1).strip()
            if referenced_file.exists():
                referenced_file.unlink()
                print(f"Deleted original file: {referenced_file}")
        note_path.unlink()
        print(f"Deleted note: {note_path}")
    else:
        print(f"No note found at {note_path} — removing from the index anyway, in case it's stale.")

    remove_document(relative_path)
    print(f"Removed '{relative_path}' from the Chroma index.")


if __name__ == "__main__":
    main()
