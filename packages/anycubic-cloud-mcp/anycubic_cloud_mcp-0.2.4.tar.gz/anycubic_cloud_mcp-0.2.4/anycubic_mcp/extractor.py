from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

TOKEN_RE = re.compile(r'"access_token"\s*:\s*"([^"]+)"')

DEFAULT_SLICER_PATHS = [
    Path.home() / "Library" / "Application Support" / "AnycubicSlicerNext" / "AnycubicSlicerNext.conf",
    Path.home() / "Library" / "Application Support" / "AnycubicSlicer" / "AnycubicSlicer.ini",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Anycubic Slicer access_token.")
    parser.add_argument(
        "--path",
        help="Path to AnycubicSlicer config file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output with the token.",
    )
    return parser.parse_args()


def _find_default_path() -> Path | None:
    env_path = os.environ.get("ANYCUBIC_SLICER_CONFIG")
    if env_path:
        path = Path(env_path).expanduser()
        if path.exists():
            return path

    for candidate in DEFAULT_SLICER_PATHS:
        if candidate.exists():
            return candidate

    app_support = Path.home() / "Library" / "Application Support"
    if app_support.exists():
        for candidate in app_support.rglob("AnycubicSlicerNext.conf"):
            return candidate

    return None


def extract_token(text: str) -> str:
    try:
        data = json.loads(text)
        token = data.get("access_token")
        if isinstance(token, str) and token:
            return token
    except json.JSONDecodeError:
        pass

    match = TOKEN_RE.search(text)
    if not match:
        raise ValueError("access_token not found in file.")
    return match.group(1)


def main() -> None:
    args = parse_args()
    conf_path = Path(args.path).expanduser() if args.path else _find_default_path()
    if conf_path is None or not conf_path.exists():
        raise FileNotFoundError("Config file not found. Use --path to specify it.")

    content = conf_path.read_text(encoding="utf-8", errors="ignore")
    token = extract_token(content)
    if args.json:
        print(json.dumps({"token": token, "path": str(conf_path)}, indent=2))
    else:
        print(token)


if __name__ == "__main__":
    main()
