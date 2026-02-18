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
        scan_interval = entry.options.get("scan_interval", entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{entry.entry_id}", update_interval=timedelta(seconds=scan_interval))
        self.config_entry = entry
        self.api = IndevoltAPI(host=entry.data['host'], port=entry.data['port'], session=async_get_clientsession(hass))
        self._first_update = True
        # Get batch size from config, default to 50
        self.batch_size = entry.options.get("batch_size", entry.data.get("batch_size", 65))

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            # Select correct sensor list based on model
            gen = get_device_gen(self.config_entry.data.get("device_model"))
            sensor_list = SENSORS_GEN1 if gen == 1 else SENSORS_GEN2
            
            # Extract keys as integers for the API call
            keys = [int(desc.key) for desc in sensor_list]
            
            # Fetch data with batching support
            data = await self.api.fetch_data(keys, batch_size=self.batch_size)
            
            # If device is offline, return empty data instead of raising error
            if not data:
                if self._first_update:
                    raise UpdateFailed("No data received from device - check if device is online")
                _LOGGER.debug("Device is offline or unreachable - will retry later")
                # Return last known data if available, otherwise empty dict
                return self.data if self.data else {}

            if self._first_update:
                _LOGGER.info("Successfully connected to Indevolt device (using batch size: %d)", self.batch_size)
                self._first_update = False

            return data
        except UpdateFailed:
            # Re-raise UpdateFailed for first update
            raise
        except Exception as err:
            # For subsequent updates, log but don't raise to avoid spam
            if self._first_update:
                raise UpdateFailed(f"Failed to fetch data: {err}") from err
            _LOGGER.debug(f"Failed to fetch data: {err}")
            return self.data if self.data else {}
