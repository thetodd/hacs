"""The Your Integration integration."""

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from . import isapi

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.SENSOR, Platform.LOCK]

type IsapiConfigEntry = ConfigEntry[isapi.IsapiDevice]


async def async_setup_entry(hass: HomeAssistant, entry: IsapiConfigEntry) -> bool:
    """Set up Hello World from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    # api = isapi.Isapi(
    #    entry.data["host"], entry.data["username"], entry.data["password"]
    # )

    entry.runtime_data = isapi.IsapiDevice(hass, entry)

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IsapiConfigEntry) -> bool:
    """Unload the config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
