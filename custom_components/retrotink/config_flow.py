"""Config flow for RetroTINK Serial Remote integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .connection import open_serial_connection
from .const import CONF_DEVICE_MODEL, CONF_SERIAL_PORT, DEVICE_MODELS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_MODEL): vol.In(DEVICE_MODELS),
        vol.Required(CONF_SERIAL_PORT): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    def test_serial() -> bool:
        try:
            with open_serial_connection(data[CONF_SERIAL_PORT]):
                pass
            return True
        except (OSError, ValueError):
            return False

    # Test serial connection in executor since it's blocking
    result = await hass.async_add_executor_job(test_serial)
    
    if not result:
        raise CannotConnect

    # Use device model as the name
    return {"title": data[CONF_DEVICE_MODEL]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RetroTINK Serial Remote."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Check if this serial port is already configured
            await self.async_set_unique_id(user_input[CONF_SERIAL_PORT])
            self._abort_if_unique_id_configured()
            
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
