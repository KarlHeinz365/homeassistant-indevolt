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
from .utils import get_device_gen # Import wieder hinzugefügt

_LOGGER = logging.getLogger(__name__)


class IndevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for inDevolt."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> IndevoltOptionsFlowHandler:
        """Get the options flow for this handler."""
        # KORREKTUR: Der Handler wird jetzt ohne Argument aufgerufen.
        return IndevoltOptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            device_model = user_input["device_model"]
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)

            api = IndevoltAPI(host, port, async_get_clientsession(self.hass))
            
            try:
                # KORREKTUR: Verwende Key 0 für SN (wie im Originalcode und API-Doku) 
                _LOGGER.debug("Attempting to fetch device SN (key 0) for setup")
                data = await api.fetch_data([0]) # Key 0 ist INT
                serial_number = data.get("0") # Antwort-Key ist STR

                if not serial_number:
                    raise ConnectionError("Could not retrieve serial number from device (key 0)")
                
                # Stelle die ursprüngliche FW-Logik aus deiner Datei wieder her
                device_gen = get_device_gen(device_model)
                fw_version = ""
                if device_gen == 1:
                    fw_version = "V1.3.0A_R006.072_M4848_00000039"
                else:
                    fw_version = "V1.3.09_R00D.012_M4801_00000015"
                
                _LOGGER.info(f"Successfully connected to Indevolt device. SN: {serial_number}")

                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()

                data_to_save = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    "device_model": device_model,
                    "sn": serial_number,
                    "fw_version": fw_version, # Verwende die "hardgecodete" FW-Version
                }
                
                options_to_save = {
                    CONF_SCAN_INTERVAL: scan_interval
                }

                return self.async_create_entry(
                    title=f"INDEVOLT {serial_number}", 
                    data=data_to_save,
                    options=options_to_save
                )

            except (ConnectionError, asyncio.TimeoutError):
                _LOGGER.warning("Failed to connect to Indevolt at %s:%s", host, port)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during setup")
                errors["base"] = "unknown"

        # Schema für das *erste* Setup (mit scan_interval)
        setup_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            vol.Required("device_model"): vol.In(SUPPORTED_MODELS),
        })
        
        return self.async_show_form(
            step_id="user", data_schema=setup_schema, errors=errors
        )


class IndevoltOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    # KORREKTUR: Die __init__-Methode wurde entfernt, um die 'deprecated'-Warnung zu beheben.
    # self.config_entry wird von der Basisklasse bereitgestellt.

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # If the user submitted new options, create an entry to save them
            return self.async_create_entry(title="", data=user_input)

        # Definiere das Schema für das Options-Formular
        options_schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=5)), # Intervall muss mind. 5 Sek. sein
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
