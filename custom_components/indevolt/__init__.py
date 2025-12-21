from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN, PLATFORMS
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = IndevoltCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if len(hass.data[DOMAIN]) == 1:
        await async_register_services(hass)
    return True

async def async_register_services(hass: HomeAssistant):
    async def get_coord(call: ServiceCall):
        return list(hass.data[DOMAIN].values())[0]

    async def set_self_consumption(call):
        await (await get_coord(call)).api.async_set_self_consumption_mode()
    async def set_schedule(call):
        await (await get_coord(call)).api.async_set_schedule_mode()
    async def set_realtime(call):
        await (await get_coord(call)).api.async_set_realtime_mode()
    async def charge(call):
        await (await get_coord(call)).api.async_charge(call.data["power"])
    async def discharge(call):
        await (await get_coord(call)).api.async_discharge(call.data["power"])
    async def stop(call):
        await (await get_coord(call)).api.async_stop()

    hass.services.async_register(DOMAIN, "set_self_consumption_mode", set_self_consumption)
    hass.services.async_register(DOMAIN, "set_schedule_mode", set_schedule)
    hass.services.async_register(DOMAIN, "set_realtime_mode", set_realtime)
    hass.services.async_register(DOMAIN, "charge", charge)
    hass.services.async_register(DOMAIN, "discharge", discharge)
    hass.services.async_register(DOMAIN, "stop", stop)
