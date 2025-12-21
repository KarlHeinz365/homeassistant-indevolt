from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
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
        
        if len(hass.data[DOMAIN]) == 1:
            await async_register_services(hass)
        return True
    except Exception as err:
        _LOGGER.exception("Unexpected error occurred while setting up Indevolt")
        raise ConfigEntryNotReady from err

async def async_register_services(hass: HomeAssistant) -> None:
    """Register integration-level services."""
    async def get_coord():
        # Retrieves the first available coordinator instance
        return list(hass.data[DOMAIN].values())[0]

    # --- Existing Power Control Services ---
    async def charge(call: ServiceCall):
        coord = await get_coord()
        await coord.api.async_charge(call.data["power"], call.data.get("soc_limit", 100))

    async def discharge(call: ServiceCall):
        coord = await get_coord()
        await coord.api.async_discharge(call.data["power"], call.data.get("soc_limit", 5))

    async def stop(call: ServiceCall):
        coord = await get_coord()
        await coord.api.async_stop()

    # --- New Working Mode Services ---
    async def set_self_consumption_mode(call: ServiceCall):
        """Sets device to Mode 1 (Self-consumed prioritized)."""
        coord = await get_coord()
        await coord.api.async_set_mode(1)

    async def set_schedule_mode(call: ServiceCall):
        """Sets device to Mode 2 (Schedule)."""
        # Note: PDF Source 489 specifies value 2 for Schedule mode in register 47005
        coord = await get_coord()
        await coord.api.async_set_mode(2)

    async def set_realtime_mode(call: ServiceCall):
        """Sets device to Mode 4 (Real-time control)."""
        # Required before using charge/discharge commands manually
        coord = await get_coord()
        await coord.api.async_set_mode(4)

    # Register all services
    hass.services.async_register(DOMAIN, "charge", charge)
    hass.services.async_register(DOMAIN, "discharge", discharge)
    hass.services.async_register(DOMAIN, "stop", stop)
    
    hass.services.async_register(DOMAIN, "set_self_consumption_mode", set_self_consumption_mode)
    hass.services.async_register(DOMAIN, "set_schedule_mode", set_schedule_mode)
    hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime_mode)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
