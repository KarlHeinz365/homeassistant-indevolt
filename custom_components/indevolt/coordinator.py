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
# NEUER IMPORT: Wir brauchen die Sensor-Definitionen für die dynamischen Keys
from .sensor import SENSORS_GEN1, SENSORS_GEN2

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

    # --- START DER OPTIMIERTEN METHODE (Optimierung 1) ---

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        
        try:
            keys: list[int] = [] # Definiere als Liste von Integers
            
            if get_device_gen(self.config["device_model"])==1:
                # OPTIMIERUNG: Erstelle die Key-Liste dynamisch
                # KORREKTUR: Wandle Keys in int() um
                keys=[int(desc.key) for desc in SENSORS_GEN1]
            else:
                # OPTIMIERUNG: Erstelle die Key-Liste dynamisch
                # KORREKTUR: Wandle Keys in int() um
                keys=[int(desc.key) for desc in SENSORS_GEN2]
            
            # --- HAUPTOPTIMIERUNG: ---
            # Rufe ALLE Keys in EINEM EINZIGEN API-Aufruf ab
            _LOGGER.debug(f"Fetching {len(keys)} keys in a single request")
            data = await self.api.fetch_data(keys)

            if not data:
                _LOGGER.warning("No data received from API, returning last known data or empty dict.")
                return self.data or {}

            # Daten sind bereits ein dict { "key_str": value },
            # da die API Strings zurückgibt.
            return data
        
        except Exception as err:
            # OPTIMIERUNG: Fange spezifische API-Fehler ab und melde sie korrekt
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Failed to fetch data: {err}") from err

    # --- ENDE DER OPTIMIERTEN METHODE ---
