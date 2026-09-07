"""System resource stats for the /health chat command."""
import shutil
import subprocess
import time

import psutil

BTOP_PORT = 7681
GB = 1024**3


def _service_is_active(name: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name], capture_output=True, text=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.stdout.strip() == "active"


def _tailscale_ip() -> str | None:
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    ip = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
    return ip


def _format_uptime(seconds: float) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def get_health_summary() -> str:
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    uptime = _format_uptime(time.time() - psutil.boot_time())
    ollama_status = "running" if _service_is_active("ollama") else "stopped"

    lines = [
        f"CPU: {cpu_percent:.0f}%",
        f"RAM: {memory.used / GB:.1f} / {memory.total / GB:.1f} GB ({memory.percent:.0f}%)",
        f"Disk: {disk.used / GB:.1f} / {disk.total / GB:.1f} GB",
        f"Ollama: {ollama_status}",
        f"Uptime: {uptime}",
    ]

    tailscale_ip = _tailscale_ip()
    if tailscale_ip:
        lines.append(f"\nLive detail: http://{tailscale_ip}:{BTOP_PORT}")
    else:
        lines.append("\n(Live btop view unavailable — Tailscale not detected on this machine.)")

    return "\n".join(lines)
