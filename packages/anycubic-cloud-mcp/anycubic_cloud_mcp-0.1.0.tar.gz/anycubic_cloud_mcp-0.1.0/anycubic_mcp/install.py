from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG_PATH, save_config
from .extractor import extract_token


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write_remote_config(
    ssh_host: str,
    config_path: str,
    payload: dict[str, Any],
) -> None:
    remote_dir = str(Path(config_path).parent)
    mkdir_cmd = f"mkdir -p {remote_dir}"
    subprocess.run(["ssh", ssh_host, mkdir_cmd], check=True)
    subprocess.run(
        ["ssh", ssh_host, f"cat > {config_path}"],
        input=json.dumps(payload, indent=2),
        text=True,
        check=True,
    )


def _install_systemd_service(
    service_path: Path,
    user: str,
    exec_start: str,
    config_path: Path,
    log_level: str,
) -> None:
    content = "\n".join(
        [
            "[Unit]",
            "Description=Anycubic Cloud MCP Server",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            f"User={user}",
            f"Group={user}",
            f"Environment=ANYCUBIC_CONFIG_PATH={config_path}",
            f"Environment=ANYCUBIC_LOG_LEVEL={log_level}",
            f"ExecStart={exec_start}",
            "Restart=on-failure",
            "RestartSec=5",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "",
        ]
    )
    service_path.write_text(content, encoding="utf-8")


def _default_slicer_path() -> Path | None:
    mac_path = Path.home() / "Library" / "Application Support" / "AnycubicSlicerNext" / "AnycubicSlicerNext.conf"
    if mac_path.exists():
        return mac_path
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anycubic Cloud MCP installer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    default_remote_config = "~/.config/anycubic-cloud-mcp/config.json"

    token_parser = subparsers.add_parser("token", help="Extract token from Slicer config.")
    token_parser.add_argument("--path", help="Path to Slicer config file.")
    token_parser.add_argument("--json", action="store_true", help="Print JSON output.")
    token_parser.add_argument("--ssh", help="SSH target to sync config, e.g. agent@aegis.")
    token_parser.add_argument(
        "--remote-config-path",
        help="Remote config path on server.",
        default=default_remote_config,
    )
    token_parser.add_argument(
        "--auth-mode",
        default="slicer",
        help="Auth mode for the token (default: slicer).",
    )
    token_parser.add_argument("--device-id", help="Device ID for android auth.")

    server_parser = subparsers.add_parser("server", help="Prepare server config/systemd.")
    server_parser.add_argument("--auth-mode", help="Auth mode to save.")
    server_parser.add_argument("--token", help="Token to save.")
    server_parser.add_argument("--device-id", help="Device ID for android auth.")
    server_parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to local config file.",
    )
    server_parser.add_argument("--log-level", default="INFO", help="Log level.")
    server_parser.add_argument("--systemd", action="store_true", help="Install systemd service.")
    server_parser.add_argument("--service-path", default="/etc/systemd/system/anycubic-cloud-mcp.service")
    server_parser.add_argument("--user", default=os.environ.get("USER", "agent"))
    server_parser.add_argument("--http", action="store_true", help="Enable HTTP transport.")
    server_parser.add_argument("--host", default="127.0.0.1")
    server_parser.add_argument("--port", type=int, default=8000)

    return parser.parse_args()


def run_token_command(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser() if args.path else _default_slicer_path()
    if path is None or not path.exists():
        raise FileNotFoundError("Slicer config not found. Use --path to specify it.")

    token = extract_token(_read_text(path))
    payload = {
        "auth_mode": args.auth_mode,
        "auth_token": token,
        "device_id": args.device_id,
    }

    if args.ssh:
        _write_remote_config(args.ssh, args.remote_config_path, payload)

    if args.json:
        print(json.dumps({"token": token, "path": str(path)}, indent=2))
    else:
        print(token)


def run_server_command(args: argparse.Namespace) -> None:
    config_path = Path(args.config_path).expanduser()
    if args.token and args.auth_mode:
        save_config(
            config_path=config_path,
            auth_mode=args.auth_mode,
            auth_token=args.token,
            device_id=args.device_id,
            log_level=args.log_level,
        )

    if args.systemd:
        if args.http:
            exec_start = (
                f"{sys.executable} -m anycubic_mcp.mcp_server --http "
                f"--host {args.host} --port {args.port}"
            )
        else:
            exec_start = f"{sys.executable} -m anycubic_mcp.mcp_server"

        service_path = Path(args.service_path)
        _install_systemd_service(
            service_path=service_path,
            user=args.user,
            exec_start=exec_start,
            config_path=config_path,
            log_level=args.log_level,
        )

        if shutil.which("systemctl"):
            subprocess.run(["systemctl", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "enable", "--now", service_path.name], check=False)


def main() -> None:
    args = parse_args()
    if args.command == "token":
        run_token_command(args)
    elif args.command == "server":
        run_server_command(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
