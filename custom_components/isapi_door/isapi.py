"""ISAPI device classes."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

import aiohttp
from defusedxml.ElementTree import fromstring
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.isapi_door.const import DOMAIN

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from homeassistant.core import HomeAssistant

    from custom_components.isapi_door import IsapiConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class IsapiConfig:
    """Configuration object for reallife isapi device."""

    host: str
    username: str
    password: str
    device_info: IsapiDeviceInfo


@dataclass
class IsapiDeviceInfo:
    """Device info from API."""

    device_name: str
    device_id: str
    device_model: str
    device_serial: str
    device_firmware: str


type IsapiIoType = Literal[
    "disable", "electricLock", "custom", "openDoor", "doorStatus"
]


@dataclass
class IsapiIOChannel:
    """IO Channel."""

    id: str
    name: str
    iotype: IsapiIoType


class Isapi:
    """Class representing the isapi communication."""

    ns = "{http://www.isapi.org/ver20/XMLSchema}"

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize isapi requests."""
        self._auth = aiohttp.DigestAuthMiddleware(login=username, password=password)
        self._host = host
        self._username = username
        self._password = password

    async def _isapi_request(self, url: str) -> Element[str]:
        session = aiohttp.ClientSession(middlewares=(self._auth,))
        response = await session.request("GET", f"http://{self._host}{url}")
        content = await response.content.read()
        await session.close()
        _LOGGER.debug(content)
        return fromstring(content)

    def _coalesce(self, text: Element[str] | None, alternative: str) -> str:
        return (text.text if text is not None else alternative) or alternative

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        user_check = (await self._isapi_request("/ISAPI/Security/userCheck")).find(
            f"{self.ns}statusString"
        )

        return user_check is not None and user_check.text == "OK"

    async def trigger_door_output(self, output_id: str) -> Element[str]:
        """Request door opener relais to trigger."""
        session = aiohttp.ClientSession(middlewares=(self._auth,))
        response = await session.request(
            "PUT",
            f"http://{self._host}/ISAPI/AccessControl/RemoteControl/door/{output_id}",
            data="<RemoteControlDoor><cmd>open</cmd></RemoteControlDoor>",
        )
        content = await response.content.read()
        await session.close()
        _LOGGER.debug(content)
        return fromstring(content)

    async def get_device_info(self) -> IsapiDeviceInfo:
        """Request device information from real device."""
        device_capabilities = await self._isapi_request("/ISAPI/System/deviceInfo")
        device_name = device_capabilities.find(f"{self.ns}deviceName")
        device_id = device_capabilities.find(f"{self.ns}deviceID")
        device_model = device_capabilities.find(f"{self.ns}model")
        device_serial = device_capabilities.find(f"{self.ns}serialNumber")
        device_firmware = device_capabilities.find(f"{self.ns}firmwareVersion")
        return IsapiDeviceInfo(
            self._coalesce(device_name, ""),
            self._coalesce(device_id, ""),
            self._coalesce(device_model, ""),
            self._coalesce(device_serial, ""),
            self._coalesce(device_firmware, ""),
        )

    async def get_output_channels(self) -> list[IsapiIOChannel]:
        """Get a list of available output channels."""
        output_ports = (await self._isapi_request("/ISAPI/System/IO/outputs")).findall(
            f"{self.ns}IOOutputPort"
        )
        return [
            IsapiIOChannel(
                id=self._coalesce(port.find(f"{self.ns}id"), ""),
                name=self._coalesce(port.find(f"{self.ns}name"), ""),
                iotype=cast(
                    "IsapiIoType",
                    self._coalesce(
                        port.find(f"{self.ns}IOUseType"),
                        "disable",
                    ),
                ),
            )
            for port in output_ports
        ]

    async def get_input_channels(self) -> list[IsapiIOChannel]:
        """Get a list of available input channels."""
        input_ports = (await self._isapi_request("/ISAPI/System/IO/inputs")).findall(
            f"{self.ns}IOInputPort"
        )
        return [
            IsapiIOChannel(
                id=self._coalesce(port.find(f"{self.ns}id"), ""),
                name=self._coalesce(port.find(f"{self.ns}name"), ""),
                iotype=cast(
                    "IsapiIoType",
                    self._coalesce(
                        port.find(f"{self.ns}IOUseType"),
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
        _: HomeAssistant,
        entry: IsapiConfigEntry,
        api: Isapi,
        device_info: IsapiDeviceInfo,
    ) -> None:
        """Initialize the device class."""
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
