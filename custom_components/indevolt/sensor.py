from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass, 
    SensorEntityDescription, 
    SensorStateClass
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from .utils import get_device_gen
from .const import DOMAIN
from dataclasses import dataclass, field
from typing import Final
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    PERCENTAGE
)
import logging

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    """Custom entity description class for Indevolt sensors."""
    name: str = ""
    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)
    translation_key: str | None = None
    entity_category: EntityCategory | None = None

# (Keep your SENSORS_GEN1 and SENSORS_GEN2 definitions exactly as they were)
SENSORS_GEN1: Final = ( ... )
SENSORS_GEN2: Final = ( ... )

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform for Indevolt."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    if get_device_gen(coordinator.config_entry.data.get("device_model")) == 1:
        for description in SENSORS_GEN1:
            entities.append(IndevoltSensorEntity(coordinator=coordinator, description=description))
    else:
        for description in SENSORS_GEN2:
            entities.append(IndevoltSensorEntity(coordinator=coordinator, description=description))
    async_add_entities(entities)

class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Represents a sensor entity for Indevolt devices."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None
        self._last_update_date = dt_util.now().date() # Track the date of the last successful value

        sn = coordinator.config_entry.data.get("sn", "unknown")
        model = coordinator.config_entry.data.get("device_model", "unknown")
        self._attr_unique_id = f"{DOMAIN}_{sn}_{coordinator.config_entry.entry_id}_{description.key}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="INDEVOLT",
            name=f"INDEVOLT {model}",
            serial_number=sn,
            model=model,
            sw_version=coordinator.config_entry.data.get("fw_version", "unknown"),
        )
        
        if description.device_class == SensorDeviceClass.ENUM:
            self._attr_options = list(set(description.state_mapping.values()))

    async def async_added_to_hass(self):
        """Restore last state for TOTAL_INCREASING sensors."""
        await super().async_added_to_hass()
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            last_state = await self.async_get_last_state()
            if last_state and last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._last_valid_value = float(last_state.state)
                except (ValueError, TypeError):
                    pass

    @property
    def native_value(self):
        """Return the current value with safeguards for daily resets."""    
        raw_value = self.coordinator.data.get(self.entity_description.key)
        
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            if raw_value is None: return None
            return self.entity_description.state_mapping.get(raw_value)
        
        if raw_value is None:
            if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
                return self._last_valid_value
            return None
        
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()
        
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            if self._last_valid_value is not None:
                # If value decreases significantly...
                if new_value < (self._last_valid_value - 0.1):
                    # Only accept the decrease if the date has changed (Midnight reset)
                    if current_date > self._last_update_date:
                        _LOGGER.debug("%s: Accepting daily reset for new date.", self.entity_id)
                    else:
                        # Block the decrease during the same day (Communication glitch)
                        _LOGGER.warning("%s: Prevented intraday reset. New: %s, Last: %s.", 
                                       self.entity_id, new_value, self._last_valid_value)
                        return self._last_valid_value
            
            self._last_valid_value = new_value
            self._last_update_date = current_date
        
        return new_value
