import logging
import secrets

from yarl import URL

from custom_components.fordconnect_query.const import (
    DOMAIN,
    CALLBACK_URL,
    STATE_LOOKUP_MAP,
    FORD_AUTHORIZE_URL,
    FORD_TOKEN_URL
)
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    AuthImplementation,
    ClientCredential,
)
from homeassistant.components.http import current_request
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

_LOGGER = logging.getLogger(__name__)

class FordConQOAuth2Implementation(LocalOAuth2Implementation):

    @property
    def redirect_uri(self) -> str:
        # since when the user just uses a hostname or just localhost, we must
        # use this for the redirect!
        if (req := current_request.get()) is not None:
            protocol = "https" if req.secure else "http"
            host = req.host
            return f"{protocol}://{host}{CALLBACK_URL}"

        # just as fallback...
        from homeassistant.helpers.network import get_url
        return f"{get_url(self.hass)}{CALLBACK_URL}"

    async def async_generate_authorize_url(self, flow_id: str) -> str:

        secure_state = secrets.token_urlsafe(16)
        # storing our flow_id in a dict to be able to retrieve it later...
        self.hass.data.setdefault(DOMAIN, {}).setdefault(STATE_LOOKUP_MAP, {})[secure_state] = flow_id

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": secure_state
        }
        url_str = str(URL(self.authorize_url).with_query(params))
        _LOGGER.debug(f"async_generate_authorize_url(): create final URL: {url_str}")
        return url_str

    async def async_resolve_external_data(self, external_data: dict) -> dict:
        _LOGGER.info(f"async_resolve_external_data(): called will request now the final token data with the received code")
        request_data = {
            "code": external_data.get("code"),
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        data = await self._token_request(request_data)
        if data is not None:
            _LOGGER.info(f"async_resolve_external_data(): got token response with {len(data)} entries")
            return data
        else:
            _LOGGER.error(f"async_resolve_external_data(): No token data received from oAuth provider for {external_data}")
            return None

async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    return AuthorizationServer(
        authorize_url=FORD_AUTHORIZE_URL,
        token_url=FORD_TOKEN_URL,
    )

async def async_get_auth_implementation(hass: HomeAssistant, auth_domain: str, credential: ClientCredential) -> AuthImplementation:
    server = await async_get_authorization_server(hass)
    return FordConQOAuth2Implementation(hass, auth_domain, credential.client_id, credential.client_secret, server.authorize_url, server.token_url)
