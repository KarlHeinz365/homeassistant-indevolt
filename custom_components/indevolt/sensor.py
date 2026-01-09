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
    # Device Info
    IndevoltSensorEntityDescription(
        key="0", 
        name="Serial Number", 
        icon="mdi:identifier"
    ),
    
    # Working Mode
    IndevoltSensorEntityDescription(
        key="7101", 
        name="Working Mode", 
        state_mapping={
            0: "Outdoor Portable", 
            1: "Self-consumed Prioritized", 
            2: "Charge/Discharge Schedule", 
            4: "Real-time Control", 
            5: "Charge/Discharge Schedule"
        }, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:cog"
    ),
    
    # DC Input (Solar)
    IndevoltSensorEntityDescription(
        key="1664", 
        name="DC Input Power 1", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    IndevoltSensorEntityDescription(
        key="1665", 
        name="DC Input Power 2", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    
    # AC Power
    IndevoltSensorEntityDescription(
        key="2108", 
        name="Total AC Output Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:power-plug"
    ),
    IndevoltSensorEntityDescription(
        key="2101", 
        name="Total AC Input Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower"
    ),
    
    # Energy Production
    IndevoltSensorEntityDescription(
        key="1502", 
        name="Daily Production", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-panel"
    ),
    IndevoltSensorEntityDescription(
        key="1505", 
        name="Cumulative Production", 
        coefficient=0.001, 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-panel"
    ),
    IndevoltSensorEntityDescription(
        key="2107", 
        name="Total AC Input Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower"
    ),
    
    # DC Output
    IndevoltSensorEntityDescription(
        key="1501", 
        name="Total DC Output Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt"
    ),
    
    # Battery
    IndevoltSensorEntityDescription(
        key="6000", 
        name="Battery Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="6001", 
        name="Battery State", 
        state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:battery-charging"
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
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-alert"
    ),
    IndevoltSensorEntityDescription(
        key="6004", 
        name="Battery Daily Charging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging"
    ),
    IndevoltSensorEntityDescription(
        key="6005", 
        name="Battery Daily Discharging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus"
    ),
    IndevoltSensorEntityDescription(
        key="6006", 
        name="Battery Total Charging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging"
    ),
    IndevoltSensorEntityDescription(
        key="6007", 
        name="Battery Total Discharging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus"
    ),
    
    # Meter
    IndevoltSensorEntityDescription(
        key="7120", 
        name="Meter Connection Status", 
        state_mapping={1000: "Enable", 1001: "Disable"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:electric-switch"
    ),
    IndevoltSensorEntityDescription(
        key="21028", 
        name="Meter Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:meter-electric"
    ),
)

# ==================== GEN 2: SolidFlex/PowerFlex2000 ====================
SENSORS_GEN2: Final = (
    # Device Info
    IndevoltSensorEntityDescription(
        key="0", 
        name="Serial Number", 
        icon="mdi:identifier"
    ),
    
    # Firmware Versions
    IndevoltSensorEntityDescription(
        key="1118", 
        name="Firmware EMS", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1109", 
        name="Firmware BMS-MB", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1119", 
        name="Firmware PCS", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1120", 
        name="Firmware DCDC", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1136", 
        name="Firmware DCDC1", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1137", 
        name="Firmware BMS1", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1138", 
        name="Firmware DCDC2", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1139", 
        name="Firmware BMS2", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1140", 
        name="Firmware DCDC3", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1141", 
        name="Firmware BMS3", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1142", 
        name="Firmware DCDC4", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1143", 
        name="Firmware BMS4", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1098", 
        name="Firmware DCDC5", 
        icon="mdi:chip"
    ),
    IndevoltSensorEntityDescription(
        key="1099", 
        name="Firmware BMS5", 
        icon="mdi:chip"
    ),
    
    # System Operating
    IndevoltSensorEntityDescription(
        key="7101", 
        name="Working Mode", 
        state_mapping={
            1: "Self-consumed Prioritized", 
            2: "Charge/Discharge Schedule", 
            4: "Real-time Control", 
            5: "Charge/Discharge Schedule"
        }, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:cog"
    ),
    IndevoltSensorEntityDescription(
        key="142", 
        name="Rated Capacity", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="6105", 
        name="Emergency Power Supply", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-alert"
    ),
    IndevoltSensorEntityDescription(
        key="2618", 
        name="Grid Charging", 
        state_mapping={1000: "Disable", 1001: "Enable"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:transmission-tower"
    ),
    IndevoltSensorEntityDescription(
        key="11009", 
        name="Inverter Input Limit", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge"
    ),
    IndevoltSensorEntityDescription(
        key="2101", 
        name="Total AC Input Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower"
    ),
    IndevoltSensorEntityDescription(
        key="2108", 
        name="Total AC Output Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:power-plug"
    ),
    IndevoltSensorEntityDescription(
        key="11010", 
        name="Feed-in Power Limit", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge"
    ),
    
    # Bypass Power
    IndevoltSensorEntityDescription(
        key="667", 
        name="Bypass Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:electric-switch"
    ),
    
    # Energy Information
    IndevoltSensorEntityDescription(
        key="2107", 
        name="Total AC Output Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt"
    ),
    IndevoltSensorEntityDescription(
        key="2104", 
        name="Total AC Input Energy", 
        coefficient=0.001,  # Wh to kWh
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower"
    ),
    IndevoltSensorEntityDescription(
        key="2105", 
        name="Off-grid Output Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:power-plug-off"
    ),
    IndevoltSensorEntityDescription(
        key="11034", 
        name="Bypass Input Energy", 
        coefficient=0.001,  # Wh to kWh
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:electric-switch"
    ),
    IndevoltSensorEntityDescription(
        key="1502", 
        name="Daily PV Generation", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-panel"
    ),
    IndevoltSensorEntityDescription(
        key="6004", 
        name="Battery Daily Charging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging"
    ),
    IndevoltSensorEntityDescription(
        key="6005", 
        name="Battery Daily Discharging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus"
    ),
    IndevoltSensorEntityDescription(
        key="6006", 
        name="Battery Total Charging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging"
    ),
    IndevoltSensorEntityDescription(
        key="6007", 
        name="Battery Total Discharging Energy", 
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, 
        device_class=SensorDeviceClass.ENERGY, 
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus"
    ),
    
    # Meter Status
    IndevoltSensorEntityDescription(
        key="7120", 
        name="Meter Connection Status", 
        state_mapping={1000: "Enable", 1001: "Disable"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:electric-switch"
    ),
    IndevoltSensorEntityDescription(
        key="11016", 
        name="Meter Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:meter-electric"
    ),
    
    # Grid Information
    IndevoltSensorEntityDescription(
        key="2600", 
        name="Grid Voltage", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="2612", 
        name="Grid Frequency", 
        native_unit_of_measurement=UnitOfFrequency.HERTZ, 
        device_class=SensorDeviceClass.FREQUENCY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave"
    ),
    
    # Battery Pack Operating Parameters
    IndevoltSensorEntityDescription(
        key="6001", 
        name="Battery State", 
        state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, 
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:battery-charging"
    ),
    IndevoltSensorEntityDescription(
        key="6000", 
        name="Battery Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="6002", 
        name="Total Battery SOC", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT
    ),
    
    # Main Battery (MB)
    IndevoltSensorEntityDescription(
        key="9008", 
        name="Battery SN Main", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9000", 
        name="Battery SOC Main", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9004", 
        name="Battery Voltage Main", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="9013", 
        name="Battery Current Main", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9012", 
        name="Battery Temperature Main", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # Slave Battery 1
    IndevoltSensorEntityDescription(
        key="9032", 
        name="Battery SN Slave 1", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9016", 
        name="Battery SOC Slave 1", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9020", 
        name="Battery Voltage Slave 1", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="19173", 
        name="Battery Current Slave 1", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9030", 
        name="Battery Temperature Slave 1", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # Slave Battery 2
    IndevoltSensorEntityDescription(
        key="9051", 
        name="Battery SN Slave 2", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9035", 
        name="Battery SOC Slave 2", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9039", 
        name="Battery Voltage Slave 2", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="19174", 
        name="Battery Current Slave 2", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9049", 
        name="Battery Temperature Slave 2", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # Slave Battery 3
    IndevoltSensorEntityDescription(
        key="9070", 
        name="Battery SN Slave 3", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9054", 
        name="Battery SOC Slave 3", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9058", 
        name="Battery Voltage Slave 3", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="19175", 
        name="Battery Current Slave 3", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9068", 
        name="Battery Temperature Slave 3", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # Slave Battery 4
    IndevoltSensorEntityDescription(
        key="9165", 
        name="Battery SN Slave 4", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9149", 
        name="Battery SOC Slave 4", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9153", 
        name="Battery Voltage Slave 4", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="19176", 
        name="Battery Current Slave 4", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9163", 
        name="Battery Temperature Slave 4", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # Slave Battery 5
    IndevoltSensorEntityDescription(
        key="9218", 
        name="Battery SN Slave 5", 
        icon="mdi:identifier"
    ),
    IndevoltSensorEntityDescription(
        key="9202", 
        name="Battery SOC Slave 5", 
        native_unit_of_measurement=PERCENTAGE, 
        device_class=SensorDeviceClass.BATTERY, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery"
    ),
    IndevoltSensorEntityDescription(
        key="9206", 
        name="Battery Voltage Slave 5", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="19177", 
        name="Battery Current Slave 5", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="9216", 
        name="Battery Temperature Slave 5", 
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, 
        device_class=SensorDeviceClass.TEMPERATURE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer"
    ),
    
    # PV Operating Parameters
    IndevoltSensorEntityDescription(
        key="1501", 
        name="Total DC Output Power", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    
    # PV String 1
    IndevoltSensorEntityDescription(
        key="1632", 
        name="DC Input Current 1", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="1600", 
        name="DC Input Voltage 1", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="1664", 
        name="DC Input Power 1", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    
    # PV String 2
    IndevoltSensorEntityDescription(
        key="1633", 
        name="DC Input Current 2", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="1601", 
        name="DC Input Voltage 2", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="1665", 
        name="DC Input Power 2", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    
    # PV String 3
    IndevoltSensorEntityDescription(
        key="1634", 
        name="DC Input Current 3", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="1602", 
        name="DC Input Voltage 3", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="1666", 
        name="DC Input Power 3", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
    
    # PV String 4
    IndevoltSensorEntityDescription(
        key="1634", 
        name="DC Input Current 4", 
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, 
        device_class=SensorDeviceClass.CURRENT, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc"
    ),
    IndevoltSensorEntityDescription(
        key="1603", 
        name="DC Input Voltage 4", 
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, 
        device_class=SensorDeviceClass.VOLTAGE, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash"
    ),
    IndevoltSensorEntityDescription(
        key="1667", 
        name="DC Input Power 4", 
        native_unit_of_measurement=UnitOfPower.WATT, 
        device_class=SensorDeviceClass.POWER, 
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power"
    ),
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
        self._attr_unique_id = f"{DOMAIN}_{sn}_{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.config_entry.entry_id)}, name=f"INDEVOLT {sn}")

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        
        # Handle ENUM types
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            return self.entity_description.state_mapping.get(raw_value) if raw_value is not None else None
        
        # Handle string values (SN, firmware versions)
        if isinstance(raw_value, str):
            return raw_value
        
        # Handle None values
        if raw_value is None:
            return self._last_valid_value if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING else None
        
        # Apply coefficient
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()
        
        # Handle TOTAL_INCREASING with daily reset detection
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            if self._last_valid_value is not None:
                if current_date == self._last_update_date:
                    if new_value < (self._last_valid_value - 0.1):
                        return self._last_valid_value
                else:
                    _LOGGER.info("Accepting daily reset for %s", self.entity_id)
            self._last_valid_value = new_value
            self._last_update_date = current_date
        
        return new_value