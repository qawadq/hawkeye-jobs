"""Entrypoint for the single-user hosted Hawkeye Jobs service."""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import uvicorn

from logs import setup_logging
from runner import AutoSearch, RunManager
from web.server import create_app
from web.services import AppServices


def _required(name: str, minimum: int) -> str:
    value = os.environ.get(name, "")
    if len(value) < minimum:
        raise RuntimeError(f"{name} must be configured and contain at least {minimum} characters")
    return value


def _allowed_hosts() -> set[str]:
    values = {item.strip().lower() for item in os.environ.get("HAWKEYE_ALLOWED_HOSTS", "").split(",") if item.strip()}
    if not values:
        raise RuntimeError("HAWKEYE_ALLOWED_HOSTS must list the hostnames allowed to access this app")
    return values


def main() -> None:
    os.environ.setdefault("HAWKEYE_DATA_DIR", "/data")
    Path(os.environ["HAWKEYE_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    password = _required("HAWKEYE_WEB_PASSWORD", 12)
    session_secret = _required("HAWKEYE_WEB_SESSION_SECRET", 32)
    allowed_hosts = _allowed_hosts()
    cookie_secure = os.environ.get("HAWKEYE_COOKIE_SECURE", "true").strip().lower() not in {"0", "false", "no", "off"}
    port = int(os.environ.get("PORT", "8000"))

    setup_logging()
    manager = RunManager(notifier=lambda jobs: True)
    auto = AutoSearch(manager)
    services = AppServices.default(manager)
    services.hosted = True
    services.open_url = lambda url: None
    services.open_path = lambda path: None
    services.set_start_at_login = lambda enabled: None
    services.background = lambda: {"tray": False, "autostart": False}

    app = create_app(token=None, allowed_hosts=allowed_hosts, services=services,
                     web_password=password, session_secret=session_secret, cookie_secure=cookie_secure)
    try:
        manager.recover_interrupted()
        auto.start()
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", access_log=False)
    finally:
        auto.stop()
        manager.close()
        manager.cancel()
        manager.wait(35)
        manager.close_subscribers()


if __name__ == "__main__":
    main()
