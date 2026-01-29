from dataclasses import dataclass, field
from typing import Optional

from yt_grabber.playlist_header import HeaderMetadata


@dataclass
class Video:
    """Represents a video entry in a playlist."""

    url: str
    downloaded: bool = False
    added: bool = False
    removed: bool = False


@dataclass
class Playlist:
    """Represents a complete playlist with header and videos."""

    header: Optional[HeaderMetadata]
    videos: list[Video]


@dataclass
class HeaderChange:
    """Represents a change in header field."""

    field: str
    old_value: str
    new_value: str


@dataclass
class SyncResult:
    """Result of syncing a playlist with its source."""

    added_urls: list[str] = field(default_factory=list)
    removed_urls: list[str] = field(default_factory=list)
    header_changes: list[HeaderChange] = field(default_factory=list)
