"""Google Drive OAuth2 credentials: loaded from a token file, refreshed as needed.

The initial token is produced out-of-band by scripts/drive_authorize.py, which
runs the interactive browser consent flow — that can't happen inside the
FastAPI server itself.
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/drive"]


class DriveAuthError(RuntimeError):
    """Raised when Drive credentials can't be loaded or refreshed."""


def get_credentials() -> Credentials:
    settings = get_settings()
    token_path = Path(settings.google_token_file)

    if not token_path.exists():
        raise DriveAuthError(
            f"No Drive token found at {token_path}. Run scripts/drive_authorize.py once "
            "to complete the OAuth consent flow."
        )

    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials.valid:
        raise DriveAuthError("Drive credentials are invalid and could not be refreshed.")

    return credentials
