"""Support for RetroTINK serial remote control."""
from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .connection import open_serial_connection
from .const import (
    COMMAND_MAP,
    CONF_DEVICE_MODEL,
    CONF_SERIAL_PORT,
    DOMAIN,
    POWER_OFF_CMD,
    POWER_ON_CMD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RetroTINK remote from a config entry."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities(
        [RetroTINKRemote(
            config[CONF_DEVICE_MODEL],  # Use device model as name
            config[CONF_DEVICE_MODEL],
            config[CONF_SERIAL_PORT],
            config_entry.entry_id
        )],
        True,
    )


class RetroTINKRemote(RemoteEntity):
    """Representation of a RetroTINK remote control."""

    def __init__(
        self,
        name: str,
        device_model: str,
        serial_port: str,
        entry_id: str,
    ) -> None:
        """Initialize the RetroTINK remote."""
        self._attr_name = name
        self._device_model = device_model
        self._serial_port = serial_port
        self._attr_unique_id = f"{entry_id}_remote"
        self._attr_is_on = False  # Track power state based on commands sent

    @property
    def device_info(self):
        """Return device information about this RetroTINK."""
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "RetroTINK",
            "model": self._device_model,
        }

    def _send_command(self, command: str, is_power_on: bool = False) -> bool:
        """Send a command to the RetroTINK via serial.
        
        Args:
            command: The command to send (will be prefixed with 'remote ' unless it's power on)
            is_power_on: If True, command is 'pwr on' and sent without 'remote ' prefix
        """
        try:
            # Format command - only 'pwr on' doesn't get 'remote' prefix
            if is_power_on:
                cmd = f"{command}\n"
            else:
                cmd = f"remote {command}\n"
                
            _LOGGER.debug("Sending command to %s: %s", self._attr_name, cmd.strip())
            with open_serial_connection(self._serial_port) as ser:
                ser.write(cmd.encode("ascii"))
            return True
            
        except (OSError, ValueError) as err:
            _LOGGER.error("Error sending command to %s: %s", self._attr_name, err)
            return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the remote on (power on the device)."""
        result = await self.hass.async_add_executor_job(
            self._send_command, POWER_ON_CMD, True
        )
        if result:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the remote off (power off the device)."""
        result = await self.hass.async_add_executor_job(
            self._send_command, POWER_OFF_CMD, False
        )
        if result:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to the device.
        
        Args:
            command: A list of commands to send.
            **kwargs: Additional arguments (num_repeats, delay_secs, etc.)
        """
        num_repeats = kwargs.get("num_repeats", 1)
        delay_secs = kwargs.get("delay_secs", 0.4)
        
        for _ in range(num_repeats):
            for cmd in command:
                # Check if this is a power command
                is_power_on = False
                actual_cmd = cmd.lower()
                
                if actual_cmd in ["power_on", "pwr_on"]:
                    actual_cmd = POWER_ON_CMD
                    is_power_on = True
                    self._attr_is_on = True
                elif actual_cmd in ["power_off", "power", "pwr"]:
                    actual_cmd = POWER_OFF_CMD
                    is_power_on = False  # This will get 'remote' prefix
                    self._attr_is_on = False
                else:
                    # Map standard remote commands to RetroTINK commands
                    actual_cmd = COMMAND_MAP.get(actual_cmd, actual_cmd)
                
                # Send the command
                await self.hass.async_add_executor_job(
                    self._send_command, actual_cmd, is_power_on
                )
                
                # Update state if power changed
                if actual_cmd in [POWER_ON_CMD, POWER_OFF_CMD]:
                    self.async_write_ha_state()
                
                # Add delay between commands if there are more to send
                if delay_secs > 0 and (len(command) > 1 or num_repeats > 1):
                    await self.hass.async_add_executor_job(
                        lambda: __import__('time').sleep(delay_secs)
                    )
