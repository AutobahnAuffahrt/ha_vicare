"""Constants for the ViCare integration."""
import enum

from homeassistant.const import DEVICE_CLASS_ENERGY, DEVICE_CLASS_GAS

DOMAIN = "vicare"

PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

VICARE_DEVICE_CONFIG = "device_conf"
VICARE_API = "api"
VICARE_NAME = "name"
VICARE_CIRCUITS = "circuits"

CONF_HEATING_TYPE = "heating_type"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_HEATING_TYPE = "auto"

VICARE_CUBIC_METER = "cubicMeter"
VICARE_KWH = "kilowattHour"

VICARE_UNIT_TO_DEVICE_CLASS = {
    VICARE_KWH: DEVICE_CLASS_ENERGY,
    VICARE_CUBIC_METER: DEVICE_CLASS_GAS,
}


class HeatingType(enum.Enum):
    """Possible options for heating type."""

    auto = "auto"
    gas = "gas"
    oil = "oil"
    pellets = "pellets"
    heatpump = "heatpump"
    fuelcell = "fuelcell"
