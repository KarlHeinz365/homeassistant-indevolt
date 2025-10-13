from __future__ import annotations

"""Home Assistant integration for indevolt device."""

import logging
from typing import Any
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
# HIER IST DIE KORREKTUR: DEFAULT_SCAN_INTERVAL wird jetzt importiert
from .const import DOMAIN, PLATFORMS, DEFAULT_SCAN_INTERVAL
from .coordinator import IndevoltCoordinator
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({
    vol.Required("power"): cv.positive_int,
})

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """
    Set up the indevolt integration component.
    """
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up indevolt from a config entry.
    """
    hass.data.setdefault(DOMAIN, {})
    
    try:
        coordinator = IndevoltCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.async_on_unload(entry.add_update_listener(async_update_listener))

        # --- SERVICE REGISTRATION ---
        async def charge(call: ServiceCall):
            """Handle the service call to start charging."""
            power = call.data.get("power")
            await coordinator.api.set_data(f=16, t=47015, v=[1, power, 100])

        async def discharge(call: ServiceCall):
            """Handle the service call to start discharging."""
            power = call.data.get("power")
            await coordinator.api.set_data(f=16, t=47015, v=[2, power, 5])

        async def stop(call: ServiceCall):
            """Handle the service call to stop the battery."""
            await coordinator.api.set_data(f=16, t=47015, v=[0, 0, 0])
            
        async def set_realtime_mode(call: ServiceCall):
            """Handle the service call to force real-time control mode."""
            await coordinator.api.set_data(f=16, t=47005, v=[4])

        hass.services.async_register(DOMAIN, "charge", charge, schema=SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, "discharge", discharge, schema=SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, "stop", stop)
        hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime_mode)
        
        return True 
    
    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting config entry.")
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]
        raise ConfigEntryNotReady from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry and clean up resources.
    """
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return True
    
    hass.services.async_remove(DOMAIN, "charge")
    hass.services.async_remove(DOMAIN, "discharge")
    hass.services.async_remove(DOMAIN, "stop")
    hass.services.async_remove(DOMAIN, "set_realtime_mode")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    
    return unload_ok

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    new_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    
    coordinator.update_interval = timedelta(seconds=new_interval)
    _LOGGER.info(f"Indevolt scan interval updated to {new_interval} seconds")
