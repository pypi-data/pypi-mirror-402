"""Playlist file management for tracking downloaded videos."""

from pathlib import Path
from typing import List

from loguru import logger

from yt_grabber.playlist_manager import build_playlist, parse_playlist


class PlaylistManager:
    """Manages reading and updating playlist files with download tracking."""

    def __init__(self, playlist_path: Path):
        """Initialize playlist manager.

        Args:
            playlist_path: Path to the playlist file
        """
        self.playlist_path = playlist_path

    def read_urls(self) -> List[str]:
        """Read undownloaded URLs from the playlist file.

        Returns:
            List of URLs that are not marked as downloaded and not removed

        Raises:
            FileNotFoundError: If playlist file does not exist
        """
        if not self.playlist_path.exists():
            raise FileNotFoundError(f"Playlist file not found: {self.playlist_path}")

        playlist = parse_playlist(str(self.playlist_path))

        # Return only URLs that are not downloaded and not removed
        urls = [
            video.url
            for video in playlist.videos
            if not video.downloaded and not video.removed
        ]

        logger.info(f"Found {len(urls)} URLs to download")
        return urls

    def mark_as_downloaded(self, url: str) -> None:
        """Mark a URL as downloaded.

        Args:
            url: The URL to mark as downloaded

        Raises:
            ValueError: If URL is not found in the playlist file
        """
        playlist = parse_playlist(str(self.playlist_path))

        # Find and mark the video as downloaded
        url_found = False
        for video in playlist.videos:
            if video.url == url:
                video.downloaded = True
                # Clear added marker once downloaded
                video.added = False
                url_found = True
                logger.debug(f"Marked URL as downloaded: {url}")
                break

        if not url_found:
            raise ValueError(f"URL not found in playlist: {url}")

        # Save updated playlist
        build_playlist(playlist, str(self.playlist_path))

        logger.success(f"Updated playlist file: {self.playlist_path}")
