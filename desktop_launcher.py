"""Native Windows launcher for the AUnitedAI desktop application."""

from __future__ import annotations

import os
import shutil
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


APP_NAME = "AUnitedAI"


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def prepare_user_workspace() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    workspace = base / APP_NAME
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)
    default_config = resource_root() / "worker_config.json"
    user_config = workspace / "worker_config.json"
    if default_config.exists() and not user_config.exists():
        shutil.copy2(default_config, user_config)
    return workspace


def available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until_ready(url: str, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1.0) as response:
                if response.status == 200:
                    return
        except Exception as exc:  # backend is still importing its AI stack
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"AUnitedAI could not start its local engine: {last_error}")


def show_fatal_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    except Exception:
        pass


def main() -> int:
    try:
        import uvicorn
        import webview
    except Exception as exc:
        show_fatal_error(f"The desktop runtime is incomplete.\n\n{exc}")
        return 1

    workspace = prepare_user_workspace()
    frontend = resource_root() / "frontend_dist"
    os.environ["AUNITEDAI_DESKTOP"] = "1"
    os.environ["AUNITEDAI_FRONTEND_DIR"] = str(frontend)
    os.chdir(workspace)

    # Import only after moving to the per-user workspace. Existing relative
    # output/config paths then remain writable after installation in Program Files.
    from orchestrator.api import app

    port = available_port()
    url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    backend = threading.Thread(target=server.run, name="aunitedai-engine", daemon=True)
    backend.start()

    try:
        wait_until_ready(url)
    except Exception as exc:
        server.should_exit = True
        show_fatal_error(str(exc))
        return 1

    logo = resource_root() / "aunitedai-logo.png"
    window = webview.create_window(
        APP_NAME,
        url,
        width=1440,
        height=940,
        min_size=(1024, 700),
        background_color="#080808",
        confirm_close=False,
    )
    window.events.closed += lambda: setattr(server, "should_exit", True)

    try:
        webview.start(
            gui="edgechromium",
            icon=str(logo) if logo.exists() else None,
            debug=os.getenv("AUNITEDAI_DESKTOP_DEBUG") == "1",
        )
    finally:
        server.should_exit = True
        backend.join(timeout=4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
