import logging
import time
import traceback
from datetime import timedelta
from typing import Any

import voluptuous as vol

from custom_components.fordconnect_query.const import (
    DOMAIN,
    CONF_VIN,
    FORD_TELEMETRY_URL,
    MANUFACTURER_FORD,
    MANUFACTURER_LINCOLN,
    COORDINATOR_KEY,
    TRANSLATIONS,
    CONF_PRESSURE_UNIT,
    PRESSURE_UNITS,
    RCC_SEAT_MODE_NONE, RCC_SEAT_MODE_HEAT_AND_COOL, RCC_SEAT_MODE_HEAT_ONLY, STARTUP_MESSAGE, SCAN_INTERVAL_DEFAULT,
    DEFAULT_PRESSURE_UNIT, CONF_GARAGE_DATA
)
from custom_components.fordconnect_query.const_tags import Tag, FUEL_OR_PEV_ONLY_TAGS, EV_ONLY_TAGS, RCC_TAGS
from custom_components.fordconnect_query.fordpass_handler import (
    UNSUPPORTED,
    ROOT_METRICS,
    ROOT_MESSAGES,
    ROOT_VEHICLES,
    FordpassDataHandler
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import ImplementationUnavailableError, OAuth2Session, \
    async_get_config_entry_implementation
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import UpdateFailed, DataUpdateCoordinator, CoordinatorEntity
from homeassistant.loader import async_get_integration
from homeassistant.util.unit_system import UnitSystem

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
#PLATFORMS = ["button", "lock", "number", "sensor", "switch", "select", "device_tracker"]
PLATFORMS = ["sensor", "device_tracker"]


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if DOMAIN not in hass.data:
        the_integration = await async_get_integration(hass, DOMAIN)
        intg_version = the_integration.version if the_integration is not None else "UNKNOWN"
        _LOGGER.info(STARTUP_MESSAGE % intg_version)
        hass.data.setdefault(DOMAIN, {"manifest_version": intg_version})



    # continue with startup...
    vin = config_entry.data[CONF_VIN]
    for config_entry_data in config_entry.data:
        _LOGGER.debug(f"[@{vin}] config_entry.data: {config_entry_data}")

    update_interval_as_int = config_entry.data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
    _LOGGER.debug(f"[@{vin}] Update interval: {update_interval_as_int}")


    # creating our web-session...
    try:
        implementation = await async_get_config_entry_implementation(hass, config_entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="oauth2_implementation_unavailable") from err
    session = OAuth2Session(hass, config_entry, implementation)
    coordinator = FordConQDataCoordinator(hass, session, config_entry, update_interval_as_int=update_interval_as_int)

    # init our coordinator...
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady("")
    else:
        await coordinator.read_config_on_startup(hass)

    # make sure our default options are set...
    if not config_entry.options:
        await async_update_options(hass, config_entry)

    fordconq_options_listener =config_entry.add_update_listener(entry_update_listener)

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR_KEY: coordinator,
        CONF_VIN: vin,
        "fordconq_options_listener": fordconq_options_listener
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # possible SERVICES coming here
    config_entry.async_on_unload(config_entry.add_update_listener(entry_update_listener))
    return True


async def async_update_options(hass, config_entry):
    # the pressure unit is our only default...
    options = {
        CONF_PRESSURE_UNIT: config_entry.data.get(CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT),
    }
    hass.config_entries.async_update_entry(config_entry, options=options)


# we need to reload our entry on config changes...
async def entry_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    _LOGGER.debug(f"entry_update_listener() called for entry: {config_entry.entry_id}")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"async_unload_entry() called for entry: {config_entry.entry_id}")
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR_KEY]
            await coordinator.clear_data()
            hass.data[DOMAIN].pop(config_entry.entry_id)

        # hass.services.async_remove(DOMAIN, "refresh_status")
        # hass.services.async_remove(DOMAIN, "clear_tokens")
        # hass.services.async_remove(DOMAIN, "poll_api")
        # hass.services.async_remove(DOMAIN, "reload")

    return unload_ok

class FordConQDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, session: OAuth2Session, config_entry: ConfigEntry, update_interval_as_int:int):
        self._session = session
        self.last_update_success = False
        self._vin = config_entry.data["vin"]
        self._last_update_time = 0

        # just copied over must check later...
        self._config_entry = config_entry
        self.vli = f"[@{self._vin}] "

        lang = hass.config.language.lower()
        if lang in TRANSLATIONS:
            self.lang_map = TRANSLATIONS[lang]
        else:
            self.lang_map = TRANSLATIONS["en"]

        self._available = True
        self._reauth_requested = False
        self._is_brand_lincoln = False # now hardcoded
        self._engine_type = None
        self._number_of_lighting_zones = 0
        self._supports_GUARD_MODE = None
        self._supports_REMOTE_START = None
        self._supports_ZONE_LIGHTING = None
        self._supports_ALARM = None
        self._supports_GEARLEVERPOSITION = None
        self._supports_AUTO_UPDATES = None
        self._supports_HAF = None
        self._force_REMOTE_CLIMATE_CONTROL = False  # now hardcoded
        self._supports_REMOTE_CLIMATE_CONTROL = None
        self._supports_HEATED_STEERING_WHEEL = None
        self._supports_HEATED_HEATED_SEAT_MODE = None

        # we need to make a clone of the unit system so that we can change the pressure unit (for our tire types)
        self.units:UnitSystem = hass.config.units
        if config_entry.options is not None and CONF_PRESSURE_UNIT in config_entry.options:
            user_pressure_unit = config_entry.options.get(CONF_PRESSURE_UNIT, None)
            if user_pressure_unit is not None and user_pressure_unit in PRESSURE_UNITS:
                local_pressure_unit = UnitOfPressure.KPA
                if user_pressure_unit == "PSI":
                    local_pressure_unit = UnitOfPressure.PSI
                elif user_pressure_unit == "BAR":
                    local_pressure_unit = UnitOfPressure.BAR

                orig = hass.config.units
                self.units = UnitSystem(
                    f"{orig._name}_fordconnect_query",
                    accumulated_precipitation=orig.accumulated_precipitation_unit,
                    area=orig.area_unit,
                    conversions=orig._conversions,
                    length=orig.length_unit,
                    mass=orig.mass_unit,
                    pressure=local_pressure_unit,
                    temperature=orig.temperature_unit,
                    volume=orig.volume_unit,
                    wind_speed=orig.wind_speed_unit,
                )

        self._watchdog = None
        self._a_task = None
        self._force_classic_requests = False

        # moved from 1'st line to bottom...
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=update_interval_as_int), config_entry=config_entry)


    def tag_not_supported_by_vehicle(self, a_tag: Tag) -> bool:
        if a_tag in FUEL_OR_PEV_ONLY_TAGS:
            return self.supportFuel is False

        if a_tag in EV_ONLY_TAGS:
            return self.supportPureEvOrPluginEv is False

        # handling of the remote climate control tags...
        if a_tag in RCC_TAGS:
            ret_val = self._supports_REMOTE_CLIMATE_CONTROL
            if ret_val:
                # not all vehicles do support some of the remote climate control tags, so we need to check
                if a_tag == Tag.RCC_STEERING_WHEEL:
                    ret_val = self._supports_HEATED_STEERING_WHEEL
                elif a_tag in [Tag.RCC_SEAT_FRONT_LEFT, Tag.RCC_SEAT_FRONT_RIGHT, Tag.RCC_SEAT_REAR_LEFT, Tag.RCC_SEAT_REAR_RIGHT]:
                    ret_val = self._supports_HEATED_HEATED_SEAT_MODE != RCC_SEAT_MODE_NONE

            #_LOGGER.error(f"{self.vli}Remote Climate Control support: {ret_val} - {a_tag.name}")
            return ret_val is False

        # other vehicle dependant tags...
        if a_tag in [Tag.REMOTE_START_STATUS,
                     Tag.REMOTE_START_COUNTDOWN,
                     Tag.REMOTE_START,
                     Tag.EXTEND_REMOTE_START,
                     Tag.GUARD_MODE,
                     Tag.ZONE_LIGHTING,
                     Tag.ALARM,
                     Tag.GEARLEVERPOSITION,
                     Tag.AUTO_UPDATES,
                     Tag.HAF_SHORT, Tag.HAF_DEFAULT, Tag.HAF_LONG]:
            # just handling the unpleasant fact, that for 'Tag.REMOTE_START_STATUS' and 'Tag.REMOTE_START' we just
            # share the same 'support_ATTR_NAME'...
            if a_tag == Tag.REMOTE_START_STATUS or a_tag == Tag.REMOTE_START_COUNTDOWN or a_tag == Tag.EXTEND_REMOTE_START:
                support_ATTR_NAME = f"_supports_{Tag.REMOTE_START.name}"
            elif a_tag in [Tag.HAF_SHORT, Tag.HAF_DEFAULT, Tag.HAF_LONG]:
                support_ATTR_NAME = f"_supports_HAF"
            else:
                support_ATTR_NAME = f"_supports_{a_tag.name}"

            return getattr(self, support_ATTR_NAME, None) is None or getattr(self, support_ATTR_NAME) is False

        return False

    @property
    def has_ev_soc(self) -> bool:
        return self._engine_type is not None and self._engine_type in ["BEV", "PHEV"]

    @property
    def supportPureEvOrPluginEv(self) -> bool:
        # looks like that 'HEV' are just have an additional 48V battery getting energy from breaking...
        # and also looks like that there is no special EV related data present in state object (json)
        return self._engine_type is not None and self._engine_type in ["BEV", "HEV", "PHEV"]

    @property
    def supportFuel(self) -> bool:
        return self._engine_type is not None and self._engine_type not in ["BEV"]


    async def clear_data(self):
        _LOGGER.debug(f"{self.vli}clear_data called...")
        self.data.clear()


    async def read_config_on_startup(self, hass: HomeAssistant):
        _LOGGER.debug(f"{self.vli}read_config_on_startup...")

        garage_data = self._config_entry.data.get(CONF_GARAGE_DATA, None)
        if garage_data is not None:
            # data = {'vin': 'WF0TK3R7ABCD01234', 'vehicleType': '2023 Mustang Mach-E', 'color': 'GRABBER BLUE METALLIC',
            #         'modelName': 'Mustang Mach-E', 'modelCode': 'VLGW', 'modelYear': '2023', 'tcuEnabled': 1,
            #         'make': 'Ford', 'ngSdnManaged': 1, 'vehicleAuthorizationIndicator': 1, 'engineType': 'BEV'}
            if "vehicleType" in garage_data:
                self.vli = f"[{garage_data['vehicleType']}] "

            if "engineType" in garage_data:
                self._engine_type = garage_data["engineType"]
                _LOGGER.debug(f"{self.vli}EngineType is: {self._engine_type}")

            if "numberOfLightingZones" in garage_data:
                self._number_of_lighting_zones = int(garage_data["numberOfLightingZones"])
                _LOGGER.debug(f"{self.vli}NumberOfLightingZones is: {self._number_of_lighting_zones}")

        if self.data is not None:
            self._supports_ALARM = Tag.ALARM.get_state(self.data) != UNSUPPORTED

            # other self._supports_* attribues will be checked in 'metrics' data...
            if ROOT_METRICS in self.data:
                self._supports_AUTO_UPDATES = Tag.AUTO_UPDATES.get_state(self.data) != UNSUPPORTED
                _LOGGER.debug(f"{self.vli}AutoUpdates supported: {self._supports_AUTO_UPDATES}")
        else:
            _LOGGER.warning(f"{self.vli}DATA is NONE!!! - {self.data}")

        # # THE CHECKS FROM FORDPASS Integration
        # # we are reading here from the global coordinator data object!
        # if self.data is not None:
        #     if ROOT_VEHICLES in self.data:
        #         veh_data = self.data[ROOT_VEHICLES]
        #
        #         # getting the engineType...
        #         if "vehicleProfile" in veh_data:
        #             for a_vehicle_profile in veh_data["vehicleProfile"]:
        #                 if a_vehicle_profile["VIN"] == self._vin:
        #                     if "model" in a_vehicle_profile:
        #                         self.vli = f"[{a_vehicle_profile['model']}] "
        #
        #                     if "engineType" in a_vehicle_profile:
        #                         self._engine_type = a_vehicle_profile["engineType"]
        #                         _LOGGER.debug(f"{self.vli}EngineType is: {self._engine_type}")
        #
        #                     if "numberOfLightingZones" in a_vehicle_profile:
        #                         self._number_of_lighting_zones = int(a_vehicle_profile["numberOfLightingZones"])
        #                         _LOGGER.debug(f"{self.vli}NumberOfLightingZones is: {self._number_of_lighting_zones}")
        #
        #                     if "transmissionIndicator" in a_vehicle_profile:
        #                         self._supports_GEARLEVERPOSITION = a_vehicle_profile["transmissionIndicator"] == "A"
        #                         _LOGGER.debug(f"{self.vli}GearLeverPosition support: {self._supports_GEARLEVERPOSITION}")
        #
        #                     # remote climate control stuff...
        #                     if self._force_REMOTE_CLIMATE_CONTROL:
        #                         self._supports_REMOTE_CLIMATE_CONTROL = True
        #                         _LOGGER.debug(f"{self.vli}RemoteClimateControl FORCED: {self._supports_REMOTE_CLIMATE_CONTROL}")
        #                     else:
        #                         if "remoteClimateControl" in a_vehicle_profile:
        #                             self._supports_REMOTE_CLIMATE_CONTROL = a_vehicle_profile["remoteClimateControl"]
        #                             _LOGGER.debug(f"{self.vli}RemoteClimateControl support: {self._supports_REMOTE_CLIMATE_CONTROL}")
        #
        #                         if not self._supports_REMOTE_CLIMATE_CONTROL and "remoteHeatingCooling" in a_vehicle_profile:
        #                             self._supports_REMOTE_CLIMATE_CONTROL = a_vehicle_profile["remoteHeatingCooling"]
        #                             _LOGGER.debug(f"{self.vli}RemoteClimateControl/remoteHeatingCooling support: {self._supports_REMOTE_CLIMATE_CONTROL}")
        #
        #                     if "heatedSteeringWheel" in a_vehicle_profile:
        #                         self._supports_HEATED_STEERING_WHEEL = a_vehicle_profile["heatedSteeringWheel"]
        #                         _LOGGER.debug(f"{self.vli}HeatedSteeringWheel support: {self._supports_HEATED_STEERING_WHEEL}")
        #
        #                     self._supports_HEATED_HEATED_SEAT_MODE = RCC_SEAT_MODE_NONE
        #                     if "driverHeatedSeat" in a_vehicle_profile:
        #                         # possible values: 'None', 'Heat Only', 'Heat with Vent'
        #                         heated_seat = a_vehicle_profile["driverHeatedSeat"].upper()
        #                         if heated_seat == "HEAT WITH VENT":
        #                             self._supports_HEATED_HEATED_SEAT_MODE = RCC_SEAT_MODE_HEAT_AND_COOL
        #                         elif "HEAT" in heated_seat:
        #                             self._supports_HEATED_HEATED_SEAT_MODE = RCC_SEAT_MODE_HEAT_ONLY
        #                     _LOGGER.debug(f"{self.vli}DriverHeatedSeat support mode: {self._supports_HEATED_HEATED_SEAT_MODE}")
        #                     break
        #         else:
        #             _LOGGER.warning(f"{self.vli}No vehicleProfile in 'vehicles' found in coordinator data - no 'engineType' available! {self.data['vehicles']}")
        #
        #         # check, if RemoteStart is supported
        #         if "vehicleCapabilities" in veh_data:
        #             for capability_obj in veh_data["vehicleCapabilities"]:
        #                 if capability_obj["VIN"] == self._vin:
        #                     self._supports_ALARM = Tag.ALARM.get_state(self.data) != UNSUPPORTED
        #                     self._supports_REMOTE_START = self._check_if_veh_capability_supported("remoteStart", capability_obj)
        #                     self._supports_GUARD_MODE = self._check_if_veh_capability_supported("guardMode", capability_obj)
        #                     self._supports_ZONE_LIGHTING = self._check_if_veh_capability_supported("zoneLighting", capability_obj) and self._number_of_lighting_zones > 0
        #                     self._supports_HAF = self._check_if_veh_capability_supported("remotePanicAlarm", capability_obj)
        #                     break
        #         else:
        #             _LOGGER.warning(f"{self.vli}No vehicleCapabilities in 'vehicles' found in coordinator data - no 'support_remote_start' available! {self.data['vehicles']}")
        #
        #         # check, if GuardMode is supported
        #         # [original impl]
        #         self._supports_GUARD_MODE = FordpassDataHandler.is_guard_mode_supported(self.data)
        #
        #     else:
        #         _LOGGER.warning(f"{self.vli}No vehicles data found in coordinator data - no engineType available! {self.data}")
        #
        #     # other self._supports_* attribues will be checked in 'metrics' data...
        #     if ROOT_METRICS in self.data:
        #         self._supports_AUTO_UPDATES = Tag.AUTO_UPDATES.get_state(self.data) != UNSUPPORTED
        #         _LOGGER.debug(f"{self.vli}AutoUpdates supported: {self._supports_AUTO_UPDATES}")
        # else:
        #     _LOGGER.warning(f"{self.vli}DATA is NONE!!! - {self.data}")

    def _check_if_veh_capability_supported(self, a_capability: str, capabilities: dict) -> bool:
        """Check if a specific vehicle capability is supported."""
        is_supported = False
        if a_capability in capabilities and capabilities[a_capability] is not None:
            val = capabilities[a_capability]
            if (isinstance(val, bool) and val) or val.upper() == "DISPLAY":
                is_supported = True
            _LOGGER.debug(f"{self.vli}Is '{a_capability}' supported?: {is_supported} - {val}")
        else:
            _LOGGER.warning(f"{self.vli}No '{a_capability}' data found for VIN {self._vin} - assuming not supported")

        return is_supported



    async def _async_update_data(self):
        _LOGGER.debug(f"{self.vli}_async_update_data(): Updating data for VIN: {self._vin}")
        now = time.monotonic()
        if now - self._last_update_time < 15:
            _LOGGER.debug(f"{self.vli}Rate limit: Returning cached data (last update {now - self._last_update_time:.1f}s ago)")
            return self.data

        # IMHO this is not required for an OAuth2Session
        await self._session.async_ensure_token_valid()
        some_data = await self.get_telemetry()
        if some_data is None:
            raise UpdateFailed("No data received from Ford API")

        self._last_update_time = time.monotonic()
        return some_data

    async def get_telemetry(self):
        res = await self._session.async_request(
            method="get",
            url=FORD_TELEMETRY_URL
        )
        try:
            res.raise_for_status()
            data = await res.json()
            #_LOGGER.debug(f"get_telemetry(): {data}")

            parsed = {ROOT_METRICS: data}
            _LOGGER.debug(f"{self.vli}get_telemetry(): {len(data)}")
            return data
        except BaseException as e:
            _LOGGER.error(f"{self.vli}get_telemetry(): {type(e).__name__} {e}")

            stack_trace = traceback.format_stack()
            stack_trace_str = ''.join(stack_trace[:-1])  # Exclude the call to this function
            _LOGGER.info(f"{self.vli}the stack trace:\n{stack_trace_str}")



