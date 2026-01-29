"""Playlist extractor for YouTube playlists."""

from yt_grabber.extractors.base import BaseExtractor


class PlaylistExtractor(BaseExtractor):
    """Extracts video URLs from YouTube playlists."""

    def get_source_type(self) -> str:
        return "playlist"

    def normalize_url(self, url_input: str) -> str:
        """Normalize playlist input to full URL.

        Args:
            url_input: Playlist URL or ID

        Returns:
            Full YouTube playlist URL
        """
        # If it's already a full URL, return as is
        if url_input.startswith("http://") or url_input.startswith("https://"):
            return url_input

        # If it's just an ID, construct the URL
        return f"https://www.youtube.com/playlist?list={url_input}"
