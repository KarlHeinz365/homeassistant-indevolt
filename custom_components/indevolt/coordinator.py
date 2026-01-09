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
    def __init__(self, hass, entry: ConfigEntry):
        scan_interval = entry.options.get("scan_interval", entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{entry.entry_id}", update_interval=timedelta(seconds=scan_interval))
        self.config_entry = entry
        self.api = IndevoltAPI(host=entry.data['host'], port=entry.data['port'], session=async_get_clientsession(hass))

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            gen = get_device_gen(self.config_entry.data.get("device_model"))
            sensor_list = SENSORS_GEN1 if gen == 1 else SENSORS_GEN2
            keys = [int(desc.key) for desc in sensor_list]
            
            data = await self.api.fetch_data(keys)
            if not data:
                raise UpdateFailed("No data received")

            # --- Active Safety Watchdog ---
            current_soc = data.get("6002") # Battery SOC key
            battery_state = data.get("6001") # State key (1002 = Discharging)
            min_soc = self.config_entry.options.get("virtual_min_soc", 8)

            if current_soc is not None and battery_state == 1002:
                if current_soc <= min_soc:
                    _LOGGER.warning("Watchdog: SOC (%s%%) <= Min-SOC (%s%%). Sending Stop command.", current_soc, min_soc)
                    await self.api.async_stop() #

            return data
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err
