from homeassistant.const import Platform

DOMAIN = "indevolt"
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30
PLATFORMS = [
    Platform.SENSOR
]

SUPPORTED_MODELS = [
    "BK1600/BK1600Ultra",
    "SolidFlex/PowerFlex2000"
]

# Physical hardware limits (based on SolidFlex 2000 specs)
# Note: BK1600 (Gen 1) had lower limits, but we use the highest supported values
# for validation, as the user-configurable options will provide the real safety net.
PHYSICAL_MAX_CHARGE_POWER = 2400
PHYSICAL_MAX_DISCHARGE_POWER = 800

# Config entry option keys
CONF_MAX_CHARGE_POWER = "max_charge_power"
CONF_MAX_DISCHARGE_POWER = "max_discharge_power"
