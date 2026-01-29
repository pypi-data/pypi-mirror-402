import logging

from httpx import URL

from libqcanvas_clients.panopto.panopto_types import (
    AlternativeSession,
    DeliveryInfo,
    SessionList,
)

_logger = logging.getLogger(__name__)


class FakePanoptoClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_viewer_url(self, video_id: str) -> URL:
        raise NotImplementedError()

    async def get_session_info(self, session_id: str) -> AlternativeSession:
        raise NotImplementedError()

    async def get_folders(self) -> list:
        return []

    async def get_folder_sessions(self, folder_id: str) -> SessionList:
        raise NotImplementedError()

    async def get_delivery_info(self, delivery_id: str) -> DeliveryInfo:
        raise NotImplementedError()

    async def force_authenticate(self) -> None:
        pass

    @property
    def cookies_for_download(self) -> list:
        raise NotImplementedError()
