from __future__ import annotations

import argparse
import base64
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote
import re

from .config import DEFAULT_CONFIG_PATH, save_config
from .extractor import extract_token

DEFAULT_SERVER_NAME = "anycubic-cloud-mcp"
DEFAULT_COMMAND = "anycubic-cloud-mcp"


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


def _parse_env_vars(env_list: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    for item in env_list:
        if "=" not in item:
            raise ValueError(f"Invalid env var '{item}'. Expected KEY=VALUE.")
        key, value = item.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _parse_headers(header_list: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in header_list:
        if ":" in item:
            key, value = item.split(":", 1)
        elif "=" in item:
            key, value = item.split("=", 1)
        else:
            raise ValueError(f"Invalid header '{item}'. Expected KEY: VALUE.")
        headers[key.strip()] = value.strip()
    return headers


def _env_dict_to_list(env: dict[str, str]) -> list[str]:
    return [f"{key}={value}" for key, value in env.items()]


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    if not sys.stdin.isatty():
        return default
    suffix = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False


def _prompt_choice(prompt: str, choices: list[str], default: str) -> str:
    if not sys.stdin.isatty():
        return default
    choice_map = {choice.lower(): choice for choice in choices}
    while True:
        response = input(f"{prompt} ({'/'.join(choices)}, default {default}): ").strip().lower()
        if not response:
            return default
        if response in choice_map:
            return choice_map[response]


def _prompt_path(prompt: str, default: Path) -> Path:
    if not sys.stdin.isatty():
        return default
    response = input(f"{prompt} [default: {default}]: ").strip()
    return Path(response).expanduser() if response else default


def _select_targets_menu(default: list[str]) -> list[str]:
    if not sys.stdin.isatty():
        return default

    targets = ["claude-code", "codex", "cursor", "opencode", "factory"]
    while True:
        print("Select platforms to install:")
        for idx, target in enumerate(targets, start=1):
            print(f"  {idx}) {target}")
        print("  a) all")
        print("  n) none")
        response = input("Enter selection (e.g., 1,3,a): ").strip().lower()
        if not response:
            return default
        if response in ("a", "all"):
            return list(targets)
        if response in ("n", "none"):
            return []
        tokens = [t for t in re.split(r"[,\s]+", response) if t]
        selected: list[str] = []
        invalid = False
        for token in tokens:
            if token.isdigit():
                idx = int(token)
                if 1 <= idx <= len(targets):
                    selected.append(targets[idx - 1])
                else:
                    invalid = True
                    break
            else:
                invalid = True
                break
        if invalid:
            print("Invalid selection. Try again.")
            continue
        return list(dict.fromkeys(selected))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _merge_server_config(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in new.items():
        if key in ("env", "headers") and isinstance(value, dict):
            base = existing.get(key)
            if isinstance(base, dict):
                merged[key] = {**base, **value}
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged


def _update_mcp_config(path: Path, server_name: str, server_config: dict[str, Any]) -> None:
    data = _load_json(path)
    mcp_servers = data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}

    existing = mcp_servers.get(server_name)
    if isinstance(existing, dict):
        mcp_servers[server_name] = _merge_server_config(existing, server_config)
    else:
        mcp_servers[server_name] = server_config

    data["mcpServers"] = mcp_servers
    _write_json(path, data)


def _find_command(name: str, extra_paths: list[Path] | None = None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for path in extra_paths or []:
        if path.exists():
            return str(path)
    return None


def _find_claude_command() -> str | None:
    candidates = [
        Path.home() / ".claude" / "local" / "claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".npm-global" / "bin" / "claude",
        Path("/opt/homebrew/bin/claude"),
    ]
    return _find_command("claude", candidates)


def _find_codex_command() -> str | None:
    candidates = [
        Path.home() / ".local" / "bin" / "codex",
        Path("/usr/local/bin/codex"),
        Path("/opt/homebrew/bin/codex"),
    ]
    return _find_command("codex", candidates)


def _find_droid_command() -> str | None:
    candidates = [
        Path.home() / ".factory" / "bin" / "droid",
        Path.home() / ".local" / "bin" / "droid",
        Path("/usr/local/bin/droid"),
        Path("/opt/homebrew/bin/droid"),
    ]
    return _find_command("droid", candidates)


def _run_command(cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, result.stdout.strip()
    message = result.stderr.strip() or result.stdout.strip()
    return False, message or f"Command failed ({result.returncode})"


def _format_command(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def _cursor_deeplink(server_name: str, server_config: dict[str, Any]) -> str:
    config_json = json.dumps(server_config, separators=(",", ":"), ensure_ascii=True)
    config_b64 = base64.urlsafe_b64encode(config_json.encode("utf-8")).decode("utf-8")
    encoded_name = quote(server_name, safe="")
    return f"cursor://anysphere.cursor-deeplink/mcp/install?name={encoded_name}&config={config_b64}"


def _open_url(url: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=True, capture_output=True)
        elif sys.platform == "win32":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", url], check=True, capture_output=True)
        return True
    except (OSError, subprocess.CalledProcessError, FileNotFoundError):
        return False


def _opencode_user_config_path() -> Path:
    candidates = [
        Path.home() / ".opencode.json",
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode" / ".opencode.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


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

    pipx_parser = subparsers.add_parser("pipx", help="Install or upgrade with pipx.")
    pipx_parser.add_argument("--source", choices=["pypi", "git"], default="pypi")
    pipx_parser.add_argument("--package", default="anycubic-cloud-mcp")
    pipx_parser.add_argument("--repo-url", default="https://github.com/aegis-agent/anycubic-cloud-mcp.git")
    pipx_parser.add_argument("--ensure-path", action="store_true", help="Run pipx ensurepath.")

    integrate_parser = subparsers.add_parser("integrate", help="Install MCP config for agent clients.")
    integrate_parser.add_argument("--name", default=DEFAULT_SERVER_NAME, help="Server name to register.")
    integrate_parser.add_argument(
        "--command",
        dest="exec_command",
        default=DEFAULT_COMMAND,
        help="Command to launch the server.",
    )
    integrate_parser.add_argument("--arg", action="append", dest="args", default=[], help="Command argument.")
    integrate_parser.add_argument("--env", action="append", default=[], help="Environment variable KEY=VALUE.")
    integrate_parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to local config file.",
    )
    integrate_parser.add_argument("--log-level", default="INFO", help="Log level.")
    integrate_parser.add_argument("--http-url", help="Use HTTP MCP server instead of stdio.")
    integrate_parser.add_argument(
        "--http-header",
        action="append",
        default=[],
        help="HTTP header KEY: VALUE (repeatable).",
    )
    integrate_parser.add_argument(
        "--targets",
        nargs="*",
        choices=["claude-code", "codex", "cursor", "opencode", "factory", "all"],
        help="Targets to configure.",
    )
    integrate_parser.add_argument(
        "--scope",
        choices=["user", "project"],
        default="user",
        help="Install scope for targets that support project config.",
    )
    integrate_parser.add_argument(
        "--project-dir",
        help="Project directory for project-scope installs.",
    )
    integrate_parser.add_argument(
        "--cursor-open",
        action="store_true",
        help="Open Cursor deeplink when using user scope.",
    )
    integrate_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and use defaults.",
    )

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


def _pipx_is_installed(package: str) -> bool:
    result = subprocess.run(
        ["pipx", "list", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    venvs = payload.get("venvs", {})
    return package in venvs


def run_pipx_command(args: argparse.Namespace) -> None:
    if not shutil.which("pipx"):
        raise FileNotFoundError("pipx not found in PATH.")

    install_target = args.package
    if args.source == "git":
        install_target = f"git+{args.repo_url}"

    if _pipx_is_installed(args.package):
        subprocess.run(["pipx", "upgrade", args.package], check=True)
    else:
        subprocess.run(["pipx", "install", install_target], check=True)

    if args.ensure_path:
        subprocess.run(["pipx", "ensurepath"], check=False)


def _claude_commands(
    claude_cmd: str,
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
    headers: dict[str, str],
) -> list[list[str]]:
    cmd = [claude_cmd, "mcp", "add"]
    if http_url:
        cmd.extend(["--transport", "http", server_name, http_url])
        for key, value in headers.items():
            cmd.extend(["--header", f"{key}: {value}"])
        return [cmd]

    for key, value in env.items():
        cmd.extend(["-e", f"{key}={value}"])
    with_sep = cmd + [server_name, "--", command] + list(args)
    without_sep = cmd + [server_name, command] + list(args)
    if with_sep == without_sep:
        return [with_sep]
    return [with_sep, without_sep]


def _install_claude_code(
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
    headers: dict[str, str],
) -> tuple[bool, str, list[list[str]]]:
    claude_cmd = _find_claude_command()
    if not claude_cmd:
        return False, "Claude Code CLI not found.", []

    commands = _claude_commands(
        claude_cmd=claude_cmd,
        server_name=server_name,
        command=command,
        args=args,
        env=env,
        http_url=http_url,
        headers=headers,
    )
    last_message = ""
    for cmd in commands:
        ok, message = _run_command(cmd)
        if ok:
            return True, message, commands
        last_message = message
    return False, last_message, commands


def _codex_command(
    codex_cmd: str,
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
) -> list[str]:
    cmd = [codex_cmd, "mcp", "add", server_name]
    if http_url:
        cmd.extend(["--url", http_url])
    else:
        for key, value in env.items():
            cmd.extend(["--env", f"{key}={value}"])
        cmd.append("--")
        cmd.append(command)
        cmd.extend(args)
    return cmd


def _install_codex(
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
) -> tuple[bool, str, list[str]]:
    codex_cmd = _find_codex_command()
    if not codex_cmd:
        return False, "Codex CLI not found.", []

    cmd = _codex_command(
        codex_cmd=codex_cmd,
        server_name=server_name,
        command=command,
        args=args,
        env=env,
        http_url=http_url,
    )
    ok, message = _run_command(cmd)
    return ok, message, cmd


def _factory_command(
    droid_cmd: str,
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
    headers: dict[str, str],
) -> list[str]:
    cmd = [droid_cmd, "mcp", "add", server_name]
    if http_url:
        cmd.extend([http_url, "--type", "http"])
        for key, value in headers.items():
            cmd.extend(["--header", f"{key}: {value}"])
    else:
        command_str = " ".join(shlex.quote(part) for part in [command] + args)
        cmd.append(command_str)
        for key, value in env.items():
            cmd.extend(["--env", f"{key}={value}"])
    return cmd


def _install_factory_cli(
    server_name: str,
    command: str,
    args: list[str],
    env: dict[str, str],
    http_url: str | None,
    headers: dict[str, str],
) -> tuple[bool, str, list[str]]:
    droid_cmd = _find_droid_command()
    if not droid_cmd:
        return False, "Factory droid CLI not found.", []

    cmd = _factory_command(
        droid_cmd=droid_cmd,
        server_name=server_name,
        command=command,
        args=args,
        env=env,
        http_url=http_url,
        headers=headers,
    )
    ok, message = _run_command(cmd)
    return ok, message, cmd


def _update_cursor_workspace(
    server_name: str,
    project_dir: Path,
    server_config: dict[str, Any],
) -> None:
    config_path = project_dir / ".cursor" / "mcp.json"
    _update_mcp_config(config_path, server_name, server_config)


def _update_opencode_config(
    server_name: str,
    config_path: Path,
    server_config: dict[str, Any],
) -> None:
    _update_mcp_config(config_path, server_name, server_config)


def _update_factory_config(
    server_name: str,
    config_path: Path,
    server_config: dict[str, Any],
) -> None:
    _update_mcp_config(config_path, server_name, server_config)


def run_integrate_command(args: argparse.Namespace) -> None:
    try:
        env = _parse_env_vars(args.env)
        headers = _parse_headers(args.http_header)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    config_path = Path(args.config_path).expanduser()
    env.setdefault("ANYCUBIC_CONFIG_PATH", str(config_path))
    env.setdefault("ANYCUBIC_LOG_LEVEL", args.log_level)

    command = args.exec_command
    command_args = list(args.args or [])
    http_url = args.http_url

    if args.targets:
        targets = args.targets
        if "all" in targets:
            targets = ["claude-code", "codex", "cursor", "opencode", "factory"]
    elif args.non_interactive:
        targets = ["claude-code", "codex", "cursor", "opencode", "factory"]
    else:
        targets = _select_targets_menu(default=[])

    if not targets:
        print("No targets selected.")
        return

    results: list[dict[str, Any]] = []
    for target in targets:
        scope = "user"
        project_dir = Path(args.project_dir).expanduser() if args.project_dir else Path.cwd()
        if target in ("cursor", "opencode", "factory"):
            if args.non_interactive:
                scope = args.scope
            else:
                scope = _prompt_choice(f"{target} scope", ["user", "project"], args.scope)
            if scope == "project":
                project_dir = _prompt_path(f"{target} project directory", project_dir)
                if not project_dir.exists():
                    results.append(
                        {
                            "target": target,
                            "ok": False,
                            "message": f"Project directory not found: {project_dir}",
                            "raw": None,
                        }
                    )
                    continue

        if target == "claude-code":
            ok, message, commands = _install_claude_code(
                server_name=args.name,
                command=command,
                args=command_args,
                env=env,
                http_url=http_url,
                headers=headers,
            )
            raw = "\n".join(_format_command(cmd) for cmd in commands) if commands else None
            results.append({"target": target, "ok": ok, "message": message, "raw": raw})
            continue

        if target == "codex":
            ok, message, cmd = _install_codex(
                server_name=args.name,
                command=command,
                args=command_args,
                env=env,
                http_url=http_url,
            )
            raw = _format_command(cmd) if cmd else None
            results.append({"target": target, "ok": ok, "message": message, "raw": raw})
            continue

        if target == "cursor":
            if scope == "project":
                if http_url:
                    server_config = {"transport": "http", "url": http_url, "headers": headers}
                else:
                    server_config = {"transport": "stdio", "command": command, "args": command_args, "env": env}
                raw = json.dumps({"mcpServers": {args.name: server_config}}, indent=2)
                try:
                    _update_cursor_workspace(args.name, project_dir, server_config)
                    results.append({"target": target, "ok": True, "message": f"Installed in {project_dir}", "raw": raw})
                except Exception as exc:
                    results.append({"target": target, "ok": False, "message": str(exc), "raw": raw})
            else:
                if http_url:
                    server_config = {"transport": "http", "url": http_url, "headers": headers}
                else:
                    server_config = {"transport": "stdio", "command": command, "args": command_args, "env": env}
                deeplink = _cursor_deeplink(args.name, server_config)
                opened = False
                if args.cursor_open:
                    opened = _open_url(deeplink)
                message = deeplink if not opened else "Cursor deeplink opened."
                results.append({"target": target, "ok": True, "message": message, "raw": deeplink})
            continue

        if target == "opencode":
            if scope == "project":
                config_file = project_dir / ".opencode.json"
            else:
                config_file = _opencode_user_config_path()
            if http_url:
                server_config = {
                    "type": "sse",
                    "url": http_url,
                    "headers": headers,
                }
            else:
                server_config = {
                    "type": "stdio",
                    "command": command,
                    "args": command_args,
                    "env": _env_dict_to_list(env),
                }
            raw = json.dumps({"mcpServers": {args.name: server_config}}, indent=2)
            try:
                _update_opencode_config(args.name, config_file, server_config)
                results.append({"target": target, "ok": True, "message": f"Updated {config_file}", "raw": raw})
            except Exception as exc:
                results.append({"target": target, "ok": False, "message": str(exc), "raw": raw})
            continue

        if target == "factory":
            if scope == "project":
                config_file = project_dir / ".factory" / "mcp.json"
                if http_url:
                    server_config = {
                        "type": "http",
                        "url": http_url,
                        "headers": headers,
                        "disabled": False,
                    }
                else:
                    server_config = {
                        "type": "stdio",
                        "command": command,
                        "args": command_args,
                        "env": env,
                        "disabled": False,
                    }
                raw = json.dumps({"mcpServers": {args.name: server_config}}, indent=2)
                try:
                    _update_factory_config(args.name, config_file, server_config)
                    results.append({"target": target, "ok": True, "message": f"Updated {config_file}", "raw": raw})
                except Exception as exc:
                    results.append({"target": target, "ok": False, "message": str(exc), "raw": raw})
            else:
                ok, message, cmd = _install_factory_cli(
                    server_name=args.name,
                    command=command,
                    args=command_args,
                    env=env,
                    http_url=http_url,
                    headers=headers,
                )
                raw_command = _format_command(cmd) if cmd else None
                if not ok:
                    config_file = Path.home() / ".factory" / "mcp.json"
                    if http_url:
                        server_config = {
                            "type": "http",
                            "url": http_url,
                            "headers": headers,
                            "disabled": False,
                        }
                    else:
                        server_config = {
                            "type": "stdio",
                            "command": command,
                            "args": command_args,
                            "env": env,
                            "disabled": False,
                        }
                    raw_config = json.dumps({"mcpServers": {args.name: server_config}}, indent=2)
                    try:
                        _update_factory_config(args.name, config_file, server_config)
                        results.append({"target": target, "ok": True, "message": f"Updated {config_file}", "raw": raw_config})
                    except Exception as exc:
                        results.append({"target": target, "ok": False, "message": str(exc), "raw": raw_config or raw_command})
                else:
                    results.append({"target": target, "ok": True, "message": message, "raw": raw_command})

    for result in results:
        target = result["target"]
        ok = result["ok"]
        message = result.get("message")
        raw = result.get("raw")
        status = "ok" if ok else "failed"
        detail = f" ({message})" if message else ""
        print(f"{target}: {status}{detail}")
        if not ok and raw:
            print(f"{target} raw:\n{raw}")


def main() -> None:
    args = parse_args()
    if args.command == "token":
        run_token_command(args)
    elif args.command == "server":
        run_server_command(args)
    elif args.command == "pipx":
        run_pipx_command(args)
    elif args.command == "integrate":
        run_integrate_command(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
