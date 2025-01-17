"""Viessmann ViCare sensor device."""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import logging

from PyViCare.PyViCareUtils import (
    PyViCareInvalidDataError,
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.sensor import (
    STATE_CLASS_TOTAL_INCREASING,
    SensorEntityDescription,
    SensorEntity,
)
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_GAS,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TIME_HOURS,
)
import homeassistant.util.dt as dt_util

from . import ViCareRequiredKeysMixin
from .const import DOMAIN, VICARE_API, VICARE_DEVICE_CONFIG, VICARE_NAME

_LOGGER = logging.getLogger(__name__)

SENSOR_OUTSIDE_TEMPERATURE = "outside_temperature"
SENSOR_SUPPLY_TEMPERATURE = "supply_temperature"
SENSOR_RETURN_TEMPERATURE = "return_temperature"

# gas sensors
SENSOR_BOILER_TEMPERATURE = "boiler_temperature"
SENSOR_BURNER_MODULATION = "burner_modulation"
SENSOR_BURNER_STARTS = "burner_starts"
SENSOR_BURNER_HOURS = "burner_hours"
SENSOR_BURNER_POWER = "burner_power"
SENSOR_DHW_GAS_CONSUMPTION_TODAY = "hotwater_gas_consumption_today"
SENSOR_DHW_GAS_CONSUMPTION_THIS_WEEK = "hotwater_gas_consumption_heating_this_week"
SENSOR_DHW_GAS_CONSUMPTION_THIS_MONTH = "hotwater_gas_consumption_heating_this_month"
SENSOR_DHW_GAS_CONSUMPTION_THIS_YEAR = "hotwater_gas_consumption_heating_this_year"
SENSOR_GAS_CONSUMPTION_TODAY = "gas_consumption_heating_today"
SENSOR_GAS_CONSUMPTION_THIS_WEEK = "gas_consumption_heating_this_week"
SENSOR_GAS_CONSUMPTION_THIS_MONTH = "gas_consumption_heating_this_month"
SENSOR_GAS_CONSUMPTION_THIS_YEAR = "gas_consumption_heating_this_year"

# heatpump sensors
SENSOR_COMPRESSOR_STARTS = "compressor_starts"
SENSOR_COMPRESSOR_HOURS = "compressor_hours"
SENSOR_COMPRESSOR_HOURS_LOADCLASS1 = "compressor_hours_loadclass1"
SENSOR_COMPRESSOR_HOURS_LOADCLASS2 = "compressor_hours_loadclass2"
SENSOR_COMPRESSOR_HOURS_LOADCLASS3 = "compressor_hours_loadclass3"
SENSOR_COMPRESSOR_HOURS_LOADCLASS4 = "compressor_hours_loadclass4"
SENSOR_COMPRESSOR_HOURS_LOADCLASS5 = "compressor_hours_loadclass5"

# fuelcell sensors
SENSOR_POWER_PRODUCTION_CURRENT = "power_production_current"
SENSOR_POWER_PRODUCTION_TODAY = "power_production_today"
SENSOR_POWER_PRODUCTION_THIS_WEEK = "power_production_this_week"
SENSOR_POWER_PRODUCTION_THIS_MONTH = "power_production_this_month"
SENSOR_POWER_PRODUCTION_THIS_YEAR = "power_production_this_year"


@dataclass
class ViCareSensorEntityDescription(SensorEntityDescription, ViCareRequiredKeysMixin):
    """Describes ViCare sensor entity."""


GLOBAL_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key=SENSOR_OUTSIDE_TEMPERATURE,
        name="Outside Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        value_getter=lambda api: api.getOutsideTemperature(),
        device_class=DEVICE_CLASS_TEMPERATURE,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_RETURN_TEMPERATURE,
        name="Return Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        value_getter=lambda api: api.getReturnTemperature(),
        device_class=DEVICE_CLASS_TEMPERATURE,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_BOILER_TEMPERATURE,
        name="Boiler Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        value_getter=lambda api: api.getBoilerTemperature(),
        device_class=DEVICE_CLASS_TEMPERATURE,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_DHW_GAS_CONSUMPTION_TODAY,
        name="Hot water gas consumption today",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterToday(),
        device_class=DEVICE_CLASS_GAS,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_DHW_GAS_CONSUMPTION_THIS_WEEK,
        name="Hot water gas consumption this week",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisWeek(),
        device_class=DEVICE_CLASS_GAS,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_DHW_GAS_CONSUMPTION_THIS_MONTH,
        name="Hot water gas consumption this month",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisMonth(),
        device_class=DEVICE_CLASS_GAS,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_DHW_GAS_CONSUMPTION_THIS_YEAR,
        name="Hot water gas consumption this year",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisYear(),
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_GAS_CONSUMPTION_TODAY,
        name="Heating gas consumption today",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionTotalToday(),
        device_class=DEVICE_CLASS_GAS,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),    
    ViCareSensorEntityDescription(
        key=SENSOR_GAS_CONSUMPTION_THIS_WEEK,
        name="Heating gas consumption this week",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionTotalThisWeek(),
        device_class=DEVICE_CLASS_GAS,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),    
    ViCareSensorEntityDescription(
        key=SENSOR_GAS_CONSUMPTION_THIS_MONTH,
        name="Heating gas consumption this month",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionTotalThisMonth(),
        device_class=DEVICE_CLASS_GAS,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),    
    ViCareSensorEntityDescription(
        key=SENSOR_GAS_CONSUMPTION_THIS_YEAR,
        name="Heating gas consumption this year",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getGasConsumptionTotalThisYear(),
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_POWER_PRODUCTION_CURRENT,
        name="Power production current",
        native_unit_of_measurement=POWER_WATT,
        value_getter=lambda api: api.getPowerProductionCurrent(),
        device_class=DEVICE_CLASS_POWER,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_POWER_PRODUCTION_TODAY,
        name="Power production today",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionHeatingToday(),
        device_class=DEVICE_CLASS_ENERGY,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_POWER_PRODUCTION_THIS_WEEK,
        name="Power production this week",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionHeatingThisWeek(),
        device_class=DEVICE_CLASS_ENERGY,
    ),    
    ViCareSensorEntityDescription(
        key=SENSOR_POWER_PRODUCTION_THIS_MONTH,
        name="Power production this month",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionHeatingThisMonth(),
        device_class=DEVICE_CLASS_ENERGY,
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_POWER_PRODUCTION_THIS_YEAR,
        name="Power production this year",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionHeatingThisYear(),
        device_class=DEVICE_CLASS_ENERGY,
    )
)

