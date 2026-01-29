import logging
from numbers import Number
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_TOKEN, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .const import (
    DOMAIN,
    CONFIG_VERSION,
    CONFIG_MINOR_VERSION,
    FORD_GARAGE_TEMP,
    FORD_FCON_QUERY_BASE_URL,
    CONF_VIN,
    CONF_TITLE,
    CONF_GARAGE_DATA,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .const_shared import (
    DEFAULT_PRESSURE_UNIT,
    PRESSURE_UNITS,
    CONF_PRESSURE_UNIT,
    CONF_LOG_TO_FILESYSTEM,
)

_LOGGER = logging.getLogger(__name__)
TITLE_MAP = "title_map"

class FordConQConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    DOMAIN = DOMAIN
    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    # we need to overwrite the async_step_creation to capture a possible 'abort' from the parent class
    async def async_step_creation(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        _LOGGER.info(f"async_step_creation(): called with user_input: {user_input}")
        response = await super().async_step_creation(user_input)
        if response.get("type", None) == FlowResultType.ABORT:
            _LOGGER.info(f"async_step_creation(): got an FlowResultType.ABORT response: {response}")
            reason = response.get("reason", "UNKNOWN reason")
            return self.async_abort(reason="oauth_error_final", description_placeholders={"error_info": reason})
        else:
            _LOGGER.info(f"async_step_creation(): got response: {response}")
            return response

    async def async_oauth_create_entry(self, data):
        _LOGGER.debug(f"async_oauth_create_entry() we can finally create the entry, since oAuth has returned a token")
        access_token = data.get(CONF_TOKEN, {}).get(CONF_ACCESS_TOKEN, None)
        if access_token is not None:
            garage_data = await self.get_garage(async_create_clientsession(self.hass), access_token)

            # data = {'vin': 'WF0TK3R7ABCD01234', 'vehicleType': '2023 Mustang Mach-E', 'color': 'GRABBER BLUE METALLIC',
            #         'modelName': 'Mustang Mach-E', 'modelCode': 'VLGW', 'modelYear': '2023', 'tcuEnabled': 1,
            #         'make': 'Ford', 'ngSdnManaged': 1, 'vehicleAuthorizationIndicator': 1, 'engineType': 'BEV'}

            if garage_data and "vin" in garage_data:
                entry_data = {
                    **data,
                    CONF_VIN: garage_data["vin"],
                    CONF_NAME: garage_data.get("vehicleType", "Ford Vehicle"),
                    CONF_GARAGE_DATA: garage_data
                }
                a_fallback_title = f"{garage_data.get('color', 'A FordConnect')} {garage_data.get('modelName', '')}".strip()
                a_title = self.hass.data.get(DOMAIN, {}).get(TITLE_MAP, {}).get(self.flow_id, a_fallback_title)
                return self.async_create_entry(title=a_title, data=entry_data)
            else:
                _LOGGER.error("async_oauth_create_entry(): No VIN received from oAuth provider")
                return self.async_abort(reason="No VIN received from oAuth provider")
        else:
            _LOGGER.error("async_oauth_create_entry(): No access token received from oAuth provider")
            return self.async_abort(reason="oauth_unauthorized")

    async def get_garage(self, session, access_token:str):
        res = await session.get(
            FORD_GARAGE_TEMP.format(base_url=FORD_FCON_QUERY_BASE_URL),
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            timeout= aiohttp.ClientTimeout(
                total=45,      # Total request timeout
                connect=30,    # Connection timeout
                sock_connect=30,
                sock_read=120   # Socket read timeout
            )
        )
        try:
            res.raise_for_status()
            data = await res.json()
            _LOGGER.debug(f"get_garage(): {data}")
            return data
        except BaseException as e:
            _LOGGER.error(f"get_garage(): caused {type(e).__name__} {e}")

    async def async_step_user(self, user_input=None):
        return await self.async_step_user_connect()

    async def async_step_user_connect(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # we store the title to use it later...
            self.hass.data.setdefault(DOMAIN, {}).setdefault(TITLE_MAP, {})[self.flow_id] = user_input[CONF_TITLE]
            # starting again with a plain entry
            return await super().async_step_user(None)

        return self.async_show_form(
            step_id="user_connect",
            data_schema=vol.Schema({
                vol.Required(CONF_TITLE, default="FordConnect Query"): str,
            }),
            description_placeholders={
                "repo": "https://github.com/marq24/ha-fordconnect-query",
                "github": "https://github.com/marq24"
            },
            errors=errors
            )


    async def async_step_reauth(self, entry_data):
        """Perform reauth upon migration of old entries."""
        return await self.async_step_reauth_confirm_connect()

    async def async_step_reauth_confirm_connect(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        reauth_entry = self._get_reauth_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm_connect",
                description_placeholders={
                    CONF_USERNAME: reauth_entry.data.get(CONF_VIN, "Unknown Vehicle"),
                    "repo": "https://github.com/marq24/ha-fordconnect-query"
                },
                errors={},
            )
        else:
            return await super().async_step_pick_implementation(None)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options' flow for this handler."""
        return FordConQOptionsFlowHandler(config_entry)


class FordConQOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if CONF_SCAN_INTERVAL in user_input and isinstance(user_input[CONF_SCAN_INTERVAL], Number):
                user_input[CONF_SCAN_INTERVAL] = max(int(user_input[CONF_SCAN_INTERVAL]), MIN_SCAN_INTERVAL)
            return self.async_create_entry(title="", data=user_input)

        options = {vol.Optional(CONF_PRESSURE_UNIT, default=self._options.get(CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT),): vol.In(PRESSURE_UNITS),
                   vol.Optional(CONF_LOG_TO_FILESYSTEM, default=self._options.get(CONF_LOG_TO_FILESYSTEM, False),): bool,
                   vol.Optional(CONF_SCAN_INTERVAL, default=self._options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL), ): int}
        return self.async_show_form(step_id="init", data_schema=vol.Schema(options), description_placeholders={"integration_name": "fordconnect_query"})
