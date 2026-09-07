"""One-off script: complete the Google Drive OAuth consent flow.

Run this once, on a machine with a browser, with the venv active:
    python scripts/drive_authorize.py

It opens a browser for you to approve access, then saves the resulting
token to GOOGLE_TOKEN_FILE (see .env). If you run this somewhere other
than the server (e.g. your dev Mac, since it needs a browser), copy the
resulting token file to the server afterward.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import get_settings
from app.drive.auth import SCOPES


def main() -> None:
    settings = get_settings()
    client_secret_path = Path(settings.google_client_secret_file)
    token_path = Path(settings.google_token_file)

    if not client_secret_path.exists():
        print(f"Missing {client_secret_path} — download it from Google Cloud Console first.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    credentials = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Saved credentials to {token_path}")


if __name__ == "__main__":
    main()
