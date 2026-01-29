from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import anyio
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .client import AnycubicClient, parse_auth_mode
from .config import load_config, save_config

SERVER_NAME = "anycubic-cloud-mcp"
SERVER_VERSION = "0.2.6"


def _build_logger(log_level: str) -> logging.Logger:
    logger = logging.getLogger(SERVER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _slot_list_to_zero_based(slot_list: list[int] | None) -> list[int] | None:
    if not slot_list:
        return None
    return [int(x) - 1 for x in slot_list]


def _tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="auth_set",
            description=(
                "Set authentication mode and token. Use mode 'slicer' for Slicer Next access_token "
                "(enables MQTT), or 'web' for XX-Token (REST only)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "auth_mode": {"type": "string", "enum": ["slicer", "web", "android"]},
                    "token": {"type": "string"},
                    "device_id": {"type": "string"},
                    "save": {"type": "boolean"},
                },
                "required": ["auth_mode", "token"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "auth_mode": {"type": "string"},
                    "mqtt_supported": {"type": "boolean"},
                    "saved": {"type": "boolean"},
                    "config_path": {"type": "string"},
                },
                "required": ["ok", "auth_mode", "mqtt_supported", "saved", "config_path"],
            },
        ),
        types.Tool(
            name="auth_status",
            description="Return current auth configuration status.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            outputSchema={
                "type": "object",
                "properties": {
                    "auth_mode": {"type": "string"},
                    "token_present": {"type": "boolean"},
                    "device_id_present": {"type": "boolean"},
                    "mqtt_supported": {"type": "boolean"},
                },
                "required": ["auth_mode", "token_present", "device_id_present", "mqtt_supported"],
            },
        ),
        types.Tool(
            name="printer_list",
            description="List printers linked to the account.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            outputSchema={
                "type": "object",
                "properties": {
                    "printers": {
                        "type": "array",
                        "items": {"type": "object"},
                    }
                },
                "required": ["printers"],
            },
        ),
        types.Tool(
            name="printer_status",
            description="Fetch detailed status for a printer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "include_project": {"type": "boolean"},
                },
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"printer": {"type": "object"}},
                "required": ["printer"],
            },
        ),
        types.Tool(
            name="print_pause",
            description="Pause the active print job for a printer.",
            inputSchema={
                "type": "object",
                "properties": {"printer_id": {"type": "integer"}},
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="print_resume",
            description="Resume a paused print job for a printer.",
            inputSchema={
                "type": "object",
                "properties": {"printer_id": {"type": "integer"}},
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="print_cancel",
            description="Cancel the active print job for a printer.",
            inputSchema={
                "type": "object",
                "properties": {"printer_id": {"type": "integer"}},
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="cloud_file_list",
            description="List files in Anycubic cloud storage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printable": {"type": "boolean"},
                    "machine_type": {"type": "integer"},
                    "page": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"files": {"type": "array", "items": {"type": "object"}}},
                "required": ["files"],
            },
        ),
        types.Tool(
            name="cloud_file_upload",
            description="Upload a file to Anycubic cloud storage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "save_in_cloud": {"type": "boolean"},
                },
                "required": ["filepath"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "cloud_file_id": {"type": "integer"},
                    "saved_in_cloud": {"type": "boolean"},
                    "latest_cloud_file": {"type": "object"},
                },
                "required": ["cloud_file_id", "saved_in_cloud", "latest_cloud_file"],
            },
        ),
        types.Tool(
            name="cloud_file_delete",
            description="Delete a file from Anycubic cloud storage.",
            inputSchema={
                "type": "object",
                "properties": {"cloud_file_id": {"type": "integer"}},
                "required": ["cloud_file_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
            },
        ),
        types.Tool(
            name="print_upload",
            description=(
                "Upload a G-code file and start printing it. "
                "slot_index_list is 1-based (slot 1..4, or 1..8 for dual ACE)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "filepath": {"type": "string"},
                    "slot_index_list": {"type": "array", "items": {"type": "integer"}},
                    "save_in_cloud": {"type": "boolean"},
                },
                "required": ["printer_id", "filepath"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"result": {"type": "object"}},
                "required": ["result"],
            },
        ),
        types.Tool(
            name="print_cloud_gcode",
            description=(
                "Start a print from an existing cloud G-code ID. "
                "slot_index_list is 1-based (slot 1..4, or 1..8 for dual ACE)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "gcode_id": {"type": "integer"},
                    "slot_index_list": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["printer_id", "gcode_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"result": {"type": "object"}},
                "required": ["result"],
            },
        ),
        types.Tool(
            name="print_cloud_file",
            description=(
                "Start a print from a cloud file ID or file name. "
                "slot_index_list is 1-based (slot 1..4, or 1..8 for dual ACE)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "cloud_file_id": {"type": "integer"},
                    "file_name": {"type": "string"},
                    "slot_index_list": {"type": "array", "items": {"type": "integer"}},
                    "page": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"result": {"type": "object"}},
                "required": ["result"],
            },
        ),
        types.Tool(
            name="ace_set_slot",
            description="Set ACE slot color and material type. slot_index is 1-based.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "slot_index": {"type": "integer"},
                    "material_type": {"type": "string"},
                    "color_rgb": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 0, "maximum": 255},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id", "slot_index", "color_rgb"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="ace_feed_filament",
            description="Feed filament for an ACE slot. slot_index is 1-based.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "slot_index": {"type": "integer"},
                    "finish": {"type": "boolean"},
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id", "slot_index"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="ace_retract_filament",
            description="Retract filament from the ACE unit.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="ace_set_auto_feed",
            description="Enable or disable ACE auto-feed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "enabled": {"type": "boolean"},
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id", "enabled"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="ace_dry_start",
            description="Start ACE drying for a given duration (minutes) and target temp (C).",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "duration": {"type": "integer"},
                    "target_temp": {"type": "integer"},
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id", "duration", "target_temp"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
        types.Tool(
            name="ace_dry_stop",
            description="Stop ACE drying. If box_id is omitted, stops all boxes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "printer_id": {"type": "integer"},
                    "box_id": {"type": "integer"},
                },
                "required": ["printer_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "order_msg_id": {"type": "string"},
                },
                "required": ["ok", "order_msg_id"],
            },
        ),
    ]


