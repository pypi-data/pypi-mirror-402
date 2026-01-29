from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

from anycubic_cloud_api import AnycubicMQTTAPI
from anycubic_cloud_api.data_models.files import AnycubicCloudFile
from anycubic_cloud_api.data_models.printer import AnycubicPrinter
from anycubic_cloud_api.data_models.project import AnycubicProject
from anycubic_cloud_api.models.auth import AnycubicAuthMode

from .config import MCPConfig

AUTH_MODE_ALIASES = {
    "web": AnycubicAuthMode.WEB,
    "slicer": AnycubicAuthMode.SLICER,
    "android": AnycubicAuthMode.ANDROID,
}


def parse_auth_mode(value: str | int | AnycubicAuthMode | None) -> AnycubicAuthMode | None:
    if value is None:
        return None
    if isinstance(value, AnycubicAuthMode):
        return value
    if isinstance(value, int):
        return AnycubicAuthMode(value)
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.isdigit():
            return AnycubicAuthMode(int(cleaned))
        return AUTH_MODE_ALIASES.get(cleaned)
    return None


@dataclass
class AuthState:
    auth_mode: str | None
    token_present: bool
    device_id_present: bool
    mqtt_supported: bool


class AnycubicClient:
    def __init__(self, config: MCPConfig, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._session: aiohttp.ClientSession | None = None
        self._cookie_jar: aiohttp.CookieJar | None = None
        self._api: AnycubicMQTTAPI | None = None
        self._auth_mode: AnycubicAuthMode | None = None
        self._auth_token: str | None = None
        self._device_id: str | None = None
        self._auth_ready = False
        self._auth_lock = asyncio.Lock()

    @property
    def api(self) -> AnycubicMQTTAPI:
        if self._api is None:
            raise RuntimeError("Anycubic API not initialized.")
        return self._api

    @property
    def config(self) -> MCPConfig:
        return self._config

    async def start(self) -> None:
        if self._session is not None:
            return
        self._cookie_jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(cookie_jar=self._cookie_jar)
        self._api = AnycubicMQTTAPI(
            session=self._session,
            cookie_jar=self._cookie_jar,
            debug_logger=self._logger,
        )
        if self._config.auth_mode and self._config.auth_token:
            self.set_auth(
                auth_mode=self._config.auth_mode,
                auth_token=self._config.auth_token,
                device_id=self._config.device_id,
            )

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        self._api = None
        self._auth_ready = False

    def set_auth(
        self,
        auth_mode: str | int | AnycubicAuthMode,
        auth_token: str,
        device_id: str | None = None,
    ) -> None:
        parsed_mode = parse_auth_mode(auth_mode)
        if parsed_mode is None:
            raise ValueError(f"Unsupported auth_mode: {auth_mode}")
        if not auth_token:
            raise ValueError("Missing auth token.")

        self._auth_mode = parsed_mode
        self._auth_token = auth_token
        self._device_id = device_id
        self.api.set_authentication(
            auth_token=auth_token,
            auth_mode=parsed_mode,
            device_id=device_id,
        )
        self._auth_ready = False

    async def ensure_auth(self) -> None:
        if not self._auth_mode or not self._auth_token:
            raise ValueError("Authentication not configured.")

        async with self._auth_lock:
            if self._auth_ready and not self.api.tokens_changed:
                return
            ok = await self.api.check_api_tokens()
            if not ok:
                raise ValueError("Authentication failed. Check token and auth mode.")
            self._auth_ready = True

    def auth_status(self) -> AuthState:
        mode = self._auth_mode.name.lower() if self._auth_mode else None
        mqtt_supported = bool(
            self._auth_mode in (AnycubicAuthMode.SLICER, AnycubicAuthMode.ANDROID)
        )
        return AuthState(
            auth_mode=mode,
            token_present=bool(self._auth_token),
            device_id_present=bool(self._device_id),
            mqtt_supported=mqtt_supported,
        )

    async def list_printers(self) -> list[AnycubicPrinter]:
        await self.ensure_auth()
        printers = await self.api.list_my_printers(ignore_init_errors=True)
        return [printer for printer in printers if printer is not None]

    async def get_printer(self, printer_id: int, with_project: bool = False) -> AnycubicPrinter:
        await self.ensure_auth()
        printer = await self.api.printer_info_for_id(
            printer_id,
            ignore_init_errors=True,
        )
        if printer is None:
            raise ValueError(f"Printer not found: {printer_id}")
        if with_project:
            await printer.update_info_from_api(with_project=True)
        return printer

    @staticmethod
    def serialize_project(project: AnycubicProject | None) -> dict[str, Any] | None:
        if project is None:
            return None
        return {
            "id": project.id,
            "gcode_id": project.gcode_id,
            "name": project.name,
            "status": project.print_status,
            "status_message": project.print_status_message,
            "progress_percent": project.progress_percentage,
            "download_progress_percent": project.download_progress_percentage,
            "is_paused": project.print_is_paused,
            "print_time_elapsed_min": project.print_time_elapsed_minutes,
            "print_time_remaining_min": project.print_time_remaining_minutes,
            "current_layer": project.print_current_layer,
            "total_layers": project.print_total_layers,
            "image_url": project.image_url,
        }

    @staticmethod
    def serialize_printer(printer: AnycubicPrinter, include_project: bool = True) -> dict[str, Any]:
        fw = printer.fw_version
        data: dict[str, Any] = {
            "id": printer.id,
            "name": printer.name,
            "model": printer.model,
            "machine_type": printer.machine_type,
            "key": printer.key,
            "online": printer.printer_online,
            "status": printer.current_status,
            "busy": printer.is_busy,
            "available": printer.is_available,
            "firmware": {
                "version": fw.firmware_version if fw else None,
                "update_available": fw.update_available if fw else None,
                "available_version": fw.available_version if fw else None,
            },
            "temps": {
                "nozzle": printer.curr_nozzle_temp,
                "bed": printer.curr_hotbed_temp,
            },
            "connected_peripherals": printer.connected_peripherals,
            "ace": {
                "connected_units": printer.connected_ace_units,
                "auto_feed": printer.primary_multi_color_box_auto_feed,
                "current_temp": printer.primary_multi_color_box_current_temperature,
                "spools": printer.primary_multi_color_box_spool_info_object,
                "drying": {
                    "is_drying": printer.primary_drying_status_is_drying,
                    "target_temp": printer.primary_drying_status_target_temperature,
                    "remaining_time": printer.primary_drying_status_remaining_time,
                    "total_duration": printer.primary_drying_status_total_duration,
                },
            },
        }
        if include_project:
            data["latest_project"] = AnycubicClient.serialize_project(printer.latest_project)
        return data

    @staticmethod
    def serialize_cloud_file(file: AnycubicCloudFile) -> dict[str, Any]:
        return {
            "id": file.id,
            "name": file.old_filename,
            "size_mb": round(file.size_mb, 3),
            "gcode_id": file.gcode_id,
        }
