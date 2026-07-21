"""Platform for sensor integration."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from custom_components.isapi.isapi import IsapiDevice, IsapiIOChannel

    from .isapi import IsapiConfigEntry


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _: HomeAssistant,
    config: IsapiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    output_channels = await config.runtime_data.api.get_output_channels()
    input_channels = await config.runtime_data.api.get_input_channels()
    sensors: list[SensorEntity] = []
    sensors.extend(
        OutputChannelSensor(channel, config.runtime_data) for channel in output_channels
    )
    sensors.extend(
        InputChannelSensor(channel, config.runtime_data) for channel in input_channels
    )
    async_add_entities(sensors)


class InputChannelSensor(SensorEntity):
    """Input channel."""

    def __init__(self, channel: IsapiIOChannel, device: IsapiDevice) -> None:
        """Initialize input channel."""
        super().__init__()
        self._channel = channel
        self.entity_description = SensorEntityDescription(
            key=f"io.input.{channel.id}",
            name=channel.name,
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:import",
        )
        self.device_info = device.device_info
        self._attr_unique_id = (
            f"{device.device_info.get('serial_number')}_{self.entity_description.key}"
        )
        self._attr_native_value = channel.iotype


class OutputChannelSensor(SensorEntity):
    """Output channel."""

    def __init__(self, channel: IsapiIOChannel, device: IsapiDevice) -> None:
        """Initialize output channel."""
        super().__init__()
        self._channel = channel
        self.entity_description = SensorEntityDescription(
            key=f"io.output.{channel.id}",
            name=channel.name,
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:export",
        )
        self.device_info = device.device_info
        self._attr_unique_id = (
            f"{device.device_info.get('serial_number')}_{self.entity_description.key}"
        )
        self._attr_native_value = channel.iotype
