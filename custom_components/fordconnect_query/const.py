import logging
from typing import Final

_LOGGER = logging.getLogger(__name__)

DOMAIN: Final = "fordconnect_query"
NAME: Final = "FordConnect Query (for EU) integration for Home Assistant"
ISSUE_URL: Final = "https://github.com/marq24/ha-fordconnect-query/issues"

CONFIG_VERSION: Final = 1
CONFIG_MINOR_VERSION: Final = 0

CONF_VIN = "vin"
CONF_GARAGE_DATA = "garage"
CONF_TITLE = "config_title"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 30

FORD_BASE_URL: Final = "https://api.vehicle.ford.com"
FORD_AUTHORIZE_URL: Final = f"{FORD_BASE_URL}/fcon-public/v1/auth/init"
FORD_TOKEN_URL: Final     = f"{FORD_BASE_URL}/dah2vb2cprod.onmicrosoft.com/oauth2/v2.0/token?p=B2C_1A_FCON_AUTHORIZE"

FORD_FCON_QUERY_ENDPOINT: Final = "/fcon-query/v1"
FORD_FCON_QUERY_BASE_URL: Final = f"{FORD_BASE_URL}{FORD_FCON_QUERY_ENDPOINT}"

# the API Endpoint templates
FORD_GARAGE_TEMP: Final              = "{base_url}/garage"
FORD_TELEMETRY_TEMP: Final           = "{base_url}/telemetry"
FORD_VEH_HEALTH_TEMP: Final          = "{base_url}/vehicle-health/alerts"
FORD_WALLBOX_TEMP: Final             = "{base_url}/wallbox"
FORD_EV_DEPARTURE_TIMES_TEMP: Final  = "{base_url}/electric/departure-times"
FORD_EV_CHARGE_SCHEDULES_TEMP: Final = "{base_url}/electric/charge-schedules"
FORD_EV_SESSIONS_TEMP: Final         = "{base_url}/fccs?startDate={start}&endDate={end}"

TRANSLATIONS: Final = {
    "de": {
        "account": "Konto",
        "coord_null_data": "Es konnten keine Daten abgerufen werden. Bitte prüfe Dein Home Assistant System Protokoll auf mögliche Fehlermeldungen der Integration.",
        "coord_no_vehicle_data": "Es konnten keine Daten zu Deinem konfigurierten Fahrzeug abgerufen werden. Bitte prüfe Dein Home Assistant System Protokoll auf mögliche Fehlermeldungen der Integration."
    },
    "en": {
        "account": "Account",
        "coord_null_data": "Coordinator could not provided any data. Please check your Home Assistant system log for possible error messages.",
        "coord_no_vehicle_data": "Coordinator could not fetch essential information from your configured vehicle. Please check your Home Assistant system log for possible error messages."
    },
    "nl": {
        "account": "Account",
        "coord_null_data": "Coördinator kon geen gegevens leveren. Controleer uw Home Assistant-systeemlogboek op mogelijke foutmeldingen.",
        "coord_no_vehicle_data": "Coördinator kon essentiële informatie van uw geconfigureerde voertuig niet ophalen. Controleer uw Home Assistant-systeemlogboek op mogelijke foutmeldingen."
    }
}