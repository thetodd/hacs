"""Switch implementation for door opener."""

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from custom_components.isapi_door.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from custom_components.isapi_door.isapi import IsapiDevice, IsapiIOChannel

    from .isapi import IsapiConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _: HomeAssistant,
    config: IsapiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    output_channels = await config.runtime_data.api.get_output_channels()

    locks: list[IsapiLock] = [
        IsapiLock(config.runtime_data, channel)
        for channel in output_channels
        if channel.iotype == "electricLock"
    ]

    async_add_entities(locks)


class IsapiLock(SwitchEntity):
    """Represents a door opener."""

    def __init__(self, device: IsapiDevice, channel: IsapiIOChannel) -> None:
        """Initialize door opener."""
        super().__init__()
        self.device = device
        self.channel = channel
        self.entity_description = SwitchEntityDescription(
            key=f"{DOMAIN}.lock.{channel.id}",
            name=channel.name,
        )
        self.device_info = device.device_info
        self._attr_unique_id = (
            f"{device.device_info.get('serial_number')}_{self.entity_description.key}"
        )
        self.is_on = False

    async def async_turn_on(self) -> None:
        """Unlock all or specified locks."""
        _LOGGER.debug("Unlock %s", self.channel.id)
        self.is_on = True
        self.schedule_update_ha_state()
        _ = await self.device.api.trigger_door_output(self.channel.id)
        await asyncio.sleep(3)
        self.is_on = False
        self.schedule_update_ha_state()

    def turn_off(self) -> None:
        """Turn off lock."""
