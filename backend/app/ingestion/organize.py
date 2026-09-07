"""Move a classified upload into place and ingest a companion note for it."""
import re
import shutil
from pathlib import Path

from app.config import get_settings
from app.rag.embed import add_document


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "untitled"


def _unique_stem(directory: Path, stem: str, suffix: str) -> str:
    """Disambiguate stem if directory/stem+suffix already exists, so bulk imports of
    similarly-named documents (e.g. several years of "insurance-policy") don't
    silently overwrite each other."""
    if not (directory / f"{stem}{suffix}").exists():
        return stem
    counter = 2
    while (directory / f"{stem}-{counter}{suffix}").exists():
        counter += 1
    return f"{stem}-{counter}"


def organize(temp_path: Path, original_filename: str, classification: dict, extracted_text: str) -> dict:
    settings = get_settings()
    data_dir = Path(settings.data_dir)

    category = _slugify(str(classification["category"]))
    base_filename = _slugify(str(classification["filename"]))
    extension = Path(original_filename).suffix
    tags = classification.get("tags", [])
    summary = classification.get("summary", "")

    files_dir = data_dir / "files" / category
    files_dir.mkdir(parents=True, exist_ok=True)
    unique_stem = _unique_stem(files_dir, base_filename, extension)
    final_path = files_dir / f"{unique_stem}{extension}"
    shutil.move(str(temp_path), final_path)

    note_relative_path = f"{category}/{unique_stem}.md"
    note_path = data_dir / "notes" / note_relative_path
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        "\n".join(
            [
                f"# {classification['filename']}",
                "",
                f"- Original filename: {original_filename}",
                f"- Category: {category}",
                f"- Tags: {', '.join(tags)}",
                f"- File: {final_path.relative_to(data_dir)}",
                "",
                summary,
                "",
                extracted_text,
            ]
        ),
        encoding="utf-8",
    )

    chunk_count = add_document(note_relative_path, note_path.read_text(encoding="utf-8"))

    return {
        "category": category,
        "filename": final_path.name,
        "file_path": str(final_path.relative_to(data_dir)),
        "note_path": note_relative_path,
        "tags": tags,
        "summary": summary,
        "chunks_ingested": chunk_count,
    }
