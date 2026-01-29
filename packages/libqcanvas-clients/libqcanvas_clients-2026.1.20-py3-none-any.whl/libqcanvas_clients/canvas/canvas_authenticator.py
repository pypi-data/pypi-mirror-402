import json
import logging

import httpx
from httpx import Response

from libqcanvas_clients.canvas.canvas_client_config import CanvasClientConfig
from libqcanvas_clients.util.authenticator import Authenticator


class CanvasAuthenticator(Authenticator):
    _logger = logging.getLogger(__name__)

    def __init__(self, client: httpx.AsyncClient, client_config: CanvasClientConfig):
        super().__init__(client)
        self._canvas_client_config = client_config

    async def _authenticate(self) -> None:
        self._logger.info("Attempting authentication to canvas")

        legacy_authentication_url = await self.request_legacy_authentication_url()
        response = await self._client.get(legacy_authentication_url)

        if not response.is_redirect:
            self._logger.error("Authentication failed %s", response)
            raise RuntimeError("Authentication failed")
        else:
            self._logger.info("Authentication was successful")

    async def request_legacy_authentication_url(self) -> str:
        response = await self._client.get(
            url=self._canvas_client_config.get_endpoint("login/session_token"),
            headers=self._canvas_client_config.get_authorization_header(),
        )

        if response.is_success:
            return self._extract_legacy_authentication_url_from_response(response)
        else:
            self._logger.warning("Your API key may be incorrect")
            raise RuntimeError("Authentication failed, check your API key")

    def _extract_legacy_authentication_url_from_response(
        self, session_response: Response
    ) -> str:
        target_url = json.loads(session_response.text)["session_url"]

        self._logger.debug("Authenticating via %s", target_url)

        if target_url is None:
            self._logger.warning(
                "Session response body was malformed. Got: %s", session_response.text
            )
            raise ValueError("Session response body was malformed")
        else:
            return target_url
