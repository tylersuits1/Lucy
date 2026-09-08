"""One-off CLI to add a Lucy login. Run from backend/ with the venv active:

    python scripts/create_user.py
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth import create_user  # noqa: E402


def main() -> None:
    username = input("Username: ").strip()
    display_name = input("Display name: ").strip() or username
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords didn't match.")
        raise SystemExit(1)
    if not username or not password:
        print("Username and password are required.")
        raise SystemExit(1)

    user_id = create_user(username, password, display_name)
    print(f"Created user '{username}' (id={user_id}).")


if __name__ == "__main__":
    main()
