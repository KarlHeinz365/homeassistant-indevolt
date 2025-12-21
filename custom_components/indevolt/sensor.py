from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Final

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass, 
    SensorEntityDescription, 
    SensorStateClass
)
# CRITICAL FIX: Added CoordinatorEntity import
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfEnergy, UnitOfPower, PERCENTAGE

from .utils import get_device_gen
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)

# ... (Include your SENSORS_GEN1 and SENSORS_GEN2 lists here exactly as before)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    gen = get_device_gen(entry.data.get("device_model"))
    
    # Logic fix: select ONLY the relevant sensor list to prevent doubling
    description_list = SENSORS_GEN1 if gen == 1 else SENSORS_GEN2
    
    entities = [
        IndevoltSensorEntity(coordinator, description) 
        for description in description_list
    ]
    async_add_entities(entities)

class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None
        self._last_update_date = None
        
        sn = coordinator.config_entry.data.get("sn", "unknown")
        model = coordinator.config_entry.data.get("device_model", "unknown")
        self._attr_unique_id = f"{DOMAIN}_{sn}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"INDEVOLT {model}",
            manufacturer="INDEVOLT",
            serial_number=sn,
            model=model,
        )

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None:
            return self._last_valid_value
            
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()

        # Daily Reset Safeguard
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            if self._last_update_date and current_date > self._last_update_date:
                self._last_valid_value = new_value
                self._last_update_date = current_date
                return new_value
            
            if self._last_valid_value is not None and new_value < (self._last_valid_value - 0.1):
                return self._last_valid_value
            
            self._last_valid_value = new_value
            self._last_update_date = current_date
            
        return new_value
