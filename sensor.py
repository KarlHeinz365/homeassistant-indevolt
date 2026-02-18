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
from homeassistant.const import UnitOfEnergy, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, UnitOfTemperature, PERCENTAGE, UnitOfFrequency, UnitOfApparentPower
from .utils import get_device_gen
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)
    is_string: bool = False  # New field to indicate string-type registers

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
    
    # Working Mode: Merged your descriptions with the extra codes (2 & 4) to prevent "Unknown" errors
    IndevoltSensorEntityDescription(key="7101", name="Working Mode", state_mapping={
        0: "Outdoor Portable", 
        1: "Self-consumed Prioritized", 
        2: "Charge/Discharge Schedule", 
        4: "Real-time Control", 
        5: "Charge/Discharge Schedule"
    }, device_class=SensorDeviceClass.ENUM),
    
    IndevoltSensorEntityDescription(key="6001", name="Battery Charge/Discharge State", state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7120", name="Meter Connection Status", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
)

SENSORS_GEN2: Final = (
    IndevoltSensorEntityDescription(key="4", name="Rated Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="114", name="Maximum Charging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="142", name="Rated Capacity", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL),
    IndevoltSensorEntityDescription(key="614", name="Maximum System Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="667", name="Bypass Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1664", name="DC Input Power1", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1600", name="DC Input Voltage1", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1632", name="DC Input Current1", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1665", name="DC Input Power2", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1601", name="DC Input Voltage2", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1633", name="DC Input Current2", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="1666", name="DC Input Power3", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1602", name="DC Input Voltage3", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1634", name="DC Input Current3", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),        
    IndevoltSensorEntityDescription(key="1667", name="DC Input Power4", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1603", name="DC Input Voltage4", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1635", name="DC Input Current4", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    IndevoltSensorEntityDescription(key="1501", name="Total DC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="1502", name="Daily Production", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="1505", name="Cumulative Production", coefficient=0.001, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="2083", name="Inverter Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2095", name="Inverter Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2098", name="Total AC Apparent Power", native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="2099", name="AC Power Factor", device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="2108", name="Total AC Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="2101", name="Total AC Input Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2102", name="Grid Export Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2103", name="Off-Grid Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="2104", name="Cumulative Grid Export Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),    
    IndevoltSensorEntityDescription(key="2105", name="Cumulative Off-Grid Output Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),    
    #No data: IndevoltSensorEntityDescription(key="2106", name="Total AC Output Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="2107", name="Total AC Input Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    #No data: IndevoltSensorEntityDescription(key="2263", name="Daily AC Output Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),    
    #No data: IndevoltSensorEntityDescription(key="2264", name="Daily Grid Export Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),    
    #No data: IndevoltSensorEntityDescription(key="2265", name="Daily Off-Grid Output Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),        
    IndevoltSensorEntityDescription(key="2268", name="Total Pv Charging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2275", name="Total Input Power Of Inverter", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),            
    IndevoltSensorEntityDescription(key="2600", name="Input Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="2666", name="Grid Feed-in Power Limit", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),            
    IndevoltSensorEntityDescription(key="2802", name="AC charging power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),                
    IndevoltSensorEntityDescription(key="2612", name="Input Frequency", native_unit_of_measurement=UnitOfFrequency.HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="5010", name="Total Load Output Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="6000", name="Battery Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6004", name="Battery Daily Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6005", name="Battery Daily Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6006", name="Battery Total Charging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6007", name="Battery Total Discharging Energy", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    IndevoltSensorEntityDescription(key="6002", name="Total Battery SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6105", name="Emergency Power Supply", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="6106", name="Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),        
    IndevoltSensorEntityDescription(key="6109", name="Real-Time Charging And Discharging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="7636", name="PV1 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="7637", name="PV2 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="7640", name="PV3 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="7641", name="PV4 Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),    
    
    ### Main Unit Entities / Battery 1
    #IndevoltSensorEntityDescription(key="6009", name="Main Unit SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9002", name="Main Unit SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9004", name="Main Unit Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9005", name="Main Unit Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9007", name="Main Unit Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9009", name="Main Unit Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9010", name="Main Unit Module Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9012", name="Main Unit Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="11040", name="Main Unit Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="11041", name="Main Unit Battery Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="11042", name="Main Unit MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9071", name="Main Unit DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9072", name="Main Unit DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="9073", name="Main Unit DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9074", name="Main Unit DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9075", name="Main Unit DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9076", name="Main Unit DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9077", name="Main Unit DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9078", name="Main Unit DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9081", name="Main Unit Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9082", name="Main Unit Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9013", name="Main Unit Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    
    ### Slave Unit 1 Entities / Battery 2
    #IndevoltSensorEntityDescription(key="9016", name="Slave Unit 1 SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9018", name="Slave Unit 1 SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9020", name="Slave Unit 1 Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9021", name="Slave Unit 1 Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9023", name="Slave Unit 1 Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9084", name="Slave Unit 1 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9025", name="Slave Unit 1 Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9026", name="Slave Unit 1 Maximum Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9028", name="Slave Unit 1 Minimum Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9030", name="Slave Unit 1 Average Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),                
    #IndevoltSensorEntityDescription(key="9083", name="Slave Unit 1 Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9085", name="Slave Unit 1 MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9087", name="Slave Unit 1 DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9088", name="Slave Unit 1 DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="9089", name="Slave Unit 1 DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9090", name="Slave Unit 1 DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9091", name="Slave Unit 1 DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9092", name="Slave Unit 1 DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9093", name="Slave Unit 1 DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9094", name="Slave Unit 1 DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9097", name="Slave Unit 1 Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9098", name="Slave Unit 1 Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="19173", name="Slave Unit 1 Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            

    ### Slave Unit 2 Entities / Battery 3
    #IndevoltSensorEntityDescription(key="9035", name="Slave Unit 2 SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9037", name="Slave Unit 2 SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9039", name="Slave Unit 2 Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9040", name="Slave Unit 2 Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9042", name="Slave Unit 2 Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9100", name="Slave Unit 2 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9044", name="Slave Unit 2 Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9045", name="Slave Unit 2 Maximum Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9047", name="Slave Unit 2 Minimum Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9049", name="Slave Unit 2 Average Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),                
    #IndevoltSensorEntityDescription(key="9099", name="Slave Unit 2 Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9101", name="Slave Unit 2 MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9103", name="Slave Unit 2 DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9104", name="Slave Unit 2 DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="9105", name="Slave Unit 2 DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9106", name="Slave Unit 2 DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9107", name="Slave Unit 2 DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9108", name="Slave Unit 2 DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9109", name="Slave Unit 2 DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9110", name="Slave Unit 2 DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9113", name="Slave Unit 2 Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9114", name="Slave Unit 2 Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="19174", name="Slave Unit 2 Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            

    ### Slave Unit 3 Entities / Battery 4
    #IndevoltSensorEntityDescription(key="9054", name="Slave Unit 3 SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9056", name="Slave Unit 3 SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9058", name="Slave Unit 3 Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9059", name="Slave Unit 3 Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9061", name="Slave Unit 3 Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9116", name="Slave Unit 3 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9063", name="Slave Unit 3 Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9064", name="Slave Unit 3 Maximum Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9066", name="Slave Unit 3 Minimum Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9068", name="Slave Unit 3 Average Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),                
    #IndevoltSensorEntityDescription(key="9115", name="Slave Unit 3 Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9117", name="Slave Unit 3 MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9119", name="Slave Unit 3 DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9120", name="Slave Unit 3 DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="9121", name="Slave Unit 3 DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9122", name="Slave Unit 3 DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9123", name="Slave Unit 3 DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9124", name="Slave Unit 3 DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9125", name="Slave Unit 3 DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9126", name="Slave Unit 3 DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9129", name="Slave Unit 3 Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9130", name="Slave Unit 3 Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="19175", name="Slave Unit 3 Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            

    ### Slave Unit 4 Entities / Battery 5
    #IndevoltSensorEntityDescription(key="9149", name="Slave Unit 4 SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9151", name="Slave Unit 4 SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9153", name="Slave Unit 4 Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9154", name="Slave Unit 4 Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9156", name="Slave Unit 4 Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9132", name="Slave Unit 4 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9158", name="Slave Unit 4 Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9159", name="Slave Unit 4 Maximum Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9161", name="Slave Unit 4 Minimum Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9163", name="Slave Unit 4 Average Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),                
    #IndevoltSensorEntityDescription(key="9131", name="Slave Unit 4 Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9133", name="Slave Unit 4 MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9135", name="Slave Unit 4 DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9136", name="Slave Unit 4 DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="9137", name="Slave Unit 4 DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9138", name="Slave Unit 4 DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9139", name="Slave Unit 4 DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9140", name="Slave Unit 4 DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9141", name="Slave Unit 4 DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9142", name="Slave Unit 4 DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9145", name="Slave Unit 4 Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9146", name="Slave Unit 4 Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="19176", name="Slave Unit 4 Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),                
    
    ### Slave Unit 5 Entities / Battery 6       
    #IndevoltSensorEntityDescription(key="9202", name="Slave Unit 5 SOC", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9204", name="Slave Unit 5 SOH", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9206", name="Slave Unit 5 Overall Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9208", name="Slave Unit 5 Cell 1 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9210", name="Slave Unit 5 Cell 2 Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9216", name="Slave Unit 5 Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9211", name="Slave Unit 5 Average Cell Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9212", name="Slave Unit 5 Maximum Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),        
    #IndevoltSensorEntityDescription(key="9214", name="Slave Unit 5 Minimum Cell Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9216", name="Slave Unit 5 Average Battery Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),                
    #IndevoltSensorEntityDescription(key="9268", name="Slave Unit 5 Monomer Voltage Difference (mV)", native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9270", name="Slave Unit 5 MOS Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9272", name="Slave Unit 5 DCDC Bus Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #No Data: IndevoltSensorEntityDescription(key="9267", name="Slave Unit 5 DCDC Bus Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #No Data: IndevoltSensorEntityDescription(key="xxxx", name="Slave Unit 5 DCDC Bus Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9273", name="Slave Unit 5 DCDC Voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    #IndevoltSensorEntityDescription(key="9274", name="Slave Unit 5 DCDC Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9275", name="Slave Unit 5 DCDC Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="9276", name="Slave Unit 5 DCDC Temperature 1", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9277", name="Slave Unit 5 DCDC Temperature 2", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="9280", name="Slave Unit 5 Electric Heating Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),            
    #IndevoltSensorEntityDescription(key="xxxx", name="Slave Unit 5 Electric Heating Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    #IndevoltSensorEntityDescription(key="19176", name="Slave Unit 5 Battery Current", native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),                    
    
    IndevoltSensorEntityDescription(key="9283", name="Allowed Permitted Maximum Maximum Charging and Discharging Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),        
    IndevoltSensorEntityDescription(key="11005", name="Transformer Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    IndevoltSensorEntityDescription(key="11009", name="Charging Power Setting Value", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),    
    IndevoltSensorEntityDescription(key="11016", name="Meter Power", native_unit_of_measurement=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
    #No data: IndevoltSensorEntityDescription(key="18464", name="AC Energy Input", native_unit_of_measurement=UnitOfEnergy.WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),    
    
    # Working Mode: Merged your descriptions with extra codes
    IndevoltSensorEntityDescription(key="7101", name="Working Mode", state_mapping={
        1: "Self-consumed Prioritized", 
        2: "Charge/Discharge Schedule", 
        4: "Real-time Control", 
        5: "Charge/Discharge Schedule"
    }, device_class=SensorDeviceClass.ENUM),

    IndevoltSensorEntityDescription(key="680", name="Bypass Enable State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    IndevoltSensorEntityDescription(key="2618", name="Grid Charge Enable", state_mapping={1000: "OFF", 1001: "ON"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="6001", name="Battery Charge/Discharge State", state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7120", name="Meter Connection State", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7119", name="PV1 Connection State", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7124", name="PV2 Connection State", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7126", name="PV3 Connection State", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7127", name="PV4 Connection State", state_mapping={1000: "ON", 1001: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="7171", name="LED On-Off Control", state_mapping={1: "ON", 0: "OFF"}, device_class=SensorDeviceClass.ENUM),
    IndevoltSensorEntityDescription(key="8100", name="Alert 1", device_class=SensorDeviceClass.ENUM),    
    IndevoltSensorEntityDescription(key="8101", name="Alert 2", device_class=SensorDeviceClass.ENUM),        
    IndevoltSensorEntityDescription(key="11006", name="Operating State", state_mapping={8: "STANDBY", 9:"ON_GRID_CHARGE", 10: "ON_GRID_DISCHARGE", 14: "ON_GRID_DEEP_SLEEP", 13: "BATTERY_CHARGING", 16: "OFF_GRID_DEEP_SLEEP"}, device_class=SensorDeviceClass.ENUM),     
    
    ### Main Unit Entities (ENUM) / Battery 1
    IndevoltSensorEntityDescription(key="9079", name="Main Unit DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    IndevoltSensorEntityDescription(key="9079", name="Main Unit Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    IndevoltSensorEntityDescription(key="11043", name="Main Unit BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),        
    
    ### Slave Unit 1 Entities (ENUM) / Battery 2
    #IndevoltSensorEntityDescription(key="9095", name="Slave Unit 1 DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9096", name="Slave Unit 1 Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9086", name="Slave Unit 1 BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),            
    
    ### Slave Unit 2 Entities (ENUM) / Battery 3
    #IndevoltSensorEntityDescription(key="9111", name="Slave Unit 2 DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9112", name="Slave Unit 2 Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9102", name="Slave Unit 2 BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),                
    
    ### Slave Unit 3 Entities (ENUM) / Battery 4
    #IndevoltSensorEntityDescription(key="9127", name="Slave Unit 3 DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9128", name="Slave Unit 3 Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9118", name="Slave Unit 3 BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),                    
    
    ### Slave Unit 4 Entities (ENUM) / Battery 5
    #IndevoltSensorEntityDescription(key="9143", name="Slave Unit 4 DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9144", name="Slave Unit 4 Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9134", name="Slave Unit 4 BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),                    
    
    ### Slave Unit 5 Entities (ENUM) / Battery 6
    #IndevoltSensorEntityDescription(key="9278", name="Slave Unit 5 DCDC State", state_mapping={0: "STANDBY", 1: "CHARGE", 2: "DISCHARGE"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9279", name="Slave Unit 5 Electric Heating State", state_mapping={0: "OFF", 1: "ON"}, device_class=SensorDeviceClass.ENUM),    
    #IndevoltSensorEntityDescription(key="9271", name="Slave Unit 5 BMS Charging And Discharging Mos State", state_mapping={0: "OPEN", 1: "CLOSE"}, device_class=SensorDeviceClass.ENUM),                    
    
    # String-type sensors (e.g., firmware version, serial numbers, etc.)
    #IndevoltSensorEntityDescription(key="632", name="System Standby Time", is_string=True),    
    IndevoltSensorEntityDescription(key="1118", name="EMS Version", is_string=True),
    IndevoltSensorEntityDescription(key="1119", name="PCS Version", is_string=True),
    IndevoltSensorEntityDescription(key="1127", name="MODBUS Version", is_string=True),
    
    ### Main Unit Entities (STRING) / Battery 1
    IndevoltSensorEntityDescription(key="1120", name="DCDC Version Main Unit", is_string=True),
    IndevoltSensorEntityDescription(key="1109", name="BMS Version Main Unit", is_string=True),    
    IndevoltSensorEntityDescription(key="150", name="SN Battery Main Unit", is_string=True),
    
    ### Slave Unit 1 Entities (STRING) / Battery 2
    #IndevoltSensorEntityDescription(key="1136", name="DCDC Version Slave Unit 1", is_string=True),
    #IndevoltSensorEntityDescription(key="1137", name="BMS Version Slave Unit 1", is_string=True),
    #IndevoltSensorEntityDescription(key="9032", name="SN Battery Slave Unit 1", is_string=True),
    
    ### Slave Unit 2 Entities (STRING) / Battery 3
    #IndevoltSensorEntityDescription(key="1138", name="DCDC Version Slave Unit 2", is_string=True),
    #IndevoltSensorEntityDescription(key="1139", name="BMS Version Slave Unit 2", is_string=True),
    #IndevoltSensorEntityDescription(key="9051", name="SN Battery Slave Unit 2", is_string=True),    
    
    ### Slave Unit 3 Entities (STRING) / Battery 4
    #IndevoltSensorEntityDescription(key="1140", name="DCDC Version Slave Unit 3", is_string=True),
    #IndevoltSensorEntityDescription(key="1141", name="BMS Version Slave Unit 3", is_string=True),
    #IndevoltSensorEntityDescription(key="9070", name="SN Battery Slave Unit 3", is_string=True),
    
    ### Slave Unit 4 Entities (STRING) / Battery 5
    #IndevoltSensorEntityDescription(key="1142", name="DCDC Version Slave Unit 4", is_string=True),
    #IndevoltSensorEntityDescription(key="1143", name="BMS Version Slave Unit 4", is_string=True),
    #IndevoltSensorEntityDescription(key="9165", name="SN Battery Slave Unit 4", is_string=True),
    
    ### Slave Unit 5 Entities (STRING) / Battery 6
    #IndevoltSensorEntityDescription(key="1098", name="DCDC Version Slave Unit 5", is_string=True),
    #IndevoltSensorEntityDescription(key="1099", name="BMS Version Slave Unit 5", is_string=True),
    #IndevoltSensorEntityDescription(key="9218", name="SN Battery Slave Unit 5", is_string=True),
    
    IndevoltSensorEntityDescription(key="11019", name="Remaining Charging Time", is_string=True),
    IndevoltSensorEntityDescription(key="11020", name="Residual Discharge Time", is_string=True),
    IndevoltSensorEntityDescription(key="11039", name="Bypass Mode", is_string=True),
    
    #IndevoltSensorEntityDescription(key="605", name="System Time", is_string=True),
    # Add more string-type sensors here as needed
    # IndevoltSensorEntityDescription(key="XXXXX", name="Firmware Version", is_string=True),
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
        # Kept entry_id in unique_id to match your old installation logic and prevent duplicates
        self._attr_unique_id = f"{DOMAIN}_{sn}_{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.config_entry.entry_id)}, name=f"INDEVOLT {sn}")

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        
        # Handle string-type sensors
        if self.entity_description.is_string:
            # Return string value as-is, or None if not available
            return str(raw_value) if raw_value is not None else None
        
        # Handle ENUM-type sensors
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            return self.entity_description.state_mapping.get(raw_value) if raw_value is not None else None
        
        # Handle numeric sensors
        if raw_value is None:
            return self._last_valid_value if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING else None
        
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()
        
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
