import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from asynctaskpool import AsyncTaskPool
from asynctaskpool.task_failed_exception import TaskFailedError
from httpx import Response

from .request_exceptions import AuthenticationFailedError

_authentication_task_id = "authentication"
_logger = logging.getLogger(__name__)

AUTHENTICATION_REQUIRED_RESPONSE_CODE = 499


class Authenticator(ABC):
    max_retries = 3

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        # This task pool only ever has 1 specific task submitted to it - the authentication task.
        self._auth_taskpool = AsyncTaskPool(restart_if_finished=True)

    async def send_and_authenticate(
        self,
        request: httpx.Request,
        stream: bool = False,
        follow_redirects: Optional[bool] = None,
    ) -> httpx.Response:
        """
        Sends a request, or authenticates if the response requires it, then resends the request.
        :param request:
        :param stream:
        :param follow_redirects:
        :return:
        """
        await self._wait_for_authentication_to_finish()

        _logger.debug("Making request %s", request)

        options = dict(
            stream=stream,
            follow_redirects=follow_redirects or self._client.follow_redirects,
        )
        response = await self._client.send(request, **options)
        retry_count = 0

        while self._is_authentication_required(response) and self._should_keep_retrying(
            retry_count
        ):
            retry_count += 1

            _logger.info(
                "Authentication is required (try %s/%s)", retry_count, self.max_retries
            )

            try:
                await self._authenticate_or_wait()
            except AuthenticationFailedError:
                continue

            response = await self._client.send(request, **options)
        if not self._should_keep_retrying(
            retry_count
        ) and self._is_authentication_required(response):
            _logger.fatal("Gave up trying to authenticate")
            raise AuthenticationFailedError(
                f"Could not authenticate the client in under {self.max_retries} tries"
            )

        return response

    async def _wait_for_authentication_to_finish(self) -> None:
        try:
            await self._auth_taskpool.wait_for_task_completion(_authentication_task_id)
        except TaskFailedError:
            pass

    def _should_keep_retrying(self, retry_count: int) -> bool:
        return retry_count < self.max_retries

    async def force_authenticate(self) -> None:
        await self._authenticate_or_wait()

    async def _authenticate_or_wait(self) -> None:
        try:
            await self._auth_taskpool.submit(
                _authentication_task_id, self._authenticate()
            )
        except TaskFailedError as e:
            _logger.error("Authentication failed", exc_info=e)
            raise AuthenticationFailedError("Authentication failed") from e

    @staticmethod
    def _is_authentication_required(response: Response) -> bool:
        return response.status_code == AUTHENTICATION_REQUIRED_RESPONSE_CODE

    @abstractmethod
    async def _authenticate(self) -> None: ...