class FordPassEntity(CoordinatorEntity):
    """Defines a base FordPass entity."""
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name_addon = None

    def __init__(self, a_tag: Tag, coordinator: FordConQDataCoordinator, description: EntityDescription | None = None):
        """Initialize the entity."""
        super().__init__(coordinator, description)

        # ok setting the internal translation key attr (so we can make use of the translation key in the entity)
        self._attr_translation_key = a_tag.key.lower()
        if description is not None:
            self.entity_description = description
            # if an 'entity_description' is present and the description has a translation key - we use it!
            if hasattr(description, "translation_key") and description.translation_key is not None:
                self._attr_translation_key = description.translation_key.lower()

        if hasattr(description, "name_addon"):
            self._attr_name_addon = description.name_addon

        self.coordinator: FordConQDataCoordinator = coordinator
        self.entity_id = f"{DOMAIN}.fcq_{self.coordinator._vin.lower()}_{a_tag.key}"
        self._tag = a_tag

    def _name_internal(self, device_class_name: str | None, platform_translations: dict[str, Any], ) -> str | UndefinedType | None:
        tmp = super()._name_internal(device_class_name, platform_translations)
        if self._attr_name_addon is not None:
            return f"{self._attr_name_addon} {tmp}"
        else:
            return tmp

    @property
    def device_id(self):
        return f"fcq_did_{self.self.coordinator._vin.lower()}"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return f"fcq_uid_{self.coordinator._vin.lower()}_{self._tag.key}"

    @property
    def device_info(self):
        """Return device information about this device."""
        if self._tag is None:
            return None

        model = "unknown"
        garage_data = self.coordinator._config_entry.data.get(CONF_GARAGE_DATA, None)
        if garage_data is not None:
            # data = {'vin': 'WF0TK3R7ABCD01234', 'vehicleType': '2023 Mustang Mach-E', 'color': 'GRABBER BLUE METALLIC',
            #         'modelName': 'Mustang Mach-E', 'modelCode': 'VLGW', 'modelYear': '2023', 'tcuEnabled': 1,
            #         'make': 'Ford', 'ngSdnManaged': 1, 'vehicleAuthorizationIndicator': 1, 'engineType': 'BEV'}
            if "vehicleType" in garage_data:
                model = f"{garage_data['vehicleType']}"
            elif "modelName" in garage_data and "modelYear" in garage_data:
                model = f"{garage_data['modelYear']} {garage_data['modelName']}"
            elif "modelName" in garage_data:
                model = f"{garage_data['modelName']}"

        return {
            "identifiers": {(DOMAIN, self.coordinator._vin)},
            "name": f"VIN: {self.coordinator._vin}",
            "model": f"{model}",
            "manufacturer": MANUFACTURER_LINCOLN if self.coordinator._is_brand_lincoln else MANUFACTURER_FORD
        }


    def _friendly_name_internal(self) -> str | None:
        """Return the friendly name.
        If has_entity_name is False, this returns self.name
        If has_entity_name is True, this returns device.name + self.name
        """
        name = self.name
        if name is UNDEFINED:
            name = None

        if not self.has_entity_name or not (device_entry := self.device_entry):
            return name

        device_name = device_entry.name_by_user or device_entry.name
        if name is None and self.use_device_name:
            return device_name

        # we overwrite the default impl here and just return our 'name'
        # return f"{device_name} {name}" if device_name else name
        if device_entry.name_by_user is not None:
            return f"{device_entry.name_by_user} {name}" if device_name else name
        # elif self.coordinator.include_fordpass_prefix:
        #    return f"[fordpass] {name}"
        else:
            return name