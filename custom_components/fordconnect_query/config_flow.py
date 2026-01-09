import logging
from typing import Any

import aiohttp
from aiohttp import web

from custom_components.fordconnect_query.const import (
    DOMAIN,
    CONFIG_VERSION,
    CONFIG_MINOR_VERSION,
    CALLBACK_URL,
    CALLBACK_NAME,
    STATE_LOOKUP_MAP,
    FORD_GARAGE_URL,
    CONF_VIN,
    CONF_GARAGE_DATA
)
from homeassistant.components import http
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_create_clientsession

_LOGGER = logging.getLogger(__name__)

class FordConQOAuthCallbackView(http.HomeAssistantView):
    requires_auth = False
    url = CALLBACK_URL
    name = CALLBACK_NAME

    async def get(self, request: web.Request) -> web.Response:
        _LOGGER.debug(f"FordConQOAuthCallbackView.get(): called")
        hass = request.app["hass"]

        # this is our secure_state as it was created by application_credentials.async_generate_authorize_url()
        secure_state = request.query.get("state")
        code = request.query.get("code")

        if not secure_state or not code:
            _LOGGER.error(f"No state or code present in callback: {request.query}")
            return web.Response(text="Missing 'code' or 'state' in request", status=400)

        # now we must find our flow_id and continue it...
        the_flow_id = hass.data.setdefault(DOMAIN, {}).setdefault(STATE_LOOKUP_MAP, {}).pop(secure_state, None)
        _LOGGER.debug(f"FordConQOAuthCallbackView.get(): got flowId: '{the_flow_id}' so we can continue the flow...")

        try:
            await hass.config_entries.flow.async_configure(flow_id=the_flow_id, user_input={"code": code, "state": secure_state})
        except Exception as err:
            _LOGGER.error(f"FordConQOAuthCallbackView.get(): Error while try to continue the flow {the_flow_id}: {type(err).__name__} - {err}")
            return web.Response(text=f"Flow execution failed: {err}", status=500)

        return web.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>Authentication successful! This window can now be closed.",
        )

class FordConQConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    DOMAIN = DOMAIN
    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    async def async_oauth_create_entry(self, data):
        _LOGGER.debug(f"async_oauth_create_entry() we can finally create the entry, since oAuth has returned a token")
        access_token = data.get(CONF_TOKEN, {}).get(CONF_ACCESS_TOKEN, None)
        if access_token is not None:
            garage_data = await self.get_garage(async_create_clientsession(self.hass), access_token)

            # data = {'vin': 'WF0TK3R7ABCD01234', 'vehicleType': '2023 Mustang Mach-E', 'color': 'GRABBER BLUE METALLIC',
            #         'modelName': 'Mustang Mach-E', 'modelCode': 'VLGW', 'modelYear': '2023', 'tcuEnabled': 1,
            #         'make': 'Ford', 'ngSdnManaged': 1, 'vehicleAuthorizationIndicator': 1, 'engineType': 'BEV'}

            if "vin" in garage_data:
                entry_data = {
                    **data,
                    CONF_VIN: garage_data["vin"],
                    CONF_NAME: garage_data.get("vehicleType", "Ford Vehicle"),
                    CONF_GARAGE_DATA: garage_data
                }
                return self.async_create_entry(title="Ford Query integration", data=entry_data)
            else:
                _LOGGER.error("async_oauth_create_entry(): No VIN received from oAuth provider")
                return self.async_abort(reason="No VIN received from oAuth provider")
        else:
            _LOGGER.error("async_oauth_create_entry(): No access token received from oAuth provider")
            return self.async_abort(reason="No access_token from oAuth provider")

    async def get_garage(self, session, access_token:str):
        res = await session.get(
            FORD_GARAGE_URL,
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
        if "fordconnect_query_callback_registered" not in self.hass.data.setdefault(DOMAIN, {}):
            _LOGGER.info("async_step_user(): Register FordConQOAuth Callback View")
            self.hass.http.register_view(FordConQOAuthCallbackView())
            self.hass.data[DOMAIN]["fordconnect_query_callback_registered"] = True

        return await super().async_step_user(user_input)

    async def async_step_reauth(self, entry_data):
        """Perform reauth upon migration of old entries."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        reauth_entry = self._get_reauth_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={"account": reauth_entry.data["id"]},
                errors={},
            )

        return await self.async_step_pick_implementation(
            user_input={"implementation": reauth_entry.data["auth_implementation"]}
        )
