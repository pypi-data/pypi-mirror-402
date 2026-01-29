from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RemoteFile(BaseModel):
    id: int
    uuid: str
    display_name: str
    filename: str
    url: str
    size: int
    locked: bool
    hidden: bool
    hidden_for_user: bool
    locked_for_user: bool


class LockInfo(BaseModel):
    lock_at: Optional[datetime] = Field(default=None)
    unlock_at: Optional[datetime] = Field(default=None)


class LegacyPage(BaseModel):
    published: bool
    locked_for_user: bool
    lock_info: Optional[LockInfo] = Field(default=None)
    body: Optional[str] = Field(default=None)


class DiscussionTopicHeader(BaseModel):
    id: int
    title: str
    created_at: datetime
    private_delayed_post_at: Optional[datetime] = Field(alias="delayed_post_at")
    private_posted_at: Optional[datetime] = Field(alias="posted_at")
    position: int
    user_name: Optional[str]
    user_can_see_posts: bool
    read_state: str
    unread_count: int
    subscribed: bool
    attachments: List[RemoteFile]
    published: bool
    html_url: str
    url: str
    pinned: bool
    message: str
    is_announcement: bool
    lock_at: Optional[datetime]
    locked_for_user: bool
    # This is added manually, not returned from canvas API
    course_id: str

    @property
    def posted_at(self) -> datetime:
        return self.private_posted_at or self.private_delayed_post_at


class MediaSource(BaseModel):
    is_original: str = Field(..., alias="isOriginal")
    bitrate: str
    url: str
    file_ext: str = Field(..., alias="fileExt")
    size: str


class MediaObject(BaseModel):
    title: str
    media_sources: list[MediaSource]
