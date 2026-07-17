"""Platform for sensor integration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityDescription
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from custom_components.isapi.isapi import IsapiDevice

    from .isapi import IsapiConfigEntry

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo


async def async_setup_entry(
    hass: HomeAssistant,
    config: IsapiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities([ExampleSensor(config.runtime_data)])


class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device: IsapiDevice) -> None:
        """Initialize version entities."""
        super().__init__()
        self.entity_description = SensorEntityDescription(
            key="isapi.example_temp",
            name="Example Temperatur",
            translation_key="version",
        )
        self.device_info = device.device_info
        self._attr_unique_id = f"12345_{self.entity_description.key}"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = 23
