import logging
from http.cookiejar import Cookie

import httpx
from httpx import URL, Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from libqcanvas_clients.canvas.canvas_client import CanvasClient
from libqcanvas_clients.panopto.panopto_authenticator import PanoptoAuthenticator
from libqcanvas_clients.panopto.panopto_client_config import PanoptoClientConfig
from libqcanvas_clients.panopto.panopto_types import (
    AlternativeSession,
    DeliveryInfo,
    FolderInfo,
    SessionList,
)
from libqcanvas_clients.panopto.panopto_unauthenticated_detector_hook import (
    PanoptoUnauthenticatedDetectorHook,
)
from libqcanvas_clients.util.json_util import check_status_and_parse_json
from libqcanvas_clients.util.request_exceptions import (
    AuthenticationFailedError,
    ConfigInvalidError,
    RatelimitedError,
)


class PanoptoClient:
    _logger = logging.getLogger(__name__)

    def __init__(self, client_config: PanoptoClientConfig, canvas_client: CanvasClient):
        self._client_config = client_config
        self._canvas_client = canvas_client
        self._client = canvas_client._client
        self._authentication_controller = PanoptoAuthenticator(
            panopto_client_config=self._client_config, canvas_client=self._canvas_client
        )

        self._add_authentication_detector_hook(self._client)

    def _add_authentication_detector_hook(self, client: httpx.AsyncClient) -> None:
        client.event_hooks["response"].append(
            PanoptoUnauthenticatedDetectorHook(self._client_config.host)
        )

    def get_viewer_url(self, video_id: str) -> URL:
        return self._client_config.get_endpoint(
            f"Panopto/Pages/Viewer.aspx?id={video_id}"
        )

    async def get_session_info(self, session_id: str) -> AlternativeSession:
        response = await self._execute_request(f"Panopto/Api/Sessions/{session_id}")
        return AlternativeSession(**check_status_and_parse_json(response))

    async def get_folders(self) -> list[FolderInfo]:
        # I don't know what most of these parameters do. Just copied the url from the browser developer tools
        response = await self._execute_request(
            "Panopto/Api/Folders?"
            "parentId=null"
            "&folderSet=1"
            "&includeMyFolder=false"
            "&includePersonalFolders=true"
            "&page=0"
            "&sort=Depth"
            "&names[0]=SessionCount"
        )

        return [FolderInfo(**data) for data in check_status_and_parse_json(response)]

    async def get_folder_sessions(self, folder_id: str) -> SessionList:
        self._logger.debug("Fetching sessions for folder %s", folder_id)
        response = await self._execute_request(
            "Panopto/Services/Data.svc/GetSessions",
            json={"queryParameters": {"folderID": folder_id}},
            method="POST",
        )
        return SessionList(**check_status_and_parse_json(response)["d"])

    async def get_delivery_info(self, delivery_id: str) -> DeliveryInfo:
        response = await self._execute_request(
            "Panopto/Pages/Viewer/DeliveryInfo.aspx",
            data={"deliveryId": delivery_id, "responseType": "json"},
            method="POST",
        )
        return DeliveryInfo(**check_status_and_parse_json(response))

    @retry(
        wait=wait_exponential_jitter(initial=0.5, exp_base=1.2, max=10),
        retry=retry_if_exception_type(RatelimitedError),
        stop=stop_after_attempt(8),
    )
    async def _execute_request(
        self, endpoint_path: str | URL, method: str = "GET", **kwargs
    ) -> Response:
        request = self._client.build_request(
            method=method,
            url=self._client_config.get_endpoint(endpoint_path),
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            },
            **kwargs,
        )

        self._logger.debug("Making request %s", request)
        response = await self._authentication_controller.send_and_authenticate(request)

        if response.status_code == 429:
            raise RatelimitedError()

        return response

    async def force_authenticate(self) -> None:
        await self._authentication_controller.force_authenticate()

    @property
    def cookies_for_download(self) -> list[Cookie]:
        result: list[Cookie] = []
        # Yes I am accessing a private field, there is no better way to do it.
        # I don't understand why this isn't exposed via a function like `cookies_for_domain(domain)` anyway
        cookies = self._client.cookies.jar._cookies
        domain = self._client_config.host

        if domain not in cookies:
            return result

        for group in cookies[domain].values():
            for cookie in group.values():
                result.append(cookie)

        return result

    @staticmethod
    async def verify_config(config: PanoptoClientConfig, client: CanvasClient) -> None:
        """

        :param config: The config to test
        :param client: The client to test with (used for doing the authentication)
        :raise ConfigInvalidError: If the config is invalid
        :raise Exception: If anything else went wrong
        :return:
        """
        try:
            authenticator = PanoptoAuthenticator(
                panopto_client_config=config, canvas_client=client
            )
            authenticator.max_retries = 1
            await authenticator.force_authenticate()

        except (httpx.HTTPStatusError, AuthenticationFailedError) as e:
            raise ConfigInvalidError(
                "Couldn't authenticate to panopto. Check that your account has been linked to canvas."
            ) from e
        except httpx.ConnectError as e:
            raise ConfigInvalidError("URL is incorrect.") from e
