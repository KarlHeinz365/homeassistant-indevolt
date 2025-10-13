from __future__ import annotations

"""Home Assistant integration for indevolt device."""

import logging
from typing import Any, Dict
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .indevolt_api import IndevoltAPI
from .utils import get_device_gen

_LOGGER = logging.getLogger(__name__)

class IndevoltCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry: ConfigEntry):
        
        scan_interval = entry.options.get(
            "scan_interval", 
            entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        
        self.config_entry = entry
        self.session = async_get_clientsession(hass)
        
        self.api = IndevoltAPI(
            host=entry.data['host'],
            port=entry.data['port'],
            session=async_get_clientsession(self.hass)
        )
    
    @property
    def config(self) -> dict:
        """Helper to access combined config data and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            keys=[]
            if get_device_gen(self.config["device_model"])==1:
                keys=[7101,1664,1665,2108,1502,1505,2101,2107,1501,6000,6001,6002,6105,6004,6005,6006,6007,7120,21028]
            else:
                keys=[7101,1664,1665,1666,1667,1501,2108,1502,1505,2101,2107,142,6000,6001,6002,6009,6010,6105,6004,6005,6006,6007,7120,11016,667]
            
            data: Dict[str, Any]={}
            for key in keys:
                result=await self.api.fetch_data([key])
                data.update(result)

            return data
        
        except Exception as err:
            _LOGGER.error("API request failed: %s", str(err))
            return self.data or {}
        
        except Exception as err:
            _LOGGER.exception("Unexpected update error")
            # KORRIGIERT: "Failed" zu "UpdateFailed" geändert für korrekte Fehlerbehandlung
            raise UpdateFailed(f"Update failed: {err}") from err
