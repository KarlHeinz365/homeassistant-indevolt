import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, SUPPORTED_MODELS
from .utils import get_device_gen
import logging
import asyncio
from .indevolt_api import IndevoltAPI

_LOGGER = logging.getLogger(__name__)

class IndevoltConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration flow for Indevolt integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Erstellt den Options-Flow-Handler."""
        return IndevoltOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """
        Handle the initial user configuration step.
        """
        errors = {}
        if user_input is not None:
            host = user_input["host"]
            port = user_input.get("port", DEFAULT_PORT)
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            device_model = user_input["device_model"]

            api = IndevoltAPI(host, port, async_get_clientsession(self.hass))
            device_gen = get_device_gen(device_model)
            
            try:
                fw_version=""
                if device_gen == 1:
                    fw_version="V1.3.0A_R006.072_M4848_00000039"
                else:
                    fw_version="V1.3.09_R00D.012_M4801_00000015"

                data = await api.fetch_data([0])
                device_sn = data.get("0")

                return self.async_create_entry(
                    title=f"INDEVOLT {device_model} ({host})",
                    data={
                        "host": host,
                        "port": port,
                        "scan_interval": scan_interval,
                        "sn": device_sn,
                        "device_model": device_model,
                        "fw_version": fw_version
                    }
                )
            
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except Exception as e:
                _LOGGER.error("Unknown error occurred while verifying device: %s", str(e), exc_info=True)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("port", default=DEFAULT_PORT): int,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required("device_model"): vol.In(SUPPORTED_MODELS),
            }),
            errors=errors
        )

class IndevoltOptionsFlowHandler(OptionsFlow):
    """Handles options flow for the Indevolt integration."""

    # --- ENDGÜLTIGE KORREKTUR ---
    # Wir definieren __init__, um das 'config_entry' Argument zu akzeptieren,
    # aber lassen den Körper leer, da Home Assistant sich um die Zuweisung kümmert.
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        pass

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "scan_interval",
                    default=self.config_entry.options.get(
                        "scan_interval", 
                        self.config_entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
                    ),
                ): int,
            }),
        )
