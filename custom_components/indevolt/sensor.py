from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Final
from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorEntityDescription, SensorStateClass
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.const import (
    UnitOfEnergy, UnitOfPower, UnitOfElectricPotential, 
    UnitOfElectricCurrent, UnitOfTemperature, UnitOfFrequency, PERCENTAGE
)
from .utils import get_device_gen
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)

# ==================== GEN 1: BK1600/BK1600Ultra ====================
SENSORS_GEN1: Final = (
    IndevoltSensorEntityDescription(key="0", name="Serial Number", icon="mdi:identifier"),
    IndevoltSensorEntityDescription(
        key="7101", 
        name="Working Mode", 
        state_mapping={0: "Outdoor", 1: "Self-consumption", 2: "Schedule", 4: "Real-time", 5: "Schedule"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:cog"
    ),
    IndevoltSensorEntityDescription(key="1664", name="DC Input Power 1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1665", name="DC Input Power 2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2108", name="Total AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2101", name="Total AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1502", name="Daily Production", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6000", name="Battery Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6001", name="Battery State", state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="6002", name="Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6004", name="Battery Daily Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6005", name="Battery Daily Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
)

# Note: SENSORS_GEN2 would follow the same pattern as SENSORS_GEN1 but with keys from original sensor.py

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    gen = get_device_gen(coordinator.config_entry.data.get("device_model"))
    sensor_list = SENSORS_GEN1 if gen == 1 else SENSORS_GEN2 # SENSORS_GEN2 defined in original file
    async_add_entities([IndevoltSensorEntity(coordinator, d) for d in sensor_list])

class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None
        self._last_update_date = dt_util.now().date()
        sn = coordinator.config_entry.data.get("sn", "unknown")
        self._attr_unique_id = f"{DOMAIN}_{sn}_{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.config_entry.entry_id)}, name=f"INDEVOLT {sn}")

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        use_filter = self.coordinator.config_entry.options.get("enable_safety_filter", True)

        # 1. Handle Enums/Strings
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            return self.entity_description.state_mapping.get(raw_value)
        if isinstance(raw_value, str):
            return raw_value

        # 2. Safety Filter for Missing Data
        if raw_value is None:
            if use_filter and self._last_valid_value is not None:
                return self._last_valid_value
            return None

        # 3. Apply Scaling
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()

        # 4. Smart Logic for Energy Sensors (TOTAL_INCREASING)
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            if use_filter and self._last_valid_value is not None:
                # Check if same day but massive drop (likely broken data)
                if current_date == self._last_update_date:
                    if new_value < (self._last_valid_value * 0.1) and self._last_valid_value > 0.5:
                        _LOGGER.debug("Safety Filter blocked suspicious drop for %s", self.entity_id)
                        return self._last_valid_value
                else:
                    _LOGGER.info("Date change detected for %s: Resetting for new day", self.entity_id)
            
            self._last_valid_value = new_value
            self._last_update_date = current_date

        return new_value