def build_server(client: AnycubicClient) -> Server:
    server = Server(
        name=SERVER_NAME,
        version=SERVER_VERSION,
        instructions=(
            "Use auth_set to configure tokens, then call printer_list, printer_status, "
            "and print/ACE tools to control your Anycubic printer."
        ),
    )

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return _tools()

    @server.call_tool()
    async def call_tool(tool_name: str, arguments: dict[str, Any]):
        if tool_name == "auth_set":
            auth_mode = arguments["auth_mode"]
            token = arguments["token"]
            device_id = arguments.get("device_id")
            save = bool(arguments.get("save", False))
            client.set_auth(auth_mode=auth_mode, auth_token=token, device_id=device_id)
            await client.ensure_auth()
            parsed = parse_auth_mode(auth_mode)
            status = client.auth_status()
            config_path = client.config.config_path
            if save:
                save_config(
                    config_path=config_path,
                    auth_mode=auth_mode,
                    auth_token=token,
                    device_id=device_id,
                    log_level=client.config.log_level,
                )
            return {
                "ok": True,
                "auth_mode": parsed.name.lower() if parsed else "unknown",
                "mqtt_supported": status.mqtt_supported,
                "saved": save,
                "config_path": str(config_path),
            }

        if tool_name == "auth_status":
            status = client.auth_status()
            return {
                "auth_mode": status.auth_mode or "unset",
                "token_present": status.token_present,
                "device_id_present": status.device_id_present,
                "mqtt_supported": status.mqtt_supported,
            }

        if tool_name == "printer_list":
            printers = await client.list_printers()
            return {
                "printers": [
                    client.serialize_printer(printer, include_project=False)
                    for printer in printers
                ]
            }

        if tool_name == "printer_status":
            printer_id = int(arguments["printer_id"])
            include_project = bool(arguments.get("include_project", True))
            printer = await client.get_printer(printer_id, with_project=include_project)
            return {"printer": client.serialize_printer(printer, include_project=include_project)}

        if tool_name in ("print_pause", "print_resume", "print_cancel"):
            printer_id = int(arguments["printer_id"])
            printer = await client.get_printer(printer_id, with_project=True)
            if tool_name == "print_pause":
                msg_id = await client.api.pause_print(printer)
            elif tool_name == "print_resume":
                msg_id = await client.api.resume_print(printer)
            else:
                msg_id = await client.api.cancel_print(printer)
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "cloud_file_list":
            printable = arguments.get("printable")
            machine_type = arguments.get("machine_type")
            page = int(arguments.get("page", 1))
            limit = int(arguments.get("limit", 20))
            files = await client.api.get_user_cloud_files(
                printable=printable,
                machine_type=machine_type,
                page=page,
                limit=limit,
            )
            return {
                "files": [
                    client.serialize_cloud_file(file) for file in (files or [])
                ]
            }

        if tool_name == "cloud_file_upload":
            filepath = Path(arguments["filepath"]).expanduser()
            if not filepath.exists():
                raise ValueError(f"File not found: {filepath}")
            save_in_cloud = bool(arguments.get("save_in_cloud", True))
            cloud_file_id = await client.api.upload_file_to_cloud(
                full_file_path=str(filepath),
                temp_file=not save_in_cloud,
            )
            latest = await client.api.get_latest_cloud_file()
            latest_payload = client.serialize_cloud_file(latest) if latest else {}
            return {
                "cloud_file_id": int(cloud_file_id),
                "saved_in_cloud": save_in_cloud,
                "latest_cloud_file": latest_payload,
            }

        if tool_name == "cloud_file_delete":
            cloud_file_id = int(arguments["cloud_file_id"])
            ok = await client.api.delete_file_from_cloud(cloud_file_id)
            return {"ok": bool(ok)}

        if tool_name == "print_upload":
            printer_id = int(arguments["printer_id"])
            filepath = Path(arguments["filepath"]).expanduser()
            if not filepath.exists():
                raise ValueError(f"File not found: {filepath}")
            slot_index_list = _slot_list_to_zero_based(arguments.get("slot_index_list"))
            save_in_cloud = bool(arguments.get("save_in_cloud", True))
            printer = await client.get_printer(printer_id, with_project=False)
            if save_in_cloud:
                resp = await client.api.print_and_upload_save_in_cloud(
                    printer=printer,
                    full_file_path=str(filepath),
                    slot_index_list=slot_index_list,
                )
            else:
                resp = await client.api.print_and_upload_no_cloud_save(
                    printer=printer,
                    full_file_path=str(filepath),
                    slot_index_list=slot_index_list,
                )
            return {"result": resp.event_dict}

        if tool_name == "print_cloud_gcode":
            printer_id = int(arguments["printer_id"])
            gcode_id = int(arguments["gcode_id"])
            slot_index_list = _slot_list_to_zero_based(arguments.get("slot_index_list"))
            printer = await client.get_printer(printer_id, with_project=False)
            resp = await client.api.print_with_cloud_gcode_id(
                printer=printer,
                gcode_id=gcode_id,
                slot_index_list=slot_index_list,
            )
            return {"result": resp.event_dict}

        if tool_name == "print_cloud_file":
            printer_id = int(arguments["printer_id"])
            cloud_file_id = arguments.get("cloud_file_id")
            file_name = arguments.get("file_name")
            page = int(arguments.get("page", 1))
            limit = int(arguments.get("limit", 50))
            slot_index_list = _slot_list_to_zero_based(arguments.get("slot_index_list"))

            if cloud_file_id is None and not file_name:
                raise ValueError("Provide cloud_file_id or file_name.")

            files = await client.api.get_user_cloud_files(
                printable=True,
                machine_type=0,
                page=page,
                limit=limit,
            )
            match = None
            for file in files or []:
                if cloud_file_id is not None and file.id == int(cloud_file_id):
                    match = file
                    break
                if file_name and file.old_filename == file_name:
                    match = file
                    break

            if match is None or match.gcode_id is None:
                raise ValueError("Cloud file not found or missing gcode_id.")

            printer = await client.get_printer(printer_id, with_project=False)
            resp = await client.api.print_with_cloud_gcode_id(
                printer=printer,
                gcode_id=match.gcode_id,
                slot_index_list=slot_index_list,
            )
            return {"result": resp.event_dict}

        if tool_name == "ace_set_slot":
            printer_id = int(arguments["printer_id"])
            slot_index = int(arguments["slot_index"]) - 1
            material_type = arguments.get("material_type", "PLA")
            color_rgb = arguments["color_rgb"]
            box_id = int(arguments.get("box_id", 0))
            if len(color_rgb) != 3:
                raise ValueError("color_rgb must be [R, G, B].")
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_set_slot(
                printer=printer,
                slot_index=slot_index,
                slot_material_type=material_type,
                slot_color_red=int(color_rgb[0]),
                slot_color_green=int(color_rgb[1]),
                slot_color_blue=int(color_rgb[2]),
                box_id=box_id,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "ace_feed_filament":
            printer_id = int(arguments["printer_id"])
            slot_index = int(arguments["slot_index"]) - 1
            finish = bool(arguments.get("finish", False))
            box_id = int(arguments.get("box_id", 0))
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_feed_filament(
                printer=printer,
                slot_index=slot_index,
                box_id=box_id,
                finish=finish,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "ace_retract_filament":
            printer_id = int(arguments["printer_id"])
            box_id = int(arguments.get("box_id", 0))
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_retract_filament(
                printer=printer,
                box_id=box_id,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "ace_set_auto_feed":
            printer_id = int(arguments["printer_id"])
            enabled = bool(arguments["enabled"])
            box_id = int(arguments.get("box_id", 0))
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_set_auto_feed(
                printer=printer,
                enabled=enabled,
                box_id=box_id,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "ace_dry_start":
            printer_id = int(arguments["printer_id"])
            duration = int(arguments["duration"])
            target_temp = int(arguments["target_temp"])
            box_id = int(arguments.get("box_id", 0))
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_drying_start(
                printer=printer,
                duration=duration,
                target_temp=target_temp,
                box_id=box_id,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        if tool_name == "ace_dry_stop":
            printer_id = int(arguments["printer_id"])
            box_id = int(arguments.get("box_id", -1))
            printer = await client.get_printer(printer_id, with_project=False)
            msg_id = await client.api.multi_color_box_drying_stop(
                printer=printer,
                box_id=box_id,
            )
            return {"ok": bool(msg_id), "order_msg_id": str(msg_id) if msg_id else ""}

        raise ValueError(f"Unknown tool: {tool_name}")

    return server


async def run_stdio_server() -> None:
    config = load_config()
    logger = _build_logger(config.log_level)
    client = AnycubicClient(config, logger)
    await client.start()
    server = build_server(client)
    init_options = server.create_initialization_options()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)
    finally:
        await client.close()


def _build_http_app(server: Server, client: AnycubicClient):
    from contextlib import asynccontextmanager

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Route

    session_manager = StreamableHTTPSessionManager(server)

    @asynccontextmanager
    async def lifespan(app: Starlette):
        await client.start()
        async with session_manager.run():
            yield
        await client.close()

    routes = [
        Route("/mcp", session_manager.handle_request, methods=["GET", "POST", "DELETE"]),
    ]
    return Starlette(routes=routes, lifespan=lifespan)


def run_http_server(host: str, port: int) -> None:
    import uvicorn

    config = load_config()
    logger = _build_logger(config.log_level)
    client = AnycubicClient(config, logger)
    server = build_server(client)
    app = _build_http_app(server, client)
    uvicorn.run(app, host=host, port=port, log_level="info")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anycubic Cloud MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP server instead of stdio.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host address.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.http:
        run_http_server(args.host, args.port)
    else:
        anyio.run(run_stdio_server)


if __name__ == "__main__":
    main()
