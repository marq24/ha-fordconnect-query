import logging
from enum import Enum
from typing import Final

_LOGGER = logging.getLogger(__name__)

DOMAIN: Final = "fordconnect-query"
CALLBACK_URL: Final = "/fordconnect-eu-cb"
CALLBACK_NAME: Final = "fordconnect-eu-cb" # the name should not really matter...
STATE_LOOKUP_MAP = "secure_state-to-flow_id-map"

FORD_AUTHORIZE_URL: Final = "https://api.vehicle.ford.com/fcon-public/v1/auth/init"
FORD_TOKEN_URL: Final     = "https://api.vehicle.ford.com/dah2vb2cprod.onmicrosoft.com/oauth2/v2.0/token?p=B2C_1A_FCON_AUTHORIZE"

FORD_GARAGE_URL: Final    = "https://api.vehicle.ford.com/fcon-query/v1/garage"
FORD_TELEMETRY_URL: Final = "https://api.vehicle.ford.com/fcon-query/v1/telemetry"

NAME: Final = "Fordconnect for EU integration for Home Assistant"
ISSUE_URL: Final = "https://github.com/marq24/ha-fordpass/issues"
MANUFACTURER_FORD: Final = "Ford Motor Company"
MANUFACTURER_LINCOLN: Final = "Lincoln Motor Company"

STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{NAME} - v%s
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

CONFIG_VERSION: Final = 1
CONFIG_MINOR_VERSION: Final = 0

CONF_VIN = "vin"
CONF_GARAGE_DATA = "garage"
CONF_TITLE = "title"
CONF_PRESSURE_UNIT: Final = "pressure_unit"
CONF_LOG_TO_FILESYSTEM: Final = "log_to_filesystem"

SCAN_INTERVAL_DEFAULT: Final = 60 #290 # it looks like that the default auto-access_token expires after 5 minutes (300 seconds)

COORDINATOR_KEY: Final = "coordinator"

DEFAULT_PRESSURE_UNIT: Final = "kPa"
PRESSURE_UNITS: Final = ["PSI", "kPa", "BAR"]

WINDOW_POSITIONS: Final = {
    "CLOSED": {
        "Fully_Closed": "Closed",
        "Fully_closed_position": "Closed",
        "Fully closed position": "Closed",
    },
    "OPEN": {
        "Fully open position": "Open",
        "Fully_Open": "Open",
        "Btwn 10% and 60% open": "Open-Partial",
    },
}

REMOTE_START_STATE_ACTIVE: Final      = "Active"
REMOTE_START_STATE_INACTIVE: Final    = "Inactive"

RCC_SEAT_MODE_HEAT_AND_COOL: Final = "HEAT_AND_COOL"
RCC_SEAT_MODE_HEAT_ONLY: Final = "HEAT_ONLY"
RCC_SEAT_MODE_NONE: Final = "NONE"
RCC_SEAT_OPTIONS_FULL: Final = ["off", "heated1", "heated2", "heated3", "cooled1", "cooled2", "cooled3"]
RCC_SEAT_OPTIONS_HEAT_ONLY: Final = ["off", "heated1", "heated2", "heated3"]

RCC_TEMPERATURES_CELSIUS:    Final = ["lo",
                                      "16", "16_5", "17", "17_5", "18", "18_5", "19", "19_5", "20", "20_5",
                                      "21", "21_5", "22", "22_5", "23", "23_5", "24", "24_5", "25", "25_5",
                                      "26", "26_5", "27", "27_5", "28", "28_5", "29", "30",
                                      "hi"]

ELVEH_TARGET_CHARGE_OPTIONS: Final = ["50", "60", "70", "80", "85", "90", "95", "100"]

VEHICLE_LOCK_STATE_LOCKED:      Final = "LOCKED"
VEHICLE_LOCK_STATE_PARTLY:      Final = "PARTLY_LOCKED"
VEHICLE_LOCK_STATE_UNLOCKED:    Final = "UNLOCKED"

