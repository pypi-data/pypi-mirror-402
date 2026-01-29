import logging

from libqcanvas_clients.canvas.canvas_client import CanvasClient
from libqcanvas_clients.panopto.panopto_client_config import PanoptoClientConfig
from libqcanvas_clients.util.authenticator import Authenticator
from libqcanvas_clients.util.request_exceptions import AuthenticationFailedError

_logger = logging.getLogger(__name__)


class PanoptoAuthenticator(Authenticator):
    def __init__(
        self, panopto_client_config: PanoptoClientConfig, canvas_client: CanvasClient
    ):
        super().__init__(canvas_client._client)
        self.max_retries = 5
        self._panopto_client_config = panopto_client_config
        self._canvas_client = canvas_client

    async def _authenticate(self) -> None:
        _logger.info("Authenticating to panopto")

        response = await self._canvas_client.authenticate_panopto(
            self._panopto_client_config.get_endpoint(
                "Panopto/Pages/Auth/Login.aspx?instance=Canvas&AllowBounce=true"
            )
        )

        response.raise_for_status()
        _logger.debug("Got response from %s", response.url)

        if not response.url.path.endswith("Home.aspx"):
            _logger.error("Panopto authentication failed")
            raise AuthenticationFailedError(
                "Couldn't authenticate to panopto via canvas. Is your canvas account linked to panopto?"
            )
        else:
            _logger.info("Authentication complete")
