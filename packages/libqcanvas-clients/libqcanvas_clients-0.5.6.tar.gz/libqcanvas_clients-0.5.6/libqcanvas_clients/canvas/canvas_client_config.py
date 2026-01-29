from httpx import URL

from libqcanvas_clients.util.url_converter import ensure_is_url


class CanvasClientConfig:
    def __init__(self, api_token: str, canvas_url: str | URL):
        self._api_token = api_token
        self._canvas_url = ensure_is_url(canvas_url)

    def get_authorization_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_token}"}

    def get_endpoint(self, path: URL | str) -> URL:
        return self._canvas_url.join(path)

    @property
    def host(self) -> str:
        return self._canvas_url.host
