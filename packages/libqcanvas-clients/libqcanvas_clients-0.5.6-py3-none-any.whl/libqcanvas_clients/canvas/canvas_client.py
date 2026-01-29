import logging
from typing import Any, Optional, override

import gql
import httpx
from gql.client import DocumentNode as GraphQLQuery
from graphql import ExecutionResult
from httpx import URL, Cookies, Request, Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from libqcanvas_clients.canvas.canvas_authenticator import CanvasAuthenticator
from libqcanvas_clients.canvas.canvas_client_config import CanvasClientConfig
from libqcanvas_clients.canvas.canvas_types import (
    DiscussionTopicHeader,
    LegacyPage,
    MediaObject,
    RemoteFile,
)
from libqcanvas_clients.canvas.canvas_unauthenticated_detector_hook import (
    CanvasUnauthenticatedDetectorHook,
)
from libqcanvas_clients.util.add_cookies_to_request_hook import AddCookiesToRequestHook
from libqcanvas_clients.util.external_client_httpx_transport import (
    ExternalClientHTTPXTransport,
)
from libqcanvas_clients.util.json_util import check_status_and_parse_json
from libqcanvas_clients.util.request_exceptions import (
    ConfigInvalidError,
    RatelimitedError,
)


class CanvasClient:
    _logger = logging.getLogger(__name__)

    def __init__(
        self,
        client_config: CanvasClientConfig,
        max_concurrent_operations: int = 20,
        gql_timeout: float = 120,
        httpx_timeout: float = 120,
        client: Any = None,
    ):
        self._client_config = client_config
        self._client = client or httpx.AsyncClient(
            timeout=httpx_timeout,
            limits=httpx.Limits(max_connections=max_concurrent_operations),
            http2=True,
        )
        self._authentication_controller = CanvasAuthenticator(
            self._client, self._client_config
        )
        self._gql_timeout = gql_timeout
        self._gql_client = gql.Client(
            transport=_CanvasTransport(
                client=self._client,
                url=self._client_config.get_endpoint("api/graphql"),
                headers=self._client_config.get_authorization_header(),
            ),
            execute_timeout=self._gql_timeout,
        )

        self._add_cookie_request_hook(self._client)
        self._add_authentication_detector_hook(self._client)

    def _add_cookie_request_hook(self, client: httpx.AsyncClient) -> None:
        client.event_hooks["request"].append(
            AddCookiesToRequestHook(self._client.cookies.jar)
        )

    def _add_authentication_detector_hook(self, client: httpx.AsyncClient) -> None:
        client.event_hooks["response"].append(
            CanvasUnauthenticatedDetectorHook(self._client_config.host)
        )

    @retry(
        wait=wait_exponential_jitter(initial=0.5, exp_base=1.2, max=10),
        retry=retry_if_exception_type(RatelimitedError),
        stop=stop_after_attempt(8),
    )
    async def graphql_query(
        self,
        query: GraphQLQuery | str,
        query_variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if query_variables is None:
            query_variables = {}

        if not isinstance(query, GraphQLQuery):
            query = gql.gql(query)

        return await self._gql_client.execute_async(
            document=query, variable_values=query_variables
        )

    async def get_temporary_session_url(self) -> str:
        return await self._authentication_controller.request_legacy_authentication_url()

    async def get_current_user_id(self) -> str:
        self._logger.debug("Fetching current user id")
        response = await self._execute_request("api/v1/users/self/")
        return str(check_status_and_parse_json(response)["id"])

    async def get_announcements(self, course_id: str) -> list[DiscussionTopicHeader]:
        self._logger.debug("Fetching announcements for %s", course_id)
        response = await self._execute_request(
            f"api/v1/courses/{course_id}/discussion_topics?only_announcements=true&per_page=999999999999"
        )
        return self._convert_announcements(course_id, response)

    @staticmethod
    def _convert_announcements(
        course_id: str, response: httpx.Response
    ) -> list[DiscussionTopicHeader]:
        # course_id is added to the items for convenience
        return [
            DiscussionTopicHeader(**item, course_id=course_id)
            for item in check_status_and_parse_json(response)
        ]

    async def get_page(self, page_id: str | int, course_id: str | int) -> LegacyPage:
        self._logger.debug(
            "Fetching page content for course %s / page %s", course_id, page_id
        )
        response = await self._execute_request(
            f"api/v1/courses/{course_id}/pages/{page_id}"
        )
        return LegacyPage(**check_status_and_parse_json(response))

    async def get_file(self, file_id: str | int, course_id: str | int) -> RemoteFile:
        self._logger.debug("Fetching file for course %s / file %s", course_id, file_id)
        response = await self._execute_request(
            f"api/v1/courses/{course_id}/files/{file_id}"
        )
        return RemoteFile(**check_status_and_parse_json(response))

    async def get_file_download_stream(self, url: str | URL) -> Response:
        """
        Gets a download stream for a file from canvas. The response is a stream and must be closed with `close()` or `aclose()`
        :param url: The url of the file
        :returns: The response as a stream
        """

        return await self._execute_request(
            endpoint_path=url, stream=True, follow_redirects=True
        )

    async def get_media_object(self, id: str) -> MediaObject:
        self._logger.debug("Fetching media object %s", id)
        response = await self._execute_request(f"media_objects/{id}/info")
        return MediaObject(**check_status_and_parse_json(response))

    async def authenticate_panopto(self, authentication_url: str | URL) -> Response:
        request = self._client.build_request(
            method="GET",
            url=authentication_url,
        )

        return await self._send_with_ratelimit_retry(request, follow_redirects=True)

    async def make_generic_request(
        self, request: Request, follow_redirects: Optional[bool] = None
    ) -> Response:
        """
        This function is only here because of panopto's horrid LTI crap. Avoid using it for anything else.
        """

        self._logger.debug("Making generic request %s", request)

        if await self._is_request_for_canvas(request):
            request.headers.update(self._client_config.get_authorization_header())

        return await self._send_with_ratelimit_retry(
            request, follow_redirects=follow_redirects
        )

    async def _is_request_for_canvas(self, request: httpx.Request) -> bool:
        return request.url.host == self._client_config.host

    async def _execute_request(
        self,
        endpoint_path: str | URL,
        method: str = "GET",
        stream: bool = False,
        follow_redirects: bool = False,
    ) -> Response:
        request = self._client.build_request(
            method=method,
            url=self._client_config.get_endpoint(endpoint_path),
            headers=self._client_config.get_authorization_header(),
        )

        return await self._send_with_ratelimit_retry(
            request=request, stream=stream, follow_redirects=follow_redirects
        )

    @retry(
        wait=wait_exponential_jitter(initial=0.5, exp_base=1.2, max=10),
        retry=retry_if_exception_type(RatelimitedError),
        stop=stop_after_attempt(8),
    )
    async def _send_with_ratelimit_retry(
        self,
        request: Request,
        follow_redirects: Optional[bool] = None,
        stream: bool = False,
    ) -> Response:
        response = await self._authentication_controller.send_and_authenticate(
            request=request, follow_redirects=follow_redirects, stream=stream
        )

        _detect_ratelimit_and_raise(response)

        return response

    @property
    def cookies(self) -> Cookies:
        return self._client.cookies

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    async def verify_config(config: CanvasClientConfig) -> None:
        """

        :param config: The config to verify
        :raise ConfigInvalidError: If the url or api key is invalid
        """

        try:
            async with httpx.AsyncClient(http2=True) as client:
                # api/v1/accounts should return very little data, so it's a quick way to verify we are authenticated
                response = await client.get(
                    url=config.get_endpoint("api/v1/accounts"),
                    headers=config.get_authorization_header(),
                    timeout=10,
                )

            response.raise_for_status()
        except httpx.ConnectError as e:
            raise ConfigInvalidError("URL is invalid.") from e
        except httpx.HTTPStatusError as e:
            raise ConfigInvalidError("API token is invalid.") from e


class _CanvasTransport(ExternalClientHTTPXTransport):
    @override
    def _prepare_result(self, response: httpx.Response) -> ExecutionResult:
        _detect_ratelimit_and_raise(response)

        return super()._prepare_result(response)


def _detect_ratelimit_and_raise(response: Response) -> None:
    # Who the FUCK decided to use 403 instead of 429?? With this stupid message??
    # And the newline at the end for some fucking reason is the cherry on top...
    if (
        response.status_code == 403
        and response.text == "403 Forbidden (Rate Limit Exceeded)\n"
        or response.status_code == 429
    ):
        raise RatelimitedError()
