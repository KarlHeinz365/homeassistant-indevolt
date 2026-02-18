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
        try:
            await coord.api.async_charge(power, soc_limit, max_charge)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send charge command - device may be offline: {e}")
            raise

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
        try:
            await coord.api.async_discharge(power, soc_limit, max_discharge)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send discharge command - device may be offline: {e}")
            raise

    async def stop(call: ServiceCall):
        """Stop charging/discharging."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        try:
            await coord.api.async_stop()
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send stop command - device may be offline: {e}")
            raise

    # --- Working Mode Services ---
    async def set_self_consumption_mode(call: ServiceCall):
        """Sets device to Mode 1 (Self-consumed prioritized)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        try:
            await coord.api.async_set_mode(1)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set self-consumption mode - device may be offline: {e}")
            raise

    async def set_schedule_mode(call: ServiceCall):
        """Sets device to Mode 5 (Schedule)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        try:
            await coord.api.async_set_mode(5)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set schedule mode - device may be offline: {e}")
            raise

    async def set_realtime_mode(call: ServiceCall):
        """Sets device to Mode 4 (Real-time control)."""
        device_id = call.data.get("device_id")
        coord = get_coordinator_by_device_id(device_id)
        try:
            await coord.api.async_set_mode(4)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set realtime mode - device may be offline: {e}")
            raise

    # --- Backup SOC Service ---
    async def set_backup_soc(call: ServiceCall):
        """Set Backup SOC (minimum reserve SOC)."""
        device_id = call.data.get("device_id")
        backup_soc = call.data["backup_soc"]

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting Backup SOC to %s%% for device %s",
            backup_soc,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_backup_soc(backup_soc)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set backup SOC - device may be offline: {e}")
            raise

    # --- AC Output Power Service ---
    async def set_ac_output_power(call: ServiceCall):
        """Set AC Output power."""
        device_id = call.data.get("device_id")
        ac_output_power = call.data["ac_output_power"]

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting AC Output power to %s%% for device %s",
            ac_output_power,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_ac_output_power(ac_output_power)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set AC output power - device may be offline: {e}")
            raise

    # --- Feed-In Power Service ---
    async def set_feed_in_power(call: ServiceCall):
        """Set Feed-In power."""
        device_id = call.data.get("device_id")
        feed_in_power = call.data["feed_in_power"]

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting Feed-In power to %s%% for device %s",
            feed_in_power,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_feed_in_power(feed_in_power)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set feed-in power - device may be offline: {e}")
            raise

    # --- Grid Charging Service ---
    async def set_grid_charging(call: ServiceCall):
        """Enable/Disable Grid Charging."""
        device_id = call.data.get("device_id")
        grid_charging_bool = call.data["grid_charging"]
        grid_charging = 1 if grid_charging_bool else 0

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting Grid Charging to %s%% for device %s",
            grid_charging,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_grid_charging(grid_charging)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set grid charging - device may be offline: {e}")
            raise

    # --- Inverter Input Power Service ---
    async def set_inverter_input_power(call: ServiceCall):
        """Set Inverter Input power."""
        device_id = call.data.get("device_id")
        inverter_input_power = call.data["inverter_input_power"]

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting Inverter Input power to %s%% for device %s",
            inverter_input_power,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_inverter_input_power(inverter_input_power)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set inverter input power - device may be offline: {e}")
            raise

    # --- Bypass Socket Service ---
    async def set_bypass_socket(call: ServiceCall):
        """Enable/Disable Bypass Socket."""
        device_id = call.data.get("device_id")
        bypass_socket_bool = call.data["bypass_socket"]
        bypass_socket = 1 if bypass_socket_bool else 0

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting Bypass Socket to %s%% for device %s",
            bypass_socket,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_bypass_socket(bypass_socket)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set bypass socket - device may be offline: {e}")
            raise

    # --- LED Light Service ---
    async def set_led_light(call: ServiceCall):
        """Enable/Disable LED Light."""
        device_id = call.data.get("device_id")
        led_light_bool = call.data["led_light"]
        led_light = 1 if led_light_bool else 0

        coord = get_coordinator_by_device_id(device_id)

        _LOGGER.info(
            "Setting LED Ligt to %s%% for device %s",
            led_light,
            coord.config_entry.entry_id,
        )

        try:
            await coord.api.async_set_led_light(led_light)
        except ConnectionError as e:
            _LOGGER.error(f"Failed to set LED light - device may be offline: {e}")
            raise

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
        try:
            await main_coord.api.async_charge(power, soc_limit, max_charge)
            _LOGGER.info("Cluster charge command sent to main device")
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send cluster charge command - device may be offline: {e}")
            raise

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
        try:
            await main_coord.api.async_discharge(power, soc_limit, max_discharge)
            _LOGGER.info("Cluster discharge command sent to main device")
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send cluster discharge command - device may be offline: {e}")
            raise

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
        
        try:
            await main_coord.api.async_stop()
            _LOGGER.info("Cluster stop command sent to main device")
        except ConnectionError as e:
            _LOGGER.error(f"Failed to send cluster stop command - device may be offline: {e}")
            raise

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
    
    backup_soc_schema = device_schema.extend({
        vol.Required("backup_soc"): vol.All(vol.Coerce(int), vol.Range(min=5, max=100)),
    })

    ac_output_power_schema = device_schema.extend({
        vol.Required("ac_output_power", default=800): vol.All(vol.Coerce(int), vol.Range(min=0, max=2400)),
    })

    feed_in_power_schema = device_schema.extend({
        vol.Required("feed_in_power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2400)),
    })

    grid_charging_schema = device_schema.extend({
        vol.Required("grid_charging"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
    })

    inverter_input_power_schema = device_schema.extend({
        vol.Required("inverter_input_power"): vol.All(vol.Coerce(int), vol.Range(min=0, max=2400)),
    })

    bypass_socket_schema = device_schema.extend({
        vol.Required("bypass_socket"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
    })

    led_light_schema = device_schema.extend({
        vol.Required("led_light"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
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
    
    hass.services.async_register(DOMAIN, "set_backup_soc",set_backup_soc, schema=backup_soc_schema)
    hass.services.async_register(DOMAIN, "set_ac_output_power",set_ac_output_power, schema=ac_output_power_schema)
    hass.services.async_register(DOMAIN, "set_feed_in_power",set_feed_in_power, schema=feed_in_power_schema)
    hass.services.async_register(DOMAIN, "set_grid_charging",set_grid_charging, schema=grid_charging_schema)
    hass.services.async_register(DOMAIN, "set_inverter_input_power",set_inverter_input_power, schema=inverter_input_power_schema)
    hass.services.async_register(DOMAIN, "set_bypass_socket",set_bypass_socket, schema=bypass_socket_schema)
    hass.services.async_register(DOMAIN, "set_led_light",set_led_light, schema=led_light_schema)
    
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
            hass.services.async_remove(DOMAIN, "set_backup_soc")
            hass.services.async_remove(DOMAIN, "set_ac_output_power")
            hass.services.async_remove(DOMAIN, "set_feed_in_power")
            hass.services.async_remove(DOMAIN, "set_grid_charging")
            hass.services.async_remove(DOMAIN, "set_inverter_input_power")
            hass.services.async_remove(DOMAIN, "set_bypass_socket")
            hass.services.async_remove(DOMAIN, "set_led_light")

            hass.services.async_remove(DOMAIN, "cluster_charge")
            hass.services.async_remove(DOMAIN, "cluster_discharge")
            hass.services.async_remove(DOMAIN, "cluster_stop")
    
    return unload_ok
