"""Pulls new files from the Drive "Lucy Inbox" folder through the upload pipeline."""
import logging
import tempfile
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import get_settings
from app.drive.auth import get_credentials
from app.ingestion.classify import ClassificationError, classify
from app.ingestion.extract import ExtractionError, extract_text
from app.ingestion.organize import organize

PROCESSED_FOLDER_NAME = "Processed"
GOOGLE_NATIVE_MIME_PREFIX = "application/vnd.google-apps"

logger = logging.getLogger("lucy.drive")


def _get_service():
    return build("drive", "v3", credentials=get_credentials())


def _get_or_create_processed_folder(service, inbox_folder_id: str) -> str:
    query = (
        f"'{inbox_folder_id}' in parents and name = '{PROCESSED_FOLDER_NAME}' "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    existing = results.get("files", [])
    if existing:
        return existing[0]["id"]

    folder = (
        service.files()
        .create(
            body={
                "name": PROCESSED_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [inbox_folder_id],
            },
            fields="id",
        )
        .execute()
    )
    return folder["id"]


def _download_file(service, file_id: str, destination: Path) -> None:
    request = service.files().get_media(fileId=file_id)
    with open(destination, "wb") as handle:
        downloader = MediaIoBaseDownload(handle, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


async def sync_inbox() -> list[dict]:
    """Pull new files from the Drive Inbox folder, file them, and move them to Processed."""
    settings = get_settings()
    inbox_folder_id = settings.drive_inbox_folder_id
    if not inbox_folder_id:
        raise ValueError("DRIVE_INBOX_FOLDER_ID is not set.")

    service = _get_service()
    processed_folder_id = _get_or_create_processed_folder(service, inbox_folder_id)

    query = f"'{inbox_folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    drive_files = results.get("files", [])

    outcomes = []
    for drive_file in drive_files:
        name = drive_file["name"]

        if drive_file["mimeType"].startswith(GOOGLE_NATIVE_MIME_PREFIX):
            outcomes.append({"drive_name": name, "status": "skipped", "reason": "Google-native file type not supported yet"})
            continue

        tmp_path = None
        try:
            suffix = Path(name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = Path(tmp.name)
            _download_file(service, drive_file["id"], tmp_path)

            text = extract_text(tmp_path)
            if not text.strip():
                outcomes.append({"drive_name": name, "status": "skipped", "reason": "no extractable text"})
                continue

            classification = await classify(text)
            result = organize(tmp_path, name, classification)
            tmp_path = None  # organize() already moved it
            outcomes.append({"drive_name": name, "status": "processed", **result})

            service.files().update(
                fileId=drive_file["id"],
                addParents=processed_folder_id,
                removeParents=inbox_folder_id,
                fields="id, parents",
            ).execute()
        except (ExtractionError, ClassificationError) as exc:
            outcomes.append({"drive_name": name, "status": "error", "reason": str(exc)})
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    if outcomes:
        logger.info("Drive sync processed %d file(s): %s", len(outcomes), outcomes)
    return outcomes
