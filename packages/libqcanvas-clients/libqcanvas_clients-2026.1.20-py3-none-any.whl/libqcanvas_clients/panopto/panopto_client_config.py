from httpx import URL

from libqcanvas_clients.util.url_converter import ensure_is_url


class PanoptoClientConfig:
    def __init__(self, panopto_url: str | URL):
        self._panopto_url = ensure_is_url(panopto_url)

    def get_endpoint(self, path: URL | str) -> URL:
        return self._panopto_url.join(path)

    @property
    def host(self) -> str:
        return self._panopto_url.host
