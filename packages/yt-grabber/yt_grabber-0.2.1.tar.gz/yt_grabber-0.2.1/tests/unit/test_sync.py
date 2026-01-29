"""Unit tests for sync module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_grabber.sync import _fetch_current_videos, sync_playlist


@pytest.mark.unit
class TestFetchCurrentVideos:
    """Test _fetch_current_videos function."""

    @patch("yt_grabber.sync.PlaylistExtractor")
    def test_fetch_playlist_videos(self, mock_extractor_class):
        """Test fetching videos from a playlist."""
        # Setup mock
        mock_extractor = MagicMock()
        mock_extractor._extract_video_ids.return_value = (
            ["video1", "video2", "video3"],
            "Test Playlist"
        )
        mock_extractor.transform_urls.side_effect = lambda urls: urls
        mock_extractor_class.return_value = mock_extractor

        # Fetch videos
        urls, title = _fetch_current_videos(
            "https://www.youtube.com/playlist?list=PLtest",
            "playlist"
        )

        # Verify
        assert len(urls) == 3
        assert urls[0] == "https://www.youtube.com/watch?v=video1"
        assert urls[1] == "https://www.youtube.com/watch?v=video2"
        assert urls[2] == "https://www.youtube.com/watch?v=video3"
        assert title == "Test Playlist"

    @patch("yt_grabber.sync.ChannelExtractor")
    def test_fetch_channel_videos(self, mock_extractor_class):
        """Test fetching videos from a channel."""
        # Setup mock
        mock_extractor = MagicMock()
        mock_extractor._extract_video_ids.return_value = (
            ["video1", "video2"],
            "Test Channel"
        )
        # Channel extractor reverses URLs
        mock_extractor.transform_urls.side_effect = lambda urls: list(reversed(urls))
        mock_extractor_class.return_value = mock_extractor

        # Fetch videos
        urls, title = _fetch_current_videos(
            "https://www.youtube.com/@TestChannel/videos",
            "channel"
        )

        # Verify - should be reversed
        assert len(urls) == 2
        assert urls[0] == "https://www.youtube.com/watch?v=video2"
        assert urls[1] == "https://www.youtube.com/watch?v=video1"
        assert title == "Test Channel"

    def test_fetch_unknown_source_type(self):
        """Test fetching with unknown source type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown source type"):
            _fetch_current_videos("https://example.com", "unknown")


