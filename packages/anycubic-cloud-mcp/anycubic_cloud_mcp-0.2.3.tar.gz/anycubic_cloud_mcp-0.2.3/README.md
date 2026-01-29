# Anycubic Cloud MCP (Kobra 3)

Cloud-backed MCP server and helper scripts for Anycubic printers. This uses the
reverse-engineered Anycubic cloud REST API (and MQTT where supported) from the
`hass-anycubic_cloud` integration.

## Quick Start

Install from GitHub (recommended):

```bash
python3 -m pip install "git+https://github.com/aegis-agent/anycubic-cloud-mcp.git"
```

Install with pipx (isolated CLI):

```bash
pipx install anycubic-cloud-mcp
```

Or from source:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

Run the MCP server (stdio transport by default):

```bash
anycubic-cloud-mcp
```

HTTP transport (optional):

```bash
anycubic-cloud-mcp --http --host 0.0.0.0 --port 8000
```

HTTP endpoint: `http://<host>:<port>/mcp`

Configure auth either via environment variables or the `auth_set` tool.

Environment variables:
- `ANYCUBIC_AUTH_MODE`: `slicer` (recommended) or `web`
- `ANYCUBIC_TOKEN`: token string
- `ANYCUBIC_DEVICE_ID`: only for `android` auth mode

## Token Sources

### Slicer Next (recommended)
This enables MQTT logon and better status updates.

Windows (Slicer Next):
- Config file:
  - `%AppData%\AnycubicSlicerNext\AnycubicSlicerNext.conf`
- The `access_token` value is the token you want.

Extract with the helper script (macOS):

```bash
anycubic-slicer-token
```

Tip: clear `access_token` in the Slicer config after extracting it to avoid
logging out your MCP session when the slicer refreshes.

### Web token (REST-only)
- Go to `https://cloud-universe.anycubic.com/file`
- Sign in
- Open DevTools console
- Run `window.localStorage["XX-Token"]`
- Copy the token string

## MCP Tools

Core tools you asked for:
- `printer_list`
- `printer_status`
- `print_pause`, `print_resume`, `print_cancel`
- `cloud_file_list`, `cloud_file_upload`, `cloud_file_delete`
- `print_upload`, `print_cloud_gcode`, `print_cloud_file`
- `ace_set_slot`, `ace_feed_filament`, `ace_retract_filament`, `ace_set_auto_feed`
- `ace_dry_start`, `ace_dry_stop`

Notes:
- `slot_index_list` is 1-based. Use `1..4` for a single ACE and `1..8` for dual ACE.
- For Kobra 3, Slicer Next tokens are currently the most reliable way to keep MQTT working.

## Config File

You can save tokens to a local config file using `auth_set` with `save: true`.
Default path:
- `~/.config/anycubic-cloud-mcp/config.json`

If you prefer a custom path, set:
- `ANYCUBIC_CONFIG_PATH=/path/to/config.json`

## Installer

The installer supports token extraction on macOS and optional SSH sync.

Token extraction (prints token and syncs config to server):

```bash
anycubic-cloud-mcp-install token --ssh agent@aegis
```

Server setup with systemd (HTTP transport):

```bash
sudo anycubic-cloud-mcp-install server --systemd --http --host 0.0.0.0 --port 8000
```

One-shot installer wrapper (uses REPO_URL):

```bash
REPO_URL="https://github.com/aegis-agent/anycubic-cloud-mcp.git" scripts/install.sh token --ssh agent@aegis
```

Pipx bootstrap:

```bash
scripts/install.sh --pipx token --ssh agent@aegis
```

Pipx upgrade (CLI command):

```bash
anycubic-cloud-mcp-install pipx --ensure-path
```

## Agent Integrations

Use the installer to register this MCP server with common agent harnesses.
Interactive mode shows a selection menu when `--targets` is omitted.

```bash
anycubic-cloud-mcp-install integrate --targets claude-code codex cursor opencode factory
```

Menu-driven selection:

```bash
anycubic-cloud-mcp-install integrate
```

Copy failed raw commands/config to clipboard:

```bash
anycubic-cloud-mcp-install integrate --copy-failures
```

Project-scope installs (Cursor, OpenCode, Factory):

```bash
anycubic-cloud-mcp-install integrate --targets cursor opencode factory --scope project --project-dir /path/to/project
```

Notes:
- Cursor user-scope installs return a deeplink; add `--cursor-open` to open it.
- OpenCode config uses `~/.opencode.json` or `.opencode.json` (project).
- Factory config uses `~/.factory/mcp.json` or `.factory/mcp.json` (project).

## Firmware Note

Firmware version typically does not affect cloud API calls directly, but Anycubic
may change auth or API behaviors server-side. If you are stable on 2.4.4.3, you
can stay there unless you need fixes in 2.4.5.
