from __future__ import annotations

import logging
from typing import Any, Dict
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .indevolt_api import IndevoltAPI
from .utils import get_device_gen
from .sensor import SENSORS_GEN1, SENSORS_GEN2

_LOGGER = logging.getLogger(__name__)

class IndevoltCoordinator(DataUpdateCoordinator):
    """Coordinator for Indevolt device data updates."""
    
    def __init__(self, hass, entry: ConfigEntry):
        scan_interval = entry.options.get(
            "scan_interval", 
            entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        
        self.config_entry = entry
        self.session = async_get_clientsession(hass)
        self.api = IndevoltAPI(
            host=entry.data['host'],
            port=entry.data['port'],
            session=self.session
        )
        self._consecutive_errors = 0
        self._max_consecutive_errors = 3
        self._first_update = True
    
    @property
    def config(self) -> dict:
        """Helper to access combined config data and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            # Generate keys dynamically from sensor definitions
            if get_device_gen(self.config["device_model"]) == 1:
                keys = [int(desc.key) for desc in SENSORS_GEN1]
                sensor_set = "GEN1"
            else:
                keys = [int(desc.key) for desc in SENSORS_GEN2]
                sensor_set = "GEN2"
            
            # Fetch all keys in a single API call
            _LOGGER.debug("Fetching %d %s keys in single request", len(keys), sensor_set)
            data = await self.api.fetch_data(keys)

            if not data:
                _LOGGER.warning("No data received from API")
                if self.data:
                    return self.data
                raise UpdateFailed("No data received from device")

            # On first successful update, log diagnostic info
            if self._first_update:
                returned_keys = set(data.keys())
                requested_keys = set(str(k) for k in keys)
                
                missing_keys = requested_keys - returned_keys
                if missing_keys:
                    _LOGGER.warning(
                        "Device did not return data for keys: %s",
                        sorted(missing_keys)
                    )
                
                _LOGGER.info(
                    "First update successful. Received %d/%d keys",
                    len(returned_keys & requested_keys),
                    len(requested_keys)
                )
                self._first_update = False

            # Reset error counter on success
            self._consecutive_errors = 0
            return data
        
        except Exception as err:
            self._consecutive_errors += 1
            
            # Log with appropriate severity
            if self._consecutive_errors <= self._max_consecutive_errors:
                _LOGGER.warning(
                    "Failed to update (attempt %d/%d): %s",
                    self._consecutive_errors,
                    self._max_consecutive_errors,
                    str(err)
                )
            else:
                _LOGGER.error(
                    "Persistent connection failure to device: %s",
                    str(err)
                )
            
            # Return stale data if available, otherwise raise
            if self.data:
                _LOGGER.debug("Returning stale data due to update failure")
                return self.data
            
            raise UpdateFailed(f"Failed to fetch data: {err}") from err
    
    async def async_shutdown(self) -> None:
        """Clean up resources."""
        _LOGGER.debug("Shutting down Indevolt coordinator")
