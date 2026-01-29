from http.cookiejar import CookieJar

from httpx import Request


class AddCookiesToRequestHook:
    def __init__(self, cookie_jar: CookieJar):
        self._cookie_jar = cookie_jar

    async def __call__(self, *args, **kwargs) -> None:
        request: Request = args[0]
        request.headers["cookie"] = self._build_cookie_header(request.url.host)

    def _build_cookie_header(self, domain: str) -> str:
        return ";".join(
            [
                f"{cookie.name}={cookie.value}"
                for cookie in self._cookie_jar
                if cookie.domain == domain
            ]
        )
