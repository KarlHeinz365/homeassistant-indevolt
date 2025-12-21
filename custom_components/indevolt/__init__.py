from __future__ import annotations

"""Home Assistant integration for indevolt device."""

import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN, 
    PLATFORMS, 
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MAX_CHARGE_POWER,
    DEFAULT_MAX_DISCHARGE_POWER
)
from .coordinator import IndevoltCoordinator
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

# Service schemas
def build_charge_schema(max_power: int) -> vol.Schema:
    """Build charge service schema with configured max power."""
    return vol.Schema({
        vol.Required("power"): vol.All(cv.positive_int, vol.Range(min=0, max=max_power)),
        vol.Optional("soc_limit", default=100): vol.All(cv.positive_int, vol.Range(min=0, max=100)),
        vol.Optional("device_id"): cv.string,
    })

def build_discharge_schema(max_power: int) -> vol.Schema:
    """Build discharge service schema with configured max power."""
    return vol.Schema({
        vol.Required("power"): vol.All(cv.positive_int, vol.Range(min=0, max=max_power)),
        vol.Optional("soc_limit", default=5): vol.All(cv.positive_int, vol.Range(min=0, max=100)),
        vol.Optional("device_id"): cv.string,
    })

SERVICE_DEVICE_SCHEMA = vol.Schema({
    vol.Optional("device_id"): cv.string,
})

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the indevolt integration component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up indevolt from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    try:
        coordinator = IndevoltCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(async_update_listener))

        if len(hass.data[DOMAIN]) == 1:
            await async_register_services(hass)
        
        return True 
    
    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting config entry.")
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]
        raise ConfigEntryNotReady from err

async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for all Indevolt devices."""
    
    async def get_coordinator_from_call(call: ServiceCall) -> IndevoltCoordinator | None:
        """Get the coordinator for a service call."""
        device_id = call.data.get("device_id")
        if device_id:
            dev_reg = dr.async_get(hass)
            device = dev_reg.async_get(device_id)
            if not device:
                _LOGGER.error("Device %s not found", device_id)
                return None
            for entry_id in device.config_entries:
                if entry_id in hass.data.get(DOMAIN, {}):
                    return hass.data[DOMAIN][entry_id]
        
        coordinators = list(hass.data[DOMAIN].values())
        if not coordinators:
            _LOGGER.error("No Indevolt devices configured")
            return None
        return coordinators[0]

    async def charge(call: ServiceCall):
        """Handle charge service call."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 100)
        max_p = coordinator.config_entry.options.get("max_charge_power", DEFAULT_MAX_CHARGE_POWER)
        try:
            await coordinator.api.async_charge(power, soc_limit, max_p)
        except Exception as err:
            _LOGGER.error("Failed to execute charge: %s", err)

    async def discharge(call: ServiceCall):
        """Handle discharge service call."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 5)
        max_p = coordinator.config_entry.options.get("max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER)
        try:
            await coordinator.api.async_discharge(power, soc_limit, max_p)
        except Exception as err:
            _LOGGER.error("Failed to execute discharge: %s", err)

    async def stop(call: ServiceCall):
        """Handle stop service call."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        try:
            await coordinator.api.async_stop()
        except Exception as err:
            _LOGGER.error("Failed to execute stop: %s", err)
        
    async def set_realtime_mode(call: ServiceCall):
        """Set Mode 4 (Real-time control)."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        try:
            await coordinator.api.async_set_realtime_mode()
        except Exception as err:
            _LOGGER.error("Failed to set realtime mode: %s", err)

    async def set_self_consumption_mode(call: ServiceCall):
        """Set Mode 1 (Self-consumed prioritized)."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        try:
            await coordinator.api.async_set_self_consumption_mode()
        except Exception as err:
            _LOGGER.error("Failed to set self-consumption mode: %s", err)

    async def set_schedule_mode(call: ServiceCall):
        """Set Mode 2 (Charge/discharge schedule)."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator: return
        try:
            await coordinator.api.async_set_schedule_mode()
        except Exception as err:
            _LOGGER.error("Failed to set schedule mode: %s", err)

    coordinators = list(hass.data[DOMAIN].values())
    if coordinators:
        first = coordinators[0]
        max_c = first.config_entry.options.get("max_charge_power", DEFAULT_MAX_CHARGE_POWER)
        max_d = first.config_entry.options.get("max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER)
        charge_schema = build_charge_schema(max_c)
        discharge_schema = build_discharge_schema(max_d)
    else:
        charge_schema = build_charge_schema(DEFAULT_MAX_CHARGE_POWER)
        discharge_schema = build_discharge_schema(DEFAULT_MAX_DISCHARGE_POWER)

    hass.services.async_register(DOMAIN, "charge", charge, schema=charge_schema)
    hass.services.async_register(DOMAIN, "discharge", discharge, schema=discharge_schema)
    hass.services.async_register(DOMAIN, "stop", stop, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime_mode, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, "set_self_consumption_mode", set_self_consumption_mode, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, "set_schedule_mode", set_schedule_mode, schema=SERVICE_DEVICE_SCHEMA)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "charge")
            hass.services.async_remove(DOMAIN, "discharge")
            hass.services.async_remove(DOMAIN, "stop")
            hass.services.async_remove(DOMAIN, "set_realtime_mode")
            hass.services.async_remove(DOMAIN, "set_self_consumption_mode")
            hass.services.async_remove(DOMAIN, "set_schedule_mode")
            hass.data.pop(DOMAIN)
    return unload_ok

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][entry.entry_id]
    new_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=new_interval)
