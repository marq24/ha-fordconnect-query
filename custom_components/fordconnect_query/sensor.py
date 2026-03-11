"""All vehicle sensors from the accessible by the API"""
import logging
from dataclasses import replace
from datetime import datetime
from numbers import Number

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import FordPassEntity, FordConQDataCoordinator
from .const import DOMAIN
from .const_shared import COORDINATOR_KEY
from .const_tags import SENSORS, ExtSensorEntityDescription, Tag
from .fordpass_handler import UNSUPPORTED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR_KEY]
    _LOGGER.debug(f"{coordinator.vli}SENSOR async_setup_entry")
    sensors = []

    for a_entity_description in SENSORS:
        a_entity_description: ExtSensorEntityDescription

        if coordinator.tag_not_supported_by_vehicle(a_entity_description.tag):
            _LOGGER.debug(f"{coordinator.vli}SENSOR '{a_entity_description.tag}' not supported for this engine-type/vehicle")
            continue

        sensor = FordPassSensor(coordinator, a_entity_description)
        # calling the state reading function to check if the sensor should be added (if there is any data)
        value = a_entity_description.tag.state_fn(coordinator.data, None)
        if value is not None and ((isinstance(value, (str, Number)) and str(value) != UNSUPPORTED) or
                                  (isinstance(value, (dict, list)) and len(value) != 0) or
                                  (isinstance(value, datetime) and value) ):
            sensors.append(sensor)
        else:
            _LOGGER.debug(f"{coordinator.vli}SENSOR '{a_entity_description.tag}' skipping cause no data available: type: {type(value).__name__} - value:'{value}'")

    async_add_entities(sensors, True)


class FordPassSensor(FordPassEntity, SensorEntity):

    def __init__(self, coordinator:FordConQDataCoordinator, entity_description:ExtSensorEntityDescription):
        # make sure that we set the device class for battery sensors [see #89]
        if (coordinator.has_ev_soc and entity_description.tag == Tag.SOC) or (not coordinator.supportFuel and entity_description.tag == Tag.FUEL):
            entity_description = replace(
                entity_description,
                device_class=SensorDeviceClass.BATTERY
            )
        super().__init__(entity_type=Platform.SENSOR, a_tag=entity_description.tag, coordinator=coordinator, description=entity_description)

    @property
    def extra_state_attributes(self):
        """Return sensor attributes"""
        return self._tag.get_attributes(self.coordinator.data, self.coordinator.units)

    @property
    def native_value(self):
        """Return Native Value"""
        return self._tag.get_state(self.coordinator.data, None)

    @property
    def available(self):
        """Return True if the entity is available."""
        state = super().available
        # the countdown sensor can be always active (does not hurt)
        # if self._tag == Tag.REMOTE_START_COUNTDOWN:
        #     return state and Tag.REMOTE_START_STATUS.get_state(self.coordinator.data) == REMOTE_START_STATE_ACTIVE
        return state