import logging
import secrets
from typing import Final

from aiohttp import ClientError
from yarl import URL

import homeassistant.helpers.config_entry_oauth2_flow as oauth2_flow
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    AuthImplementation,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2Implementation,
)
from .const import (
    DOMAIN,
    FORD_AUTHORIZE_URL,
    FORD_TOKEN_URL
)

_LOGGER = logging.getLogger(__name__)

STATE_LOOKUP_MAP:Final = "secure_state-to-flow_id-map"

class FordConQOAuth2Implementation(LocalOAuth2Implementation):

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate a short state for Ford and the redirect service."""
        # Generate a 16-character hex string (8 bytes) to meet the 16-byte limit
        secure_state = secrets.token_hex(8)

        # We must manually register the state with Home Assistant's OAuth2 flow manager
        # This is how HA knows which flow_id to resume when the callback happens.

        # The standard way HA handles this is via a signed JWT, but since we have
        # a strict 16-byte limit, we use a simple lookup map in hass.data
        self.hass.data.setdefault(DOMAIN, {}).setdefault(STATE_LOOKUP_MAP, {})[secure_state] = flow_id

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": secure_state,
            #"scope": "openid offline_access" # Adjust scopes as needed for Ford
        }
        url_str = str(URL(self.authorize_url).with_query(params))
        _LOGGER.info(f"async_generate_authorize_url(): create final URL {url_str}")
        return url_str

    async def async_resolve_external_data(self, external_data: dict) -> dict:
        _LOGGER.info(f"async_resolve_external_data(): called will request now the final token data with the received code")
        request_data = {
            "code": external_data.get("code"),
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        try:
            response = await self._token_request(request_data)
            _LOGGER.info(f"async_resolve_external_data(): got _token_request response: {response}")
            return response
        except ClientError as err:
            _LOGGER.error(f"async_resolve_external_data(): failed to get token: {err}")
            return {}

# To make the standard /auth/external/callback work with our short state,
# we wrap the decoder.
_ORIGINAL_DECODE = oauth2_flow._decode_jwt

def _patched_decode_jwt(hass, state_str):
    # If the state exists in our Ford lookup map, return a fake JWT-like dict
    if flow_id := hass.data.get(DOMAIN, {}).get(STATE_LOOKUP_MAP, {}).get(state_str):
        _LOGGER.info(f"_patched_decode_jwt(): found flow_id for state {state_str}: {flow_id}")
        return {"flow_id": flow_id}

    # Otherwise, fall back to the original HA logic
    return _ORIGINAL_DECODE(hass, state_str)

# Apply the patch
oauth2_flow._decode_jwt = _patched_decode_jwt


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    return AuthorizationServer(
        authorize_url=FORD_AUTHORIZE_URL,
        token_url=FORD_TOKEN_URL,
    )

async def async_get_auth_implementation(hass: HomeAssistant, auth_domain: str, credential: ClientCredential) -> AuthImplementation:
    server = await async_get_authorization_server(hass)
    return FordConQOAuth2Implementation(hass, auth_domain, credential.client_id, credential.client_secret, server.authorize_url, server.token_url)
