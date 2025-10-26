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

# Service schemas will be built dynamically based on configured limits
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

        # Register services only once (when first device is added)
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
            # Target specific device
            dev_reg = dr.async_get(hass)
            device = dev_reg.async_get(device_id)
            if not device:
                _LOGGER.error("Device %s not found", device_id)
                return None
            
            # Find config entry associated with this device
            for entry_id in device.config_entries:
                if entry_id in hass.data.get(DOMAIN, {}):
                    return hass.data[DOMAIN][entry_id]
        
        # If no device_id specified, use the first (or only) device
        coordinators = list(hass.data[DOMAIN].values())
        if not coordinators:
            _LOGGER.error("No Indevolt devices configured")
            return None
        
        if len(coordinators) > 1 and not device_id:
            _LOGGER.warning(
                "Multiple Indevolt devices found but no device_id specified. "
                "Using first device. Please specify device_id in service call."
            )
        
        return coordinators[0]

    async def charge(call: ServiceCall):
        """Handle the service call to start charging."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator:
            return
        
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 100)
        
        # Get configured max power from options
        max_charge_power = coordinator.config_entry.options.get(
            "max_charge_power", DEFAULT_MAX_CHARGE_POWER
        )
        
        # Validate against configured limit
        if power > max_charge_power:
            _LOGGER.error(
                "Charge power %dW exceeds configured maximum %dW",
                power, max_charge_power
            )
            raise ValueError(
                f"Charge power {power}W exceeds configured maximum {max_charge_power}W"
            )
        
        _LOGGER.debug("Charge service: power=%sW, soc_limit=%s%%", power, soc_limit)
        try:
            await coordinator.api.async_charge(power, soc_limit, max_charge_power)
        except Exception as err:
            _LOGGER.error("Failed to execute charge command: %s", err)
            raise

    async def discharge(call: ServiceCall):
        """Handle the service call to start discharging."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator:
            return
        
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 5)
        
        # Get configured max power from options
        max_discharge_power = coordinator.config_entry.options.get(
            "max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER
        )
        
        # Validate against configured limit
        if power > max_discharge_power:
            _LOGGER.error(
                "Discharge power %dW exceeds configured maximum %dW",
                power, max_discharge_power
            )
            raise ValueError(
                f"Discharge power {power}W exceeds configured maximum {max_discharge_power}W"
            )
        
        _LOGGER.debug("Discharge service: power=%sW, soc_limit=%s%%", power, soc_limit)
        try:
            await coordinator.api.async_discharge(power, soc_limit, max_discharge_power)
        except Exception as err:
            _LOGGER.error("Failed to execute discharge command: %s", err)
            raise

    async def stop(call: ServiceCall):
        """Handle the service call to stop the battery."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator:
            return
        
        _LOGGER.debug("Stop service called")
        try:
            await coordinator.api.async_stop()
        except Exception as err:
            _LOGGER.error("Failed to execute stop command: %s", err)
            raise
        
    async def set_realtime_mode(call: ServiceCall):
        """Handle the service call to force real-time control mode."""
        coordinator = await get_coordinator_from_call(call)
        if not coordinator:
            return
        
        _LOGGER.debug("Set realtime mode service called")
        try:
            await coordinator.api.async_set_realtime_mode()
        except Exception as err:
            _LOGGER.error("Failed to execute set_realtime_mode command: %s", err)
            raise

    # Register services with dynamic schemas based on first device's config
    # Note: If multiple devices have different limits, the UI will show the max range
    coordinators = list(hass.data[DOMAIN].values())
    if coordinators:
        first_coordinator = coordinators[0]
        max_charge = first_coordinator.config_entry.options.get(
            "max_charge_power", DEFAULT_MAX_CHARGE_POWER
        )
        max_discharge = first_coordinator.config_entry.options.get(
            "max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER
        )
        
        charge_schema = build_charge_schema(max_charge)
        discharge_schema = build_discharge_schema(max_discharge)
    else:
        charge_schema = build_charge_schema(DEFAULT_MAX_CHARGE_POWER)
        discharge_schema = build_discharge_schema(DEFAULT_MAX_DISCHARGE_POWER)

    hass.services.async_register(DOMAIN, "charge", charge, schema=charge_schema)
    hass.services.async_register(DOMAIN, "discharge", discharge, schema=discharge_schema)
    hass.services.async_register(DOMAIN, "stop", stop, schema=SERVICE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime_mode, schema=SERVICE_DEVICE_SCHEMA)
    
    _LOGGER.info(
        "Indevolt services registered (max charge: %dW, max discharge: %dW)",
        max_charge if coordinators else DEFAULT_MAX_CHARGE_POWER,
        max_discharge if coordinators else DEFAULT_MAX_DISCHARGE_POWER
    )

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources."""
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        
        # Remove services only when last device is removed
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "charge")
            hass.services.async_remove(DOMAIN, "discharge")
            hass.services.async_remove(DOMAIN, "stop")
            hass.services.async_remove(DOMAIN, "set_realtime_mode")
            if hass.data.get(DOMAIN) is not None:
                hass.data.pop(DOMAIN)
            _LOGGER.info("Indevolt services unregistered")
    
    return unload_ok

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Update scan interval
    new_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=new_interval)
    _LOGGER.info("Indevolt scan interval updated to %s seconds", new_interval)
    
    # Log power limit updates
    max_charge = entry.options.get("max_charge_power", DEFAULT_MAX_CHARGE_POWER)
    max_discharge = entry.options.get("max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER)
    _LOGGER.info(
        "Indevolt power limits updated: charge=%dW, discharge=%dW",
        max_charge, max_discharge
    )
    
    # Note: Services are global and use the first device's limits for schema validation
    # Individual service calls validate against the specific device's configured limits
