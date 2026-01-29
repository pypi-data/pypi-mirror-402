import logging

from httpx import Response

from libqcanvas_clients.util.authenticator import AUTHENTICATION_REQUIRED_RESPONSE_CODE

_logger = logging.getLogger(__name__)


class PanoptoUnauthenticatedDetectorHook:
    def __init__(self, panopto_host: str):
        self.panopto_host = panopto_host

    async def __call__(self, *args, **kwargs) -> None:
        response: Response = args[0]

        assert isinstance(response, Response)

        if response.url.host != self.panopto_host:
            return

        auth_cookie = ".ASPXAUTH"
        if not response.is_server_error and not response.is_redirect:
            no_auth_cookie = auth_cookie not in response.cookies.keys()
            if no_auth_cookie or response.cookies.get(auth_cookie) == "":
                if no_auth_cookie:
                    reason = "auth cookie missing"
                else:
                    reason = "auth cookie empty"

                _logger.info("Panopto request was unauthorised because %s", reason)
                response.status_code = AUTHENTICATION_REQUIRED_RESPONSE_CODE
