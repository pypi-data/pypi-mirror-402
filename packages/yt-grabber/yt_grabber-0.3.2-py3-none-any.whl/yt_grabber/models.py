from dataclasses import dataclass, field

from yt_grabber.playlist_header import HeaderMetadata


class DownloadError(Exception):
    """Exception raised when video or playlist download fails."""

    def __init__(self, message: str, url: str | None = None):
        """Initialize download error.

        Args:
            message: Error message
            url: Optional URL of the video that failed
        """
        super().__init__(message)
        self.url = url


class NonRetryableError(Exception):
    """Exception raised when video download fails with a non-retryable error.

    Examples: age verification, login required, private video, etc.
    """

    pass


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

    header: HeaderMetadata | None
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
