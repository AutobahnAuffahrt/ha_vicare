"""The ViCare integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable

from PyViCare.PyViCare import PyViCare
from PyViCare.PyViCareDevice import Device
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    CONF_HEATING_TYPE,
    DEFAULT_HEATING_TYPE,
    DOMAIN,
    PLATFORMS,
    VICARE_API,
    VICARE_CIRCUITS,
    VICARE_DEVICE_CONFIG,
    VICARE_NAME,
    HeatingType,
)


@dataclass()
class ViCareRequiredKeysMixin:
    """Mixin for required keys."""

    value_getter: Callable[[Device], bool]


_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    cv.time_period, lambda value: value.total_seconds()
                ),
                vol.Optional(CONF_NAME, default="ViCare"): cv.string,
                vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): cv.enum(
                    HeatingType
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up the ViCare component from yaml."""
    if DOMAIN not in config:
        # Setup via UI. No need to continue yaml-based setup
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    _LOGGER.debug("Setting up ViCare component")

    hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id][VICARE_NAME] = entry.data[CONF_NAME]

    if entry.data.get(CONF_HEATING_TYPE) is not None:
        hass.data[DOMAIN][entry.entry_id][CONF_HEATING_TYPE] = HeatingType[
            entry.data[CONF_HEATING_TYPE]
        ]
    else:
        hass.data[DOMAIN][entry.entry_id][CONF_HEATING_TYPE] = DEFAULT_HEATING_TYPE

    # For previous config entries where unique_id is None
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=entry.data[CONF_USERNAME]
        )

    await hass.async_add_executor_job(
        setup_vicare_api, hass, entry.data, hass.data[DOMAIN][entry.entry_id]
    )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


def vicare_login(hass, conf):
    """Login via PyVicare API."""
    vicare_api = PyViCare()
    vicare_api.setCacheDuration(conf[CONF_SCAN_INTERVAL])
    vicare_api.initWithCredentials(
        conf[CONF_USERNAME],
        conf[CONF_PASSWORD],
        conf[CONF_CLIENT_ID],
        hass.config.path(STORAGE_DIR, "vicare_token.save"),
    )


def setup_vicare_api(hass, conf, entity_data):
    """Set up PyVicare API."""
    vicare_api = PyViCare()
    vicare_api.setCacheDuration(conf[CONF_SCAN_INTERVAL])
    vicare_api.initWithCredentials(
        conf[CONF_USERNAME],
        conf[CONF_PASSWORD],
        conf[CONF_CLIENT_ID],
        hass.config.path(STORAGE_DIR, "vicare_token.save"),
    )

    device = vicare_api.devices[0]
    for device in vicare_api.devices:
        _LOGGER.info(
            "Found device: %s (online: %s)", device.getModel(), str(device.isOnline())
        )
    entity_data[VICARE_DEVICE_CONFIG] = device

    device_types = [
        (device.asAutoDetectDevice, HeatingType.auto),
        (device.asGazBoiler, HeatingType.gas),
        (device.asFuelCell, HeatingType.fuelcell),
        (device.asHeatPump, HeatingType.heatpump),
        (device.asOilBoiler, HeatingType.oil),
        (device.asPelletsBoiler, HeatingType.pellets),
    ]

    for (creator_method, heating_type) in device_types:
        if heating_type == entity_data[CONF_HEATING_TYPE]:
            _LOGGER.info("Using creator_method %s", creator_method.__name__)
            entity_data[VICARE_API] = creator_method()

    entity_data[VICARE_CIRCUITS] = entity_data[VICARE_API].circuits


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload ViCare config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
