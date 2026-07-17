"""A ISAPI device."""

import enum
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

import aiohttp
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.isapi.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from custom_components.isapi import IsapiConfigEntry

_LOGGER = logging.getLogger(__name__)


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


@dataclass
class IsapiSystemCapabilities:
    capability: str


type IsapiIoType = Literal[
    "disable", "electricLock", "custom", "openDoor", "doorStatus"
]


@dataclass
class IsapiIOChannel:
    id: str
    name: str
    iotype: IsapiIoType


class Isapi:
    """Class representing an isapi."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize isapi requests."""
        self._auth = aiohttp.DigestAuthMiddleware(login=username, password=password)
        self._host = host
        self._username = username
        self._password = password

    async def _isapi_request(self, url: str) -> ET.Element[str]:
        session = aiohttp.ClientSession(middlewares=(self._auth,))
        response = await session.request("GET", f"{self._host}{url}")
        content = await response.content.read()
        await session.close()
        _LOGGER.info(content)
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

    async def get_system_capabilities(self) -> IsapiSystemCapabilities:
        return IsapiSystemCapabilities("TODO")

    async def get_output_channels(self) -> list[IsapiIOChannel]:
        output_ports = (await self._isapi_request("/ISAPI/System/IO/outputs")).findall(
            "{http://www.isapi.org/ver20/XMLSchema}IOOutputPort"
        )
        return [
            IsapiIOChannel(
                id=self._coalesce(
                    port.find("{http://www.isapi.org/ver20/XMLSchema}id"), ""
                ),
                name=self._coalesce(
                    port.find("{http://www.isapi.org/ver20/XMLSchema}name"), ""
                ),
                iotype=cast(
                    "IsapiIoType",
                    self._coalesce(
                        port.find("{http://www.isapi.org/ver20/XMLSchema}IOUseType"),
                        "disable",
                    ),
                ),
            )
            for port in output_ports
        ]

    async def get_input_channels(self) -> list[IsapiIOChannel]:
        input_ports = (await self._isapi_request("/ISAPI/System/IO/inputs")).findall(
            "{http://www.isapi.org/ver20/XMLSchema}IOInputPort"
        )
        return [
            IsapiIOChannel(
                id=self._coalesce(
                    port.find("{http://www.isapi.org/ver20/XMLSchema}id"), ""
                ),
                name=self._coalesce(
                    port.find("{http://www.isapi.org/ver20/XMLSchema}name"), ""
                ),
                iotype=cast(
                    "IsapiIoType",
                    self._coalesce(
                        port.find("{http://www.isapi.org/ver20/XMLSchema}IOUseType"),
                        "disable",
                    ),
                ),
            )
            for port in input_ports
        ]


class IsapiDevice:
    """Class representing an isapi enabled device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: IsapiConfigEntry,
        api: Isapi,
        device_info: IsapiDeviceInfo,
    ) -> None:
        self.api = api
        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.data["device_id"])},
            manufacturer="HikVision",
            sw_version=device_info.device_firmware,
            model=device_info.device_model,
            serial_number=device_info.device_serial,
            name=device_info.device_name,
        )
