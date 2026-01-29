"""Unit tests for extractors module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_grabber.extractors import ChannelExtractor, PlaylistExtractor
from yt_grabber.extractors.base import BaseExtractor


@pytest.mark.unit
class TestPlaylistExtractor:
    """Test PlaylistExtractor class."""

    def test_get_source_type(self):
        """Test get_source_type returns 'playlist'."""
        extractor = PlaylistExtractor()
        assert extractor.get_source_type() == "playlist"

    def test_normalize_url_with_full_url(self):
        """Test normalizing a full playlist URL."""
        extractor = PlaylistExtractor()
        url = "https://www.youtube.com/playlist?list=PLtest123"

        result = extractor.normalize_url(url)

        assert result == url

    def test_normalize_url_with_http(self):
        """Test normalizing HTTP playlist URL."""
        extractor = PlaylistExtractor()
        url = "http://www.youtube.com/playlist?list=PLtest123"

        result = extractor.normalize_url(url)

        assert result == url

    def test_normalize_url_with_playlist_id(self):
        """Test normalizing a playlist ID to full URL."""
        extractor = PlaylistExtractor()
        playlist_id = "PLtest123"

        result = extractor.normalize_url(playlist_id)

        assert result == "https://www.youtube.com/playlist?list=PLtest123"

    def test_transform_urls_returns_same_order(self):
        """Test transform_urls maintains the same order for playlists."""
        extractor = PlaylistExtractor()
        urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video3",
        ]

        result = extractor.transform_urls(urls)

        assert result == urls

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_urls_success(self, mock_ydl_class, tmp_path: Path, mock_playlist_info):
        """Test successful URL extraction to file."""
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = mock_playlist_info
        mock_ydl_class.return_value = mock_ydl

        # Extract URLs
        extractor = PlaylistExtractor()
        output_file = tmp_path / "playlist.txt"
        extractor.extract_urls("PLtest123", output_file)

        # Verify file was created
        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert ": Source URL: https://www.youtube.com/playlist?list=PLtest123" in content
        assert ": Source Type: playlist" in content
        assert ": Title: Test Playlist" in content
        assert ": Total Videos: 2" in content
        assert "https://www.youtube.com/watch?v=video1" in content
        assert "https://www.youtube.com/watch?v=video2" in content

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_urls_no_entries(self, mock_ydl_class, tmp_path: Path):
        """Test extraction fails when no entries found."""
        # Setup mock without entries
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {"id": "test", "title": "Test"}
        mock_ydl_class.return_value = mock_ydl

        # Extract URLs should raise
        extractor = PlaylistExtractor()
        output_file = tmp_path / "playlist.txt"

        with pytest.raises(ValueError, match="No videos found"):
            extractor.extract_urls("PLtest123", output_file)

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_urls_empty_entries(self, mock_ydl_class, tmp_path: Path):
        """Test extraction fails when entries are empty."""
        # Setup mock with empty entries
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "id": "test",
            "title": "Test",
            "entries": []
        }
        mock_ydl_class.return_value = mock_ydl

        # Extract URLs should raise
        extractor = PlaylistExtractor()
        output_file = tmp_path / "playlist.txt"

        with pytest.raises(ValueError, match="No valid video IDs found"):
            extractor.extract_urls("PLtest123", output_file)


@pytest.mark.unit
class TestChannelExtractor:
    """Test ChannelExtractor class."""

    def test_get_source_type(self):
        """Test get_source_type returns 'channel'."""
        extractor = ChannelExtractor()
        assert extractor.get_source_type() == "channel"

    def test_normalize_url_with_full_url(self):
        """Test normalizing a full channel URL."""
        extractor = ChannelExtractor()
        url = "https://www.youtube.com/channel/UCtest123"

        result = extractor.normalize_url(url)

        assert result == "https://www.youtube.com/channel/UCtest123/videos"

    def test_normalize_url_with_full_url_already_has_videos(self):
        """Test normalizing a full channel URL that already has /videos."""
        extractor = ChannelExtractor()
        url = "https://www.youtube.com/channel/UCtest123/videos"

        result = extractor.normalize_url(url)

        assert result == url

    def test_normalize_url_with_handle(self):
        """Test normalizing a @handle to full URL."""
        extractor = ChannelExtractor()
        handle = "@ChannelName"

        result = extractor.normalize_url(handle)

        assert result == "https://www.youtube.com/@ChannelName/videos"

    def test_normalize_url_with_channel_id(self):
        """Test normalizing a channel ID to full URL."""
        extractor = ChannelExtractor()
        channel_id = "UCtest123"

        result = extractor.normalize_url(channel_id)

        assert result == "https://www.youtube.com/channel/UCtest123/videos"

    def test_normalize_url_with_trailing_slash(self):
        """Test normalizing URL with trailing slash."""
        extractor = ChannelExtractor()
        url = "https://www.youtube.com/channel/UCtest123/"

        result = extractor.normalize_url(url)

        assert result == "https://www.youtube.com/channel/UCtest123/videos"

    def test_transform_urls_reverses_order(self):
        """Test transform_urls reverses order (oldest first)."""
        extractor = ChannelExtractor()
        urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video3",
        ]

        result = extractor.transform_urls(urls)

        # Should be reversed
        assert result == [
            "https://www.youtube.com/watch?v=video3",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video1",
        ]

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_urls_reverses_order(self, mock_ydl_class, tmp_path: Path):
        """Test channel extraction reverses video order."""
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "id": "test_channel",
            "title": "Test Channel",
            "entries": [
                {"id": "newest", "url": "https://example.com/newest"},
                {"id": "middle", "url": "https://example.com/middle"},
                {"id": "oldest", "url": "https://example.com/oldest"},
            ],
        }
        mock_ydl_class.return_value = mock_ydl

        # Extract URLs
        extractor = ChannelExtractor()
        output_file = tmp_path / "channel.txt"
        extractor.extract_urls("@TestChannel", output_file)

        # Verify content order (should be reversed)
        content = output_file.read_text()
        lines = [line for line in content.split("\n") if line and not line.startswith(":")]

        assert "https://www.youtube.com/watch?v=oldest" in lines[0]
        assert "https://www.youtube.com/watch?v=middle" in lines[1]
        assert "https://www.youtube.com/watch?v=newest" in lines[2]

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_urls_with_handle(self, mock_ydl_class, tmp_path: Path, mock_playlist_info):
        """Test extraction with @handle input."""
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = mock_playlist_info
        mock_ydl_class.return_value = mock_ydl

        # Extract URLs
        extractor = ChannelExtractor()
        output_file = tmp_path / "channel.txt"
        extractor.extract_urls("@TestChannel", output_file)

        # Verify normalized URL in header
        content = output_file.read_text()
        assert ": Source URL: https://www.youtube.com/@TestChannel/videos" in content
        assert ": Source Type: channel" in content


@pytest.mark.unit
class TestBaseExtractor:
    """Test BaseExtractor abstract class."""

    def test_base_extractor_is_abstract(self):
        """Test that BaseExtractor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseExtractor()

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_video_ids_with_none_entries(self, mock_ydl_class):
        """Test handling of None entries in video list."""
        # Setup mock with None entries
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "title": "Test",
            "entries": [
                {"id": "video1"},
                None,  # This can happen with unavailable videos
                {"id": "video2"},
            ],
        }
        mock_ydl_class.return_value = mock_ydl

        # Should skip None entries
        extractor = PlaylistExtractor()
        video_ids, title = extractor._extract_video_ids("https://example.com/playlist")

        assert len(video_ids) == 2
        assert video_ids == ["video1", "video2"]
        assert title == "Test"

    @patch("yt_grabber.extractors.base.yt_dlp.YoutubeDL")
    def test_extract_video_ids_with_missing_id(self, mock_ydl_class):
        """Test handling of entries without ID field."""
        # Setup mock with entry missing ID
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "title": "Test",
            "entries": [
                {"id": "video1"},
                {"title": "No ID"},  # Missing 'id' field
                {"id": "video2"},
            ],
        }
        mock_ydl_class.return_value = mock_ydl

        # Should skip entries without ID
        extractor = PlaylistExtractor()
        video_ids, title = extractor._extract_video_ids("https://example.com/playlist")

        assert len(video_ids) == 2
        assert video_ids == ["video1", "video2"]
