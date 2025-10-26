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


SENSORS_GEN1: Final = (
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2108",
        name="Total AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1505",
        name="Cumulative Production",
        coefficient=0.001,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6002",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6105",
        name="Emergency Power Supply",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6004",
        name="Battery Daily Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6005",
        name="Battery Daily Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6006",
        name="Battery Total Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6007",
        name="Battery Total Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="21028",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="7101",
        name="Working Mode",
        state_mapping={
            0: "Outdoor Portable",
            1: "Self-consumed Prioritized",
            5: "Charge/Discharge Schedule"
        },
        device_class=SensorDeviceClass.ENUM
    ),
    IndevoltSensorEntityDescription(
        key="6001",
        name="Battery Charge/Discharge State",
        state_mapping={
            1000: "Static",
            1001: "Charging",
            1002: "Discharging"
        },
        device_class=SensorDeviceClass.ENUM
    ),
    IndevoltSensorEntityDescription(
        key="7120",
        name="Meter Connection Status",
        state_mapping={
            1000: "ON",
            1001: "OFF"
        },
        device_class=SensorDeviceClass.ENUM
    ),
)

SENSORS_GEN2: Final = (
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1666",
        name="DC Input Power3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1667",
        name="DC Input Power4",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2108",
        name="Total AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1505",
        name="Cumulative Production",
        coefficient=0.001,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="142",
        name="Rated Capacity",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL # This sensor can change, so TOTAL is correct, not TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6009",
        name="Battery SOC Main Unit",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6002",
        name="Total Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6105",
        name="Emergency Power Supply",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6004",
        name="Battery Daily Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6005",
        name="Battery Daily Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6006",
        name="Battery Total Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6007",
        name="Battery Total Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="11016",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="7101",
        name="Working Mode",
        state_mapping={
            1: "Self-consumed Prioritized",
            5: "Charge/Discharge Schedule"
        },
        device_class=SensorDeviceClass.ENUM
    ),
    IndevoltSensorEntityDescription(
        key="6001",
        name="Battery Charge/Discharge State",
        state_mapping={
            1000: "Static",
            1001: "Charging",
            1002: "Discharging"
        },
        device_class=SensorDeviceClass.ENUM
    ),
    IndevoltSensorEntityDescription(
        key="7120",
        name="Meter Connection Status",
        state_mapping={
            1000: "ON",
            1001: "OFF"
        },
        device_class=SensorDeviceClass.ENUM
    ),
    IndevoltSensorEntityDescription(
        key="667",
        name="Bypass Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform for Indevolt."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Create entities based on device generation
    if get_device_gen(coordinator.config_entry.data.get("device_model")) == 1:
        for description in SENSORS_GEN1:
            entities.append(IndevoltSensorEntity(
                coordinator=coordinator, 
                description=description
            ))
    else:
        for description in SENSORS_GEN2:
            entities.append(IndevoltSensorEntity(
                coordinator=coordinator, 
                description=description
            ))
    
    async_add_entities(entities)


class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Represents a sensor entity for Indevolt devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None  # Track last known good value

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
        
        # Restore last known value for energy counters
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            last_state = await self.async_get_last_state()
            if last_state and last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._last_valid_value = float(last_state.state)
                    _LOGGER.debug(
                        "Restored last value for %s: %s",
                        self.entity_id, self._last_valid_value
                    )
                except (ValueError, TypeError):
                    _LOGGER.debug(
                        "Could not restore last state for %s",
                        self.entity_id
                    )

    @property
    def native_value(self):
        """Return the current value of the sensor in its native unit."""    
        raw_value = self.coordinator.data.get(self.entity_description.key)
        
        # Handle ENUM sensors
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            if raw_value is None:
                return None
            return self.entity_description.state_mapping.get(raw_value)
        
        # Handle None values (device offline or communication error)
        if raw_value is None:
            # For energy counters, return last known value instead of None
            # This prevents gaps in energy dashboard
            if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
                _LOGGER.debug(
                    "%s received None, returning last valid value: %s",
                    self.entity_id, self._last_valid_value
                )
                return self._last_valid_value
            return None
        
        # Calculate new value with coefficient
        new_value = raw_value * self.entity_description.coefficient
        
        # Special handling for TOTAL_INCREASING sensors (energy counters)
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            # Detect counter resets (new value significantly less than last value)
            if self._last_valid_value is not None:
                # Allow small decreases (rounding errors), but catch real resets
                if new_value < (self._last_valid_value - 0.1):
                    _LOGGER.warning(
                        "%s detected counter reset. New: %s, Last: %s. "
                        "Keeping last value to maintain energy dashboard continuity.",
                        self.entity_id, new_value, self._last_valid_value
                    )
                    # Keep the old value to prevent energy dashboard from breaking
                    return self._last_valid_value
            
            # Update last valid value for next comparison
            self._last_valid_value = new_value
        
        return new_value
