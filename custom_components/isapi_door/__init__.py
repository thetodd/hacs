"""The ISAPI door intercom integration."""

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from . import isapi

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

type IsapiConfigEntry = ConfigEntry[isapi.IsapiDevice]


async def async_setup_entry(hass: HomeAssistant, entry: IsapiConfigEntry) -> bool:
    """Set up isapi door intercom from a config entry."""
    api = isapi.Isapi(
        entry.data["host"], entry.data["username"], entry.data["password"]
    )

    device_info = await api.get_device_info()

    entry.runtime_data = isapi.IsapiDevice(hass, entry, api, device_info)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IsapiConfigEntry) -> bool:
    """Unload the config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
