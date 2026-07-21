"""Isapi door intercom config flow."""

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries, exceptions

from .const import DOMAIN
from .isapi import Isapi

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(_: HomeAssistant, data: dict[str, str]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    isapi = Isapi(data["host"], data["username"], data["password"])
    success = await isapi.test_connection()

    if not success:
        raise CannotConnect

    info = await isapi.get_device_info()

    return {
        "host": data["host"],
        "username": data["username"],
        "password": data["password"],
        "device_name": info.device_name,
        "device_id": info.device_id,
        "device_model": info.device_model,
        "device_serial": info.device_serial,
        "device_firmware": info.device_firmware,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(f"{DOMAIN}.{info['device_serial']}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["device_name"], data=info)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Flow for reconfiguraton."""
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(f"{DOMAIN}.{info['device_serial']}")
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    title=info["device_name"],
                    data_updates=info,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=SCHEMA,
                suggested_values=entry.data | (user_input or {}),
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
