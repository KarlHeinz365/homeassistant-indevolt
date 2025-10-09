from __future__ import annotations

"""Home Assistant integration for indevolt device."""

import logging
from typing import Any
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, PLATFORMS
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({
    vol.Required("power"): cv.positive_int,
})

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """
    Set up the indevolt integration component.
    This function is called when the integration is added to the Home Assistant configuration.
    No component-level setup needed.
    """
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up indevolt from a config entry.
    This is the main setup function called when a config entry is added.
    It initializes the coordinator and sets up platforms and services.
    """
    hass.data.setdefault(DOMAIN, {})
    
    try:
        coordinator = IndevoltCoordinator(hass, entry.data)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # --- NEW SERVICE REGISTRATION ---
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

        hass.services.async_register(DOMAIN, "charge", charge, schema=SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, "discharge", discharge, schema=SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN, "stop", stop)
        # --- END NEW SERVICE REGISTRATION ---
        
        return True 
    
    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting config entry.")
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]
        raise ConfigEntryNotReady from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry and clean up resources.
    This is called when the integration is removed or reloaded.
    """
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.debug("Config entry %s not loaded or already unloaded", entry.entry_id)
        return True
    
    # --- UNLOAD SERVICES ---
    hass.services.async_remove(DOMAIN, "charge")
    hass.services.async_remove(DOMAIN, "discharge")
    hass.services.async_remove(DOMAIN, "stop")
    # --- END UNLOAD SERVICES ---

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    
    return unload_ok
