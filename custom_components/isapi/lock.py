from typing import TYPE_CHECKING

from anyio import Lock
from homeassistant.components.lock import LockEntity, LockEntityDescription

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityDescription
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from custom_components.isapi.isapi import IsapiDevice

    from .isapi import IsapiConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config: IsapiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities([MyLock(config.runtime_data)])


class MyLock(LockEntity):
    def __init__(self, device: IsapiDevice) -> None:
        super().__init__()
        self.entity_description = LockEntityDescription(
            key="isapi.example_door",
            name="Example Door",
            translation_key="version",
        )
        self.device_info = device.device_info
        self._attr_unique_id = f"12345_{self.entity_description.key}"
        self.is_locked = True

    def lock(self) -> None:
        """Unlock all or specified locks."""

    def unlock(self) -> None:
        """Unlock all or specified locks."""

    async def async_update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
