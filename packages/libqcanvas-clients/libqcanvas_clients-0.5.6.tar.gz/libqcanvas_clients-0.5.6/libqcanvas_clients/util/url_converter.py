from httpx import URL


def ensure_is_url(url: URL | str) -> URL:
    return url if isinstance(url, URL) else URL(url)
