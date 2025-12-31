from homeassistant.const import Platform

DOMAIN = "indevolt"
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30

# Virtuelle EPS Einstellungen
CONF_VIRTUAL_EPS_LIMIT = "virtual_eps_limit"
DEFAULT_VIRTUAL_EPS_LIMIT = 10

# Default power limits
DEFAULT_MAX_CHARGE_POWER = 1200
DEFAULT_MAX_DISCHARGE_POWER = 800

PLATFORMS = [Platform.SENSOR]

SUPPORTED_MODELS = [
    "BK1600/BK1600Ultra",
    "SolidFlex/PowerFlex2000"
]
