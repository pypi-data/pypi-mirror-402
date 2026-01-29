"""Channel extractor for YouTube channels."""

from typing import List

from yt_grabber.extractors.base import BaseExtractor


class ChannelExtractor(BaseExtractor):
    """Extracts video URLs from YouTube channels (regular videos only)."""

    def get_source_type(self) -> str:
        return "channel"

    def normalize_url(self, url_input: str) -> str:
        """Normalize channel input to full URL with /videos tab.

        Args:
            url_input: Channel URL, @handle, or channel ID

        Returns:
            Full YouTube channel URL with /videos suffix
        """
        # If it's already a full URL
        if url_input.startswith("http://") or url_input.startswith("https://"):
            url = url_input
            # Ensure it has /videos suffix to get only regular videos
            if not url.endswith("/videos"):
                url = url.rstrip("/") + "/videos"
            return url

        # If it's a @handle
        if url_input.startswith("@"):
            return f"https://www.youtube.com/{url_input}/videos"

        # If it's a channel ID (starts with UC typically)
        return f"https://www.youtube.com/channel/{url_input}/videos"

    def transform_urls(self, urls: List[str]) -> List[str]:
        """Reverse URL list to get oldest videos first.

        Args:
            urls: List of video URLs (newest first from yt-dlp)

        Returns:
            Reversed list (oldest first)
        """
        return list(reversed(urls))
