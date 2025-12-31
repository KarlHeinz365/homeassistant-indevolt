from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, PLATFORMS, DEFAULT_MAX_CHARGE_POWER, DEFAULT_MAX_DISCHARGE_POWER
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Indevolt from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    try:
        coordinator = IndevoltCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Register services only once
        if len(hass.data[DOMAIN]) == 1:
            await async_register_services(hass)
        return True
    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting up Indevolt")
        raise ConfigEntryNotReady from err

async def async_register_services(hass: HomeAssistant) -> None:
    """Register integration-level services with device selection."""
    
    def get_coordinator_by_device_id(device_id: str | None) -> IndevoltCoordinator:
        """Get coordinator by device_id or return main device."""
        if device_id:
            # Try to find coordinator by device_id
            for coord in hass.data[DOMAIN].values():
                if coord.config_entry.entry_id == device_id:
                    return coord
            raise ValueError(f"Device with ID {device_id} not found")
        
        # Return main device if no device_id specified
        for coord in hass.data[DOMAIN].values():
            if coord.config_entry.options.get("is_main_device", False):
                return coord
        
        # Fallback to first device if no main device set
        return list(hass.data[DOMAIN].values())[0]
    
    def get_all_coordinators() -> list[IndevoltCoordinator]:
        """Get all coordinators."""
        return list(hass.data[DOMAIN].values())

    # --- Power Control Services ---
    async def charge(call: ServiceCall):
        """Charge battery with virtual Min-SOC protection."""
        device_id = call.data.get("device_id")
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 100)
        
        coord = get_coordinator_by_device_id(device_id)
        
        # Check virtual Min-SOC
        virtual_min_soc = coord.config_entry.options.get("virtual_min_soc", 10)
        current_soc = coord.data.get("6002")  # Total Battery SOC
        
        if current_soc is not None and current_soc <= virtual_min_soc:
            _LOGGER.warning(
                "Charging blocked: Current SOC (%s%%) at or below virtual Min-SOC (%s%%)",
                current_soc, virtual_min_soc
            )
            return
        
        # Get max limits from options
        max_charge = coord.config_entry.options.get("max_charge_power", DEFAULT_MAX_CHARGE_POWER)
        await coord.api.async_charge(power, soc_limit, max_charge)

    async def discharge(call: ServiceCall):
        """Discharge battery with virtual Min-SOC protection."""
        device_id = call.data.get("device_id")
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 5)
        
        coord = get_coordinator_by_device_id(device_id)
        
        # Check virtual Min-SOC
        virtual_min_soc = coord.config_entry.options.get("virtual_min_soc", 10)
        current_soc = coord.data.get("6002")  # Total Battery SOC
        
        if current_soc is not None and current_soc <= virtual_min_soc:
            _LOGGER.warning(
                "Discharging blocked: Current SOC (%s%%) at or below virtual Min-SOC (%s%%)",
                current_soc, virtual_min_soc
            )
            return
        
        # Get max limits from options
        max_discharge = coord.config_entry.options.get("max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER)
        await coord.api.async_discharge(power, soc_limit, max_discharge)

    async def stop(call: ServiceCall):
        """Stop charging/discharging."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        await coord.api.async_stop()

    # --- Working Mode Services ---
    async def set_self_consumption_mode(call: ServiceCall):
        """Sets device to Mode 1 (Self-consumed prioritized)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        await coord.api.async_set_mode(1)

    async def set_schedule_mode(call: ServiceCall):
        """Sets device to Mode 2 (Schedule)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        await coord.api.async_set_mode(2)

    async def set_realtime_mode(call: ServiceCall):
        """Sets device to Mode 4 (Real-time control)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        await coord.api.async_set_mode(4)
    
    # --- Cluster Mode Service ---
    async def cluster_charge(call: ServiceCall):
        """Charge battery in cluster mode - sends command only to main device."""
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 100)
        
        # Find main device
        main_coord = None
        for coord in get_all_coordinators():
            if coord.config_entry.options.get("is_main_device", False):
                main_coord = coord
                break
        
        if not main_coord:
            _LOGGER.error("No main device configured for cluster mode")
            return
        
        # Check virtual Min-SOC on main device
        virtual_min_soc = main_coord.config_entry.options.get("virtual_min_soc", 10)
        current_soc = main_coord.data.get("6002")
        
        if current_soc is not None and current_soc <= virtual_min_soc:
            _LOGGER.warning(
                "Cluster charging blocked: Main device SOC (%s%%) at or below virtual Min-SOC (%s%%)",
                current_soc, virtual_min_soc
            )
            return
        
        max_charge = main_coord.config_entry.options.get("max_charge_power", DEFAULT_MAX_CHARGE_POWER)
        await main_coord.api.async_charge(power, soc_limit, max_charge)
        _LOGGER.info("Cluster charge command sent to main device")

    async def cluster_discharge(call: ServiceCall):
        """Discharge battery in cluster mode - sends command only to main device."""
        power = call.data["power"]
        soc_limit = call.data.get("soc_limit", 5)
        
        # Find main device
        main_coord = None
        for coord in get_all_coordinators():
            if coord.config_entry.options.get("is_main_device", False):
                main_coord = coord
                break
        
        if not main_coord:
            _LOGGER.error("No main device configured for cluster mode")
            return
        
        # Check virtual Min-SOC on main device
        virtual_min_soc = main_coord.config_entry.options.get("virtual_min_soc", 10)
        current_soc = main_coord.data.get("6002")
        
        if current_soc is not None and current_soc <= virtual_min_soc:
            _LOGGER.warning(
                "Cluster discharging blocked: Main device SOC (%s%%) at or below virtual Min-SOC (%s%%)",
                current_soc, virtual_min_soc
            )
            return
        
        max_discharge = main_coord.config_entry.options.get("max_discharge_power", DEFAULT_MAX_DISCHARGE_POWER)
        await main_coord.api.async_discharge(power, soc_limit, max_discharge)
        _LOGGER.info("Cluster discharge command sent to main device")

    async def cluster_stop(call: ServiceCall):
        """Stop charging/discharging in cluster mode."""
        # Find main device
        main_coord = None
        for coord in get_all_coordinators():
            if coord.config_entry.options.get("is_main_device", False):
                main_coord = coord
                break
        
        if not main_coord:
            _LOGGER.error("No main device configured for cluster mode")
            return
        
        await main_coord.api.async_stop()
        _LOGGER.info("Cluster stop command sent to main device")

    # Service schemas with device selection
    device_schema = vol.Schema({
        vol.Optional("device_id"): cv.string,
    })
    
    charge_schema = device_schema.extend({
        vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2000)),
        vol.Optional("soc_limit", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })
    
    discharge_schema = device_schema.extend({
        vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2000)),
        vol.Optional("soc_limit", default=5): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })
    
    cluster_charge_schema = vol.Schema({
        vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2000)),
        vol.Optional("soc_limit", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })
    
    cluster_discharge_schema = vol.Schema({
        vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2000)),
        vol.Optional("soc_limit", default=5): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })

    # Register all services
    hass.services.async_register(DOMAIN, "charge", charge, schema=charge_schema)
    hass.services.async_register(DOMAIN, "discharge", discharge, schema=discharge_schema)
    hass.services.async_register(DOMAIN, "stop", stop, schema=device_schema)
    
    hass.services.async_register(DOMAIN, "set_self_consumption_mode", set_self_consumption_mode, schema=device_schema)
    hass.services.async_register(DOMAIN, "set_schedule_mode", set_schedule_mode, schema=device_schema)
    hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime_mode, schema=device_schema)
    
    # Cluster mode services
    hass.services.async_register(DOMAIN, "cluster_charge", cluster_charge, schema=cluster_charge_schema)
    hass.services.async_register(DOMAIN, "cluster_discharge", cluster_discharge, schema=cluster_discharge_schema)
    hass.services.async_register(DOMAIN, "cluster_stop", cluster_stop)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unregister services if this was the last device
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "charge")
            hass.services.async_remove(DOMAIN, "discharge")
            hass.services.async_remove(DOMAIN, "stop")
            hass.services.async_remove(DOMAIN, "set_self_consumption_mode")
            hass.services.async_remove(DOMAIN, "set_schedule_mode")
            hass.services.async_remove(DOMAIN, "set_realtime_mode")
            hass.services.async_remove(DOMAIN, "cluster_charge")
            hass.services.async_remove(DOMAIN, "cluster_discharge")
            hass.services.async_remove(DOMAIN, "cluster_stop")
    
    return unload_ok
