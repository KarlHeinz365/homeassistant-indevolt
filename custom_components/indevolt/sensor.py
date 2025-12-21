from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Final
from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .utils import get_device_gen

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)

# FULL SENSOR LISTS - COPIED FROM YOUR ORIGINAL FILES
SENSORS_GEN1: Final = (
    IndevoltSensorEntityDescription(key="1664", name="DC Input Power1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1665", name="DC Input Power2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2108", name="Total AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1502", name="Daily Production", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="1505", name="Cumulative Production", coefficient=0.001, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="2101", name="Total AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2107", name="Total AC Input Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="1501", name="Total DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6000", name="Battery Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6002", name="Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6105", name="Emergency Power Supply", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6004", name="Battery Daily Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6005", name="Battery Daily Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6006", name="Battery Total Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6007", name="Battery Total Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="21028", name="Meter Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="7101", name="Working Mode", state_mapping={0: "Outdoor Portable", 1: "Self-consumed Prioritized", 5: "Charge/Discharge Schedule"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="6001", name="Battery Charge/Discharge State", state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7120", name="Meter Connection Status", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
)

SENSORS_GEN2: Final = (
    IndevoltSensorEntityDescription(key="1664", name="DC Input Power1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1665", name="DC Input Power2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1666", name="DC Input Power3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1667", name="DC Input Power4", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1501", name="Total DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2108", name="Total AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1502", name="Daily Production", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="1505", name="Cumulative Production", coefficient=0.001, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="2101", name="Total AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2107", name="Total AC Input Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="142", name="Rated Capacity", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL),
    IndevoltSensorEntityDescription(key="6000", name="Battery Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6002", name="Total Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6105", name="Emergency Power Supply", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6004", name="Battery Daily Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6005", name="Battery Daily Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6006", name="Battery Total Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6007", name="Battery Total Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="11016", name="Meter Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="7101", name="Working Mode", state_mapping={1: "Self-consumed Prioritized", 5: "Charge/Discharge Schedule"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="6001", name="Battery Charge/Discharge State", state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7120", name="Meter Connection Status", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="667", name="Bypass Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    gen = get_device_gen(coordinator.config_entry.data.get("device_model"))
    sensor_list = SENSORS_GEN1 if gen == 1 else SENSORS_GEN2
    async_add_entities([IndevoltSensorEntity(coordinator, d) for d in sensor_list])

class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None
        self._last_update_date = dt_util.now().date()
        sn = coordinator.config_entry.data.get("sn", "unknown")
        model = coordinator.config_entry.data.get("device_model", "unknown")
        self._attr_unique_id = f"{DOMAIN}_{sn}_{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.config_entry.entry_id)}, manufacturer="INDEVOLT", name=f"INDEVOLT {model}", serial_number=sn, model=model)

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            return self.entity_description.state_mapping.get(raw_value) if raw_value is not None else None
        
        if raw_value is None:
            return self._last_valid_value if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING else None

        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()

        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            if self._last_valid_value is not None:
                # Midnight reset logic
                if current_date > self._last_update_date:
                    _LOGGER.debug("%s: New day allowed reset.", self.entity_id)
                elif new_value < (self._last_valid_value - 0.1):
                    _LOGGER.warning("%s: Blocked glitch reset.", self.entity_id)
                    return self._last_valid_value
            self._last_valid_value = new_value
            self._last_update_date = current_date
        return new_value
