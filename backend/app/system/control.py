"""Start/stop Ollama on command — the deliberately narrow kill switch.

Requires a passwordless sudo rule scoped to exactly these two commands
(see BACKUP_SETUP.md's sibling, OMARCHY_SETUP.md's Phase 6 section, for
the sudoers drop-in) — the backend itself runs as an unprivileged user.
"""
import subprocess


class ServiceControlError(RuntimeError):
    """Raised when systemctl can't stop/start the Ollama service."""


def _run_systemctl(action: str) -> None:
    try:
        result = subprocess.run(
            ["sudo", "-n", "systemctl", action, "ollama"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise ServiceControlError(f"systemctl {action} ollama timed out") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or f"systemctl {action} ollama failed"
        raise ServiceControlError(detail)


def stop_ollama() -> None:
    _run_systemctl("stop")


def start_ollama() -> None:
    _run_systemctl("start")
