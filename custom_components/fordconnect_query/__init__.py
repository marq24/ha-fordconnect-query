import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Final

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    # ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import UpdateFailed, DataUpdateCoordinator, CoordinatorEntity
from homeassistant.loader import async_get_integration
from homeassistant.util.unit_system import UnitSystem
from .const import (
    DOMAIN,
    CONF_VIN,
    FORD_TELEMETRY_TEMP,
    FORD_VEH_HEALTH_TEMP,
    TRANSLATIONS,
    DEFAULT_SCAN_INTERVAL,
    CONF_GARAGE_DATA, FORD_FCON_QUERY_BASE_URL
)
from .const_shared import (
    CONF_PRESSURE_UNIT,
    MANUFACTURER_FORD,
    MANUFACTURER_LINCOLN,
    COORDINATOR_KEY,
    PRESSURE_UNITS,
    RCC_SEAT_MODE_NONE, RCC_SEAT_MODE_HEAT_AND_COOL, RCC_SEAT_MODE_HEAT_ONLY,
    STARTUP_MESSAGE,
    DEFAULT_PRESSURE_UNIT, CONF_LOG_TO_FILESYSTEM,
)
from .const_tags import Tag, FUEL_OR_PEV_ONLY_TAGS, EV_ONLY_TAGS, RCC_TAGS
from .fordpass_handler import (
    UNSUPPORTED,
    ROOT_METRICS,
    ROOT_MESSAGES,
    ROOT_VEHICLES,
    ROOT_UPDTIME,
    FordpassDataHandler
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA:Final = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
PLATFORMS:Final = [Platform.SENSOR, Platform.DEVICE_TRACKER]
LAST_TOKEN_KEY:Final = "last_token"
DATA_STORAGE_KEY:Final = "temp_data_storage"
TIME_KEY:Final = "time"
DATA_KEY:Final = "data"
RATE_LIMIT_INDICATOR:Final = "RATE_LIMIT"

OAUTH_TOKEN_KEY:Final = "token"
OAUTH_ACCESS_TOKEN_KEY:Final = "access_token"

async def async_setup(hass: HomeAssistant, config: dict):
    #hass.data.setdefault(DOMAIN, {})
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

    # in the fordconnect negation we only have the update interval in the options
    update_interval_as_int = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    _LOGGER.debug(f"[@{vin}] Update interval: {update_interval_as_int}")

    # creating our web-session...
    try:
        implementation = await async_get_config_entry_implementation(hass, config_entry)
    except ValueError as err:
        if "implementation not available" in str(err).lower():
            raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="oauth2_implementation_unavailable") from err
        else:
            _LOGGER.error(f"Unknown error occurred: {err}")
            raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="oauth2_implementation_unavailable") from err
    session = OAuth2Session(hass, config_entry, implementation)
    coordinator = FordConQDataCoordinator(hass, session, config_entry, update_interval_as_int=update_interval_as_int)

    # check if we can/must restore the last update time...
    temp_data_store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_STORAGE_KEY, {})
    restored_data = None
    if vin in temp_data_store:
        coordinator._last_update_time = temp_data_store[vin][TIME_KEY]
        restored_data = temp_data_store[vin][DATA_KEY]
        if restored_data is not None:
            coordinator.async_set_updated_data(restored_data)
            _LOGGER.debug(f"[@{vin}] Data restored: {len(coordinator.data)} {coordinator.data.keys()}")
        temp_data_store.pop(vin)

    if restored_data is None:
        # init our coordinator...
        await coordinator.async_refresh()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady("")

    await coordinator.read_config_on_startup(hass)

    # make sure our default options are set...
    if not config_entry.options:
        await async_update_options(hass, config_entry)

    # Store the current token to compare in the update listener
    current_token = config_entry.data.get(OAUTH_TOKEN_KEY, {}).get(OAUTH_ACCESS_TOKEN_KEY, None)
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_VIN: vin,
        COORDINATOR_KEY: coordinator,
        LAST_TOKEN_KEY: current_token
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # possible SERVICES coming here
    config_entry.async_on_unload(config_entry.add_update_listener(entry_update_listener))
    return True


async def async_update_options(hass, config_entry):
    _LOGGER.debug(f"async_update_options() called for entry: {config_entry.entry_id}")
    # the pressure unit is our only default...
    options = {
        CONF_PRESSURE_UNIT: config_entry.data.get(CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT),
    }
    hass.config_entries.async_update_entry(config_entry, options=options)


