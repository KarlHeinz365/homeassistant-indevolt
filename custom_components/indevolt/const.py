from homeassistant.const import Platform

DOMAIN = "indevolt"
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_MAX_CHARGE_POWER = 1200
DEFAULT_MAX_DISCHARGE_POWER = 800
DEFAULT_VIRTUAL_MIN_SOC = 8
PLATFORMS = [
    Platform.SENSOR
]

SUPPORTED_MODELS = [
    "BK1600/BK1600Ultra",
    "SolidFlex/PowerFlex2000"
]


