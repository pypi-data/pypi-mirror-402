from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "anycubic-cloud-mcp"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"


@dataclass
class MCPConfig:
    auth_mode: str | None
    auth_token: str | None
    device_id: str | None
    config_path: Path
    log_level: str


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_config() -> MCPConfig:
    config_path = Path(os.environ.get("ANYCUBIC_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    data = _read_config_file(config_path)

    auth_mode = os.environ.get("ANYCUBIC_AUTH_MODE", data.get("auth_mode"))
    auth_token = os.environ.get("ANYCUBIC_TOKEN", data.get("auth_token"))
    device_id = os.environ.get("ANYCUBIC_DEVICE_ID", data.get("device_id"))
    log_level = os.environ.get("ANYCUBIC_LOG_LEVEL", data.get("log_level", "INFO"))

    return MCPConfig(
        auth_mode=auth_mode,
        auth_token=auth_token,
        device_id=device_id,
        config_path=config_path,
        log_level=log_level,
    )


def save_config(
    config_path: Path,
    auth_mode: str | None,
    auth_token: str | None,
    device_id: str | None,
    log_level: str | None = None,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "auth_mode": auth_mode,
        "auth_token": auth_token,
        "device_id": device_id,
    }
    if log_level:
        payload["log_level"] = log_level
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