# we need to reload our entry on config changes...
async def entry_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    _LOGGER.debug(f"entry_update_listener(): called for entry: {config_entry.entry_id}")

    # Get the last known token from our data store
    the_entry_data = hass.data[DOMAIN].get(config_entry.entry_id, {})
    last_token = the_entry_data.get(LAST_TOKEN_KEY, None)

    # Get the current token from the config entry
    current_access_token = config_entry.data.get(OAUTH_TOKEN_KEY, {}).get(OAUTH_ACCESS_TOKEN_KEY, None)

    # If the token has changed, update our store and skip the reload
    if current_access_token != last_token:
        _LOGGER.debug(f"entry_update_listener(): only 'access token' was updated, skipping reload.")
        the_entry_data[LAST_TOKEN_KEY] = current_access_token
        return

    # only on 'none' access_token updates, reload the config_entry...
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"async_unload_entry() called for entry: {config_entry.entry_id}")
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR_KEY]
            # storing our last update time and a copy of the data.container...
            hass.data.setdefault(DOMAIN, {}).setdefault(DATA_STORAGE_KEY, {})[coordinator._vin] = {
                TIME_KEY: coordinator._last_update_time,
                DATA_KEY: coordinator.data.copy()
            }
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
        self._is_brand_lincoln = False # now hardcoded
        self._engine_type = None
        self._number_of_lighting_zones = 0
        self._log_to_filesystem = config_entry.options.get(CONF_LOG_TO_FILESYSTEM, False)
        if self._log_to_filesystem:
            self._storage_path = Path(hass.config.config_dir).joinpath(STORAGE_DIR)

        # different supporting booleans - probably none of them will be usefull in FordConnect?!
        self._supports_GUARD_MODE = None
        self._supports_REMOTE_START = None
        self._supports_ZONE_LIGHTING = None
        self._supports_ALARM = None
        self._supports_GEARLEVERPOSITION = None
        self._supports_AUTO_UPDATES = None
        self._supports_HAF = None
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

        self._a_task = None

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
        telemetry_data = await self.request_telemetry()
        if telemetry_data is None or telemetry_data == RATE_LIMIT_INDICATOR:
            raise UpdateFailed("No data received from Ford API (or exception/error)")
        else:
            pass
            # health_data = await self.request_health()
            # if health_data is not None and "VehicleAlertList" in health_data:
            #     # I need some sample data with content... :-/
            #     for a_alert in health_data["VehicleAlertList"]:
            #         a_alert_list = a_alert.get("ActiveAlerts", [])
            #         if len(a_alert_list) > 0:
            #             # the plan is to extract here the 'ActiveAlerts' and then insert them as
            #             # 'indicators' in the ROOT_META...
            #             pass

        if telemetry_data is not None:
            self._last_update_time = time.monotonic()
            return telemetry_data
            # result = {}
            # if ROOT_METRICS in telemetry_data:
            #     result[ROOT_METRICS] = telemetry_data[ROOT_METRICS]
            # if ROOT_UPDTIME in telemetry_data:
            #     result[ROOT_UPDTIME] = telemetry_data[ROOT_UPDTIME]
            # return result

        return self.data

    async def request_telemetry(self):
        telemetry_data = await self.__request_data(FORD_TELEMETRY_TEMP, "telemetry")
        return telemetry_data

    async def request_health(self):
        health_data = await self.__request_data(FORD_VEH_HEALTH_TEMP, "health")
        return health_data

    async def __request_data(self, url_template:str, type:str):
        url = url_template.format(base_url=FORD_FCON_QUERY_BASE_URL)
        res = await self._session.async_request(
            method="get",
            url=url
        )
        try:
            res.raise_for_status()
            response_data = await res.json()
            if response_data is not None:
                _LOGGER.debug(f"{self.vli}request_{type}(): {len(response_data)} - {response_data.keys() if response_data is not None else 'None'}")
            else:
                _LOGGER.debug(f"{self.vli}request_{type}(): No data received!")

            # dumping?
            if self._log_to_filesystem and response_data is not None:
                try:
                    await asyncio.get_running_loop().run_in_executor(None, lambda: self.__dump_data(type, response_data))
                except BaseException as e:
                    _LOGGER.debug(f"{self.vli}Error while dumping {type} data to file: {type(e).__name__} - {e}")

            return response_data

        except BaseException as e:
            if res.status == 429:
                _LOGGER.debug(f"{self.vli}request_{type}():{url} caused {res.status} - rate limit exceeded - sleeping for 15 seconds")
                self._last_update_time = time.monotonic()
                return RATE_LIMIT_INDICATOR
            else:
                _LOGGER.info(f"{self.vli}request_{type}():{url} caused {type(e).__name__} {e}")
                stack_trace = traceback.format_stack()
                stack_trace_str = ''.join(stack_trace[:-1])  # Exclude the call to this function
                _LOGGER.debug(f"{self.vli}stack trace (for marq24 to be able to debug):\n{stack_trace_str}")

    def __dump_data(self, type:str, data:dict):
        a_datetime = datetime.now(timezone.utc)
        filename = str(self._storage_path.joinpath(DOMAIN, "data_dumps", self._vin,
                                                   f"{a_datetime.year}", f"{a_datetime.month:02d}",
                                                   f"{a_datetime.day:02d}", f"{a_datetime.hour:02d}",
                                                   f"{a_datetime.strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]}_{type}.json"))
        try:
            directory = os.path.dirname(filename)
            if not os.path.exists(directory):
                os.makedirs(directory)

            #file_path = os.path.join(os.getcwd(), filename)
            with open(filename, "w", encoding="utf-8") as outfile:
                json.dump(data, outfile, indent=4)
        except BaseException as e:
            _LOGGER.info(f"{self.vli}__dump_data(): Error while writing data to file '{filename}' - {type(e).__name__} - {e}")

class FordPassEntity(CoordinatorEntity):
    """Defines a base FordPass entity."""
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name_addon = None

    def __init__(self, entity_type:str, a_tag: Tag, coordinator: FordConQDataCoordinator, description: EntityDescription | None = None):
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
        self.entity_id = f"{entity_type}.fcq_{self.coordinator._vin.lower()}_{a_tag.key}"
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