@pytest.mark.unit
class TestSyncPlaylist:
    """Test sync_playlist function."""

    def test_sync_playlist_no_header(self, tmp_path: Path):
        """Test sync raises ValueError when playlist has no header."""
        # Create playlist without header
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text("https://www.youtube.com/watch?v=video1\n")

        with pytest.raises(ValueError, match="Playlist has no header"):
            sync_playlist(playlist_file)

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_no_changes(self, mock_fetch, tmp_path: Path):
        """Test sync when no videos added or removed."""
        # Create playlist with header
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Test Playlist
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch to return same videos
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video2",
            ],
            "Test Playlist"
        )

        # Sync
        result = sync_playlist(playlist_file)

        # Verify no additions or removals
        assert len(result.added_urls) == 0
        assert len(result.removed_urls) == 0

        # Timestamp should always change
        assert any(c.field == "extraction_timestamp" for c in result.header_changes)

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_with_additions(self, mock_fetch, tmp_path: Path):
        """Test sync when new videos are added to source."""
        # Create playlist with header
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Test Playlist
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch to return additional video
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video2",
                "https://www.youtube.com/watch?v=video3",
            ],
            "Test Playlist"
        )

        # Sync
        result = sync_playlist(playlist_file)

        # Verify additions
        assert len(result.added_urls) == 1
        assert "https://www.youtube.com/watch?v=video3" in result.added_urls
        assert len(result.removed_urls) == 0

        # Verify total videos changed
        assert any(
            c.field == "total_videos" and c.new_value == "3"
            for c in result.header_changes
        )

        # Verify file has A marker for new video
        content = playlist_file.read_text()
        assert "A https://www.youtube.com/watch?v=video3" in content

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_with_removals(self, mock_fetch, tmp_path: Path):
        """Test sync when videos are removed from source."""
        # Create playlist with header
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 3
: Source Type: playlist
: Title: Test Playlist
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
https://www.youtube.com/watch?v=video3
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch to return fewer videos
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video3",
            ],
            "Test Playlist"
        )

        # Sync
        result = sync_playlist(playlist_file)

        # Verify removals
        assert len(result.added_urls) == 0
        assert len(result.removed_urls) == 1
        assert "https://www.youtube.com/watch?v=video2" in result.removed_urls

        # Verify total videos changed
        assert any(
            c.field == "total_videos" and c.new_value == "2"
            for c in result.header_changes
        )

        # Verify file has D marker for removed video
        content = playlist_file.read_text()
        assert "D https://www.youtube.com/watch?v=video2" in content

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_with_title_change(self, mock_fetch, tmp_path: Path):
        """Test sync when playlist title changes."""
        # Create playlist with header
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Old Title
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch with new title
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video2",
            ],
            "New Title"
        )

        # Sync
        result = sync_playlist(playlist_file)

        # Verify title change
        assert any(
            c.field == "title" and c.old_value == "Old Title" and c.new_value == "New Title"
            for c in result.header_changes
        )

        # Verify file has new title
        content = playlist_file.read_text()
        assert ": Title: New Title" in content

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_preserves_downloaded_markers(self, mock_fetch, tmp_path: Path):
        """Test sync preserves # markers for downloaded videos."""
        # Create playlist with downloaded video
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Test Playlist
: Extractor Version: 0.1.0
:
# https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch - same videos
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video2",
            ],
            "Test Playlist"
        )

        # Sync
        sync_playlist(playlist_file)

        # Verify downloaded marker is preserved
        content = playlist_file.read_text()
        assert "# https://www.youtube.com/watch?v=video1" in content

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_clears_added_marker_when_removed(self, mock_fetch, tmp_path: Path):
        """Test sync clears A marker when video is removed."""
        # Create playlist with added video
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Test Playlist
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
A https://www.youtube.com/watch?v=video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch - video2 removed
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
            ],
            "Test Playlist"
        )

        # Sync
        sync_playlist(playlist_file)

        # Verify A marker is cleared and replaced with D
        content = playlist_file.read_text()
        assert "D https://www.youtube.com/watch?v=video2" in content
        assert "A D https://www.youtube.com/watch?v=video2" not in content

    @patch("yt_grabber.sync._fetch_current_videos")
    def test_sync_playlist_multiple_changes(self, mock_fetch, tmp_path: Path):
        """Test sync with additions, removals, and title change."""
        # Create playlist
        playlist_content = """: Source URL: https://www.youtube.com/playlist?list=PLtest
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 3
: Source Type: playlist
: Title: Old Title
: Extractor Version: 0.1.0
:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
https://www.youtube.com/watch?v=video3
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        # Mock fetch - remove video2, add video4, change title
        mock_fetch.return_value = (
            [
                "https://www.youtube.com/watch?v=video1",
                "https://www.youtube.com/watch?v=video3",
                "https://www.youtube.com/watch?v=video4",
            ],
            "New Title"
        )

        # Sync
        result = sync_playlist(playlist_file)

        # Verify changes
        assert len(result.added_urls) == 1
        assert "https://www.youtube.com/watch?v=video4" in result.added_urls
        assert len(result.removed_urls) == 1
        assert "https://www.youtube.com/watch?v=video2" in result.removed_urls

        # Verify header changes
        assert any(c.field == "title" for c in result.header_changes)
        # total_videos stays the same (3 -> 3) so no change recorded
        assert any(c.field == "extraction_timestamp" for c in result.header_changes)

        # Verify file content
        content = playlist_file.read_text()
        assert "D https://www.youtube.com/watch?v=video2" in content
        assert "A https://www.youtube.com/watch?v=video4" in content
        assert ": Title: New Title" in content
