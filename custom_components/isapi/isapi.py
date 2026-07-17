"""A ISAPI device."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.isapi.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from custom_components.isapi import IsapiConfigEntry


@dataclass
class IsapiConfig:
    host: str
    username: str
    password: str
    device_info: IsapiDeviceInfo


@dataclass
class IsapiDeviceInfo:
    device_name: str
    device_id: str
    device_model: str
    device_serial: str
    device_firmware: str


class Isapi:
    """Class representing an isapi."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize isapi requests."""
        auth = aiohttp.DigestAuthMiddleware(login=username, password=password)
        self._session = aiohttp.ClientSession(middlewares=(auth,))
        self._host = host
        self._username = username
        self._password = password

    async def _isapi_request(self, url: str):
        response = await self._session.request("GET", f"{self._host}{url}")
        content = await response.content.read()
        return ET.fromstring(content)

    def _coalesce(self, text: ET.Element[str] | None, alternative: str) -> str:
        return (text.text if text is not None else alternative) or alternative

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        user_check = (await self._isapi_request("/ISAPI/Security/userCheck")).find(
            "{http://www.isapi.org/ver20/XMLSchema}statusString"
        )

        return user_check is not None and user_check.text == "OK"

    async def get_device_info(self) -> IsapiDeviceInfo:
        deviceCapabilities = await self._isapi_request("/ISAPI/System/deviceInfo")
        device_name = deviceCapabilities.find(
            "{http://www.isapi.org/ver20/XMLSchema}deviceName"
        )
        device_id = deviceCapabilities.find(
            "{http://www.isapi.org/ver20/XMLSchema}deviceID"
        )
        device_model = deviceCapabilities.find(
            "{http://www.isapi.org/ver20/XMLSchema}model"
        )
        device_serial = deviceCapabilities.find(
            "{http://www.isapi.org/ver20/XMLSchema}serialNumber"
        )
        device_firmware = deviceCapabilities.find(
            "{http://www.isapi.org/ver20/XMLSchema}firmwareVersion"
        )
        return IsapiDeviceInfo(
            self._coalesce(device_name, ""),
            self._coalesce(device_id, ""),
            self._coalesce(device_model, ""),
            self._coalesce(device_serial, ""),
            self._coalesce(device_firmware, ""),
        )


class IsapiDevice:
    """Class representing an isapi enabled device."""

    def __init__(self, hass: HomeAssistant, entry: IsapiConfigEntry) -> None:
        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.data["device_id"])},
            manufacturer="HikVision",
            sw_version=entry.data["device_firmware"],
            model=entry.data["device_model"],
            serial_number=entry.data["device_serial"],
            name=entry.data["device_name"],
        )
