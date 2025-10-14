"""Config flow for inDevolt integration."""
from __future__ import annotations

import logging
import asyncio
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, SUPPORTED_MODELS
from .indevolt_api import IndevoltAPI

_LOGGER = logging.getLogger(__name__)

# Schema for the initial user setup. Note: scan_interval is moved to options.
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required("device_model"): vol.In(SUPPORTED_MODELS),
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
})

class IndevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for inDevolt."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> IndevoltOptionsFlowHandler:
        """Get the options flow for this handler."""
        return IndevoltOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Create an API instance to test the connection
                api = IndevoltAPI(
                    host=user_input[CONF_HOST],
                    port=user_input.get(CONF_PORT, DEFAULT_PORT),
                    session=async_get_clientsession(self.hass)
                )
                
                # Fetch serial number (key 1000) and FW version (key 1003) to validate the device
                # This is a much more reliable test than fetching key '0'
                device_info = await api.fetch_data(["1000", "1003"])
                serial_number = device_info.get("1000")
                fw_version = device_info.get("1003")

                if not serial_number:
                    # If we don't get a serial number, it's not a valid device
                    raise ConnectionError("Could not retrieve serial number from device")

                # --- WICHTIG: Setze die einzigartige ID ---
                # This prevents the user from adding the same device multiple times.
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()

                # Data that will be stored in the config entry (immutable data)
                data_to_save = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                    "device_model": user_input["device_model"],
                    "sn": serial_number,
                    "fw_version": fw_version,
                }

                # Create the entry, using the SN in the title for clarity
                return self.async_create_entry(title=f"inDevolt {serial_number}", data=data_to_save)

            except (ConnectionError, asyncio.TimeoutError):
                # If connection fails, show a 'cannot_connect' error in the UI
                errors["base"] = "cannot_connect"
            except Exception:
                # For any other unexpected error, show a generic 'unknown' error
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show the form again if there was an error or it's the first time
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class IndevoltOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # If the user submitted new options, create an entry to save them
            return self.async_create_entry(title="", data=user_input)

        # Define the schema for the options form
        # We get the default from the existing options, falling back to the default constant
        options_schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=5)), # Ensure interval is at least 5 seconds
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)

