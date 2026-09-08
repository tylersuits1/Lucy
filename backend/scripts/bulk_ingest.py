"""Bulk-import a folder of documents through the extract/classify/organize pipeline.

For one-time historical imports (e.g. a Google Takeout export) where
uploading one file at a time through the "+" button isn't practical.

Run from the backend/ directory with the venv active:
    python scripts/bulk_ingest.py [path]

Defaults to backend/data/incoming/ if no path is given. Each supported
file is extracted, classified by Gemini, and filed into
data/files/<category>/ — the same pipeline as a normal upload, just
batched. Unsupported file types are skipped (left in place, not deleted)
and reported at the end. Processed files are moved out of the source
folder as they're handled, so re-running after an interruption (including
hitting a rate limit — the free tier is capped at 1,000 requests/day)
only picks up what's left.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.classify import ClassificationError, classify
from app.ingestion.extract import SUPPORTED_EXTENSIONS, ExtractionError, extract_text
from app.ingestion.organize import organize
from app.rag.gemini_client import GeminiError


async def process_file(path: Path) -> None:
    text = extract_text(path)
    if not text.strip():
        raise ExtractionError("no extractable text")

    classification = await classify(text)
    result = organize(path, path.name, classification, text, uploaded_by="bulk import")
    print(f"  filed: {path.name} -> {result['file_path']} ({result['chunks_ingested']} chunks)")


async def main() -> None:
    default_dir = Path(__file__).resolve().parent.parent / "data" / "incoming"
    source_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_dir

    if not source_dir.exists():
        print(f"Nothing to import: {source_dir} doesn't exist.")
        print(f"Create it and drop files in, e.g.: mkdir -p {default_dir}")
        return

    paths = sorted(p for p in source_dir.rglob("*") if p.is_file())
    if not paths:
        print(f"No files found in {source_dir}")
        return

    print(f"Found {len(paths)} file(s) in {source_dir}\n")

    processed = skipped = errors = 0
    for index, path in enumerate(paths):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"  skipped (unsupported type {path.suffix or '(none)'}): {path.name}")
            skipped += 1
            continue

        try:
            await process_file(path)
            processed += 1
        except ExtractionError as exc:
            print(f"  skipped ({exc}), left in place: {path.name}")
            skipped += 1
        except ClassificationError as exc:
            print(f"  ERROR classifying {path.name}: {exc}")
            errors += 1
        except GeminiError as exc:
            remaining = len(paths) - index - 1
            print(f"\nGemini API error: {exc}")
            print(
                f"Stopping here — {remaining} file(s) not yet attempted, left in place. "
                "If this was a rate limit, wait a bit and re-run the script to pick up "
                "where it left off."
            )
            break

    print(f"\nDone: {processed} filed, {skipped} skipped, {errors} errors.")
    if errors:
        print("Files with errors were left in place — safe to re-run the script to retry them.")


if __name__ == "__main__":
    asyncio.run(main())
