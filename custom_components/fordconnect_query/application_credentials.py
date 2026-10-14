import datetime
import logging
import secrets
import time
import jwt

from typing import Final

from aiohttp import ClientError
from yarl import URL

import homeassistant.helpers.config_entry_oauth2_flow as oauth2_flow
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    AuthImplementation,
    ClientCredential,
)
from homeassistant.exceptions import OAuth2TokenRequestReauthError
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

    async def _async_refresh_token(self, token: dict) -> dict:
        """Refresh the token and inspect the id_token if present."""
        _LOGGER.debug(f"_async_refresh_token(): called...")

        # Call the parent refresh method to fetch the new token payload from the server
        new_token = await super()._async_refresh_token(token)

        # Check if an id_token was returned in the refresh response
        if id_token := new_token.get("id_token"):
            try:
                # Decode the JWT payload without signature verification
                # (or with verification if you have the public keys configured)
                payload = jwt.decode(id_token, options={"verify_signature": False})

                # Locate the auth_time claim (Unix timestamp in seconds)
                if auth_time := payload.get("auth_time"):
                    auth_date = datetime.datetime.fromtimestamp(auth_time)
                    expire_date = datetime.datetime.fromtimestamp(auth_time + 31536000)
                    _LOGGER.debug(f"_async_refresh_token(): decoded the id_token successfully. Initial authentication date: {auth_date.strftime("%Y-%m-%dT%H:%M:%SZ")} | will expire: {expire_date.strftime("%Y-%m-%dT%H:%M:%SZ")}")
                    # 1 YEAR     - 1 WEEK
                    # 31,536,000 - 604,800 = 30,931,200
                    if time.monotonic() >  + auth_time + 30931200:
                        _LOGGER.info(f"_async_refresh_token(): we must invalidate current token!")
                        _LOGGER.warning(f"FordConnect Query requires RE-AUTH via the User via a fresh login @ Ford Website [AuthTime will/has expired @ {expire_date.strftime("%Y-%m-%dT%H:%M:%SZ")}]")
                        # This tells Home Assistant to trigger the reauth flow
                        raise OAuth2TokenRequestReauthError("Authentication session expired (stale auth_time)")

            except OAuth2TokenRequestReauthError:
                # Re-raise the reauth error so Home Assistant captures it properly
                raise

            except Exception as err:
                _LOGGER.error(f"_async_refresh_token(): Failed to decode id_token from refresh response: {type(err).__name__} - {err}")

        _LOGGER.debug(f"_async_refresh_token(): completed")
        return new_token

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