ZONE_LIGHTS_VALUE_ALL_ON:       Final = "0"
ZONE_LIGHTS_VALUE_FRONT:        Final = "1"
ZONE_LIGHTS_VALUE_REAR:         Final = "2"
ZONE_LIGHTS_VALUE_DRIVER:       Final = "3"
ZONE_LIGHTS_VALUE_PASSENGER:    Final = "4"
ZONE_LIGHTS_VALUE_OFF:          Final = "off"
ZONE_LIGHTS_OPTIONS: Final = [ZONE_LIGHTS_VALUE_ALL_ON, ZONE_LIGHTS_VALUE_FRONT, ZONE_LIGHTS_VALUE_REAR,
                              ZONE_LIGHTS_VALUE_DRIVER, ZONE_LIGHTS_VALUE_PASSENGER, ZONE_LIGHTS_VALUE_OFF]

class HONK_AND_FLASH(Enum):
    SHORT = 1
    DEFAULT = 3
    LONG = 5

XEVPLUGCHARGER_STATE_CONNECTED:     Final = "CONNECTED"
XEVPLUGCHARGER_STATE_DISCONNECTED:  Final = "DISCONNECTED"
XEVPLUGCHARGER_STATE_CHARGING:      Final = "CHARGING"      # this is from evcc code - I have not seen this in my data yet
XEVPLUGCHARGER_STATE_CHARGINGAC:    Final = "CHARGINGAC"    # this is from evcc code - I have not seen this in my data yet
XEVPLUGCHARGER_STATES:              Final = [XEVPLUGCHARGER_STATE_CONNECTED, XEVPLUGCHARGER_STATE_DISCONNECTED,
                                             XEVPLUGCHARGER_STATE_CHARGING, XEVPLUGCHARGER_STATE_CHARGINGAC]

XEVBATTERYCHARGEDISPLAY_STATE_NOT_READY:    Final = "NOT_READY"
XEVBATTERYCHARGEDISPLAY_STATE_SCHEDULED:    Final = "SCHEDULED"
XEVBATTERYCHARGEDISPLAY_STATE_PAUSED:       Final = "PAUSED"
XEVBATTERYCHARGEDISPLAY_STATE_IN_PROGRESS:  Final = "IN_PROGRESS"
XEVBATTERYCHARGEDISPLAY_STATE_STOPPED:      Final = "STOPPED"
XEVBATTERYCHARGEDISPLAY_STATE_FAULT:        Final = "FAULT"
XEVBATTERYCHARGEDISPLAY_STATION_NOT_DETECTED: Final = "STATION_NOT_DETECTED"

XEVBATTERYCHARGEDISPLAY_STATES:             Final = [XEVBATTERYCHARGEDISPLAY_STATE_NOT_READY, XEVBATTERYCHARGEDISPLAY_STATE_SCHEDULED,
                                                     XEVBATTERYCHARGEDISPLAY_STATE_PAUSED, XEVBATTERYCHARGEDISPLAY_STATE_IN_PROGRESS,
                                                     XEVBATTERYCHARGEDISPLAY_STATE_STOPPED, XEVBATTERYCHARGEDISPLAY_STATE_FAULT,
                                                     XEVBATTERYCHARGEDISPLAY_STATION_NOT_DETECTED]

DAYS_MAP = {
    "MONDAY":   0,
    "TUESDAY":  1,
    "WEDNESDAY":2,
    "THURSDAY": 3,
    "FRIDAY":   4,
    "SATURDAY": 5,
    "SUNDAY":   6,
}

TRANSLATIONS: Final = {
    "de":{
        "account": "Konto",
        "coord_null_data": "Es konnten keine Daten abgerufen werden. Bitte prüfe Dein Home Assistant System Protokoll auf mögliche Fehlermeldungen der Integration.",
        "coord_no_vehicle_data": "Es konnten keine Daten zu Deinem konfigurierten Fahrzeug abgerufen werden. Bitte prüfe Dein Home Assistant System Protokoll auf mögliche Fehlermeldungen der Integration."
    },
    "en": {
        "account": "Account",
        "coord_null_data": "Coordinator could not provided any data. Please check your Home Assistant system log for possible error messages.",
        "coord_no_vehicle_data": "Coordinator could not fetch essential information from your configured vehicle. Please check your Home Assistant system log for possible error messages."
    }
}
