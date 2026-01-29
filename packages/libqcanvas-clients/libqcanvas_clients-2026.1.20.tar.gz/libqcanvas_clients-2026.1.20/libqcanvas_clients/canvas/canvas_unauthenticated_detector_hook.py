from httpx import Response

from libqcanvas_clients.util.authenticator import AUTHENTICATION_REQUIRED_RESPONSE_CODE


class CanvasUnauthenticatedDetectorHook:
    def __init__(self, panopto_host: str):
        self.canvas_host = panopto_host

    async def __call__(self, *args, **kwargs):
        response: Response = args[0]

        assert isinstance(response, Response)

        if response.url.host != self.canvas_host:
            return

        # Canvas will silently redirect to the login page or give a 401 if we are not authenticated
        if response.url.path == "/login/canvas":  # or response.status_code == 401
            response.status_code = AUTHENTICATION_REQUIRED_RESPONSE_CODE