CIRCUIT_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key=SENSOR_SUPPLY_TEMPERATURE,
        name="Supply Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        value_getter=lambda api: api.getSupplyTemperature(),
    ),
)

BURNER_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key=SENSOR_BURNER_STARTS,
        name="Burner Starts",
        icon="mdi:counter",
        value_getter=lambda api: api.getStarts(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_BURNER_HOURS,
        name="Burner Hours",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHours(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_BURNER_MODULATION,
        name="Burner Modulation",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        value_getter=lambda api: api.getModulation(),
    ),
)

COMPRESSOR_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_STARTS,
        name="Compressor Starts",
        icon="mdi:counter",
        value_getter=lambda api: api.getStarts(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS,
        name="Compressor Hours",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHours(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS_LOADCLASS1,
        name="Compressor Hours Load Class 1",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHoursLoadClass1(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS_LOADCLASS2,
        name="Compressor Hours Load Class 2",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHoursLoadClass2(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS_LOADCLASS3,
        name="Compressor Hours Load Class 3",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHoursLoadClass3(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS_LOADCLASS4,
        name="Compressor Hours Load Class 4",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHoursLoadClass4(),
    ),
    ViCareSensorEntityDescription(
        key=SENSOR_COMPRESSOR_HOURS_LOADCLASS5,
        name="Compressor Hours Load Class 5",
        icon="mdi:counter",
        native_unit_of_measurement=TIME_HOURS,
        value_getter=lambda api: api.getHoursLoadClass5(),
    )
)


def _build_entity(name, vicare_api, device_config, sensor):
    _LOGGER.debug("Found device %s", name)
    try:
        sensor.value_getter(vicare_api)
        _LOGGER.debug("Found entity %s", name)
        return ViCareSensor(
            name,
            vicare_api,
            device_config,
            sensor,
        )
    except PyViCareNotSupportedFeatureError:
        _LOGGER.info("Feature not supported %s", name)
        return None
    except AttributeError:
        _LOGGER.debug("Attribute Error %s", name)
        return None


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Create the ViCare sensor devices."""
    name = hass.data[DOMAIN][config_entry.entry_id][VICARE_NAME]
    api = hass.data[DOMAIN][config_entry.entry_id][VICARE_API]

    all_devices = []
    for description in GLOBAL_SENSORS:
        entity = _build_entity(
            f"{name} {description.name}",
            api,
            hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
            description,
        )
        if entity is not None:
            all_devices.append(entity)

    for description in CIRCUIT_SENSORS:
        for circuit in api.circuits:
            suffix = ""
            if len(api.circuits) > 1:
                suffix = f" {circuit.id}"
            entity = _build_entity(
                f"{name} {description.name}{suffix}",
                circuit,
                hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
                description,
            )
            if entity is not None:
                all_devices.append(entity)

    try:
        for description in BURNER_SENSORS:
            for burner in api.burners:
                suffix = ""
                if len(api.burners) > 1:
                    suffix = f" {burner.id}"
                entity = _build_entity(
                    f"{name} {description.name}{suffix}",
                    burner,
                    hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
                    description,
                )
                if entity is not None:
                    all_devices.append(entity)
    except PyViCareNotSupportedFeatureError:
        _LOGGER.info("No burners found")

    try:
        for description in COMPRESSOR_SENSORS:
            for compressor in api.compressors:
                suffix = ""
                if len(api.compressors) > 1:
                    suffix = f" {compressor.id}"
                entity = _build_entity(
                    f"{name} {description.name}{suffix}",
                    compressor,
                    hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
                    description,
                )
                if entity is not None:
                    all_devices.append(entity)
    except PyViCareNotSupportedFeatureError:
        _LOGGER.info("No compressor found")

    async_add_devices(all_devices)


class ViCareSensor(SensorEntity):
    """Representation of a ViCare sensor."""

    entity_description: ViCareSensorEntityDescription

    def __init__(
        self, name, api, device_config, description: ViCareSensorEntityDescription
    ):
        """Initialize the sensor."""
        self.entity_description = description
        self._attr_name = name
        self._api = api
        self._device_config = device_config
        self._state = None
        #self._last_reset = dt_util.utcnow()

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self._device_config.getConfig().serial)},
            "name": self._device_config.getModel(),
            "manufacturer": "Viessmann",
            "model": (DOMAIN, self._device_config.getModel()),
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return f"{self._device_config.getConfig().serial}-{self._attr_name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    #@property
    #def last_reset(self):
    #    """Return the time when the sensor was last reset."""
    #    return self._last_reset

    def update(self):
        """Update state of sensor."""
        #self._last_reset = dt_util.start_of_local_day()
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._state = self.entity_description.value_getter(self._api)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
        except PyViCareInvalidDataError as invalid_data_exception:
            _LOGGER.error("Invalid data from Vicare server: %s", invalid_data_exception)
