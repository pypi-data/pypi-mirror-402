"""Unit tests for playlist_manager module."""

from pathlib import Path
from io import StringIO

import pytest
from loguru import logger

from yt_grabber.playlist_manager import load_playlist, save_playlist
from yt_grabber.models import Playlist, Video


class TestDeduplication:
    """Tests for duplicate URL handling in playlist parsing."""

    @pytest.fixture
    def log_sink(self):
        """Fixture to capture loguru logs."""
        log_output = StringIO()
        handler_id = logger.add(log_output, format="{message}")
        yield log_output
        logger.remove(handler_id)

    def test_load_playlist_with_duplicate_urls(self, tmp_path, log_sink):
        """Test that duplicate URLs are skipped and logged."""
        # Create a test playlist file with duplicates
        playlist_file = tmp_path / "test_playlist.txt"
        content = """https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=ghi789
"""
        playlist_file.write_text(content)

        # Parse the playlist
        playlist = load_playlist(playlist_file)

        # Should only have 3 unique videos
        assert len(playlist.videos) == 3
        urls = [video.url for video in playlist.videos]
        assert urls == [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
            "https://youtube.com/watch?v=ghi789",
        ]

        # Check that a warning was logged
        log_text = log_sink.getvalue()
        assert "Duplicate video URL found and skipped" in log_text
        assert "https://youtube.com/watch?v=abc123" in log_text

    def test_load_playlist_with_multiple_duplicates(self, tmp_path, log_sink):
        """Test that multiple duplicate URLs are all skipped."""
        playlist_file = tmp_path / "test_playlist.txt"
        content = """https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
"""
        playlist_file.write_text(content)

        playlist = load_playlist(playlist_file)

        # Should only have 2 unique videos
        assert len(playlist.videos) == 2
        urls = [video.url for video in playlist.videos]
        assert urls == [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
        ]

        # Check that warnings were logged for both duplicates
        log_text = log_sink.getvalue()
        assert log_text.count("Duplicate video URL found and skipped") == 2

    def test_load_playlist_with_duplicates_and_markers(self, tmp_path, log_sink):
        """Test that duplicates are detected regardless of markers."""
        playlist_file = tmp_path / "test_playlist.txt"
        content = """https://youtube.com/watch?v=abc123
# https://youtube.com/watch?v=def456
https://youtube.com/watch?v=abc123
A https://youtube.com/watch?v=def456
"""
        playlist_file.write_text(content)

        playlist = load_playlist(playlist_file)

        # Should only have 2 unique videos (duplicates removed)
        assert len(playlist.videos) == 2

        # First occurrence of each URL should be kept
        assert playlist.videos[0].url == "https://youtube.com/watch?v=abc123"
        assert playlist.videos[0].downloaded is False

        assert playlist.videos[1].url == "https://youtube.com/watch?v=def456"
        assert playlist.videos[1].downloaded is True

        # Check that warnings were logged
        log_text = log_sink.getvalue()
        assert log_text.count("Duplicate video URL found and skipped") == 2

    def test_load_playlist_no_duplicates(self, tmp_path, log_sink):
        """Test that no warnings are logged when there are no duplicates."""
        playlist_file = tmp_path / "test_playlist.txt"
        content = """https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
https://youtube.com/watch?v=ghi789
"""
        playlist_file.write_text(content)

        playlist = load_playlist(playlist_file)

        # Should have all 3 videos
        assert len(playlist.videos) == 3

        # No warning should be logged
        log_text = log_sink.getvalue()
        assert "Duplicate video URL found and skipped" not in log_text


class TestSavePlaylist:
    """Tests for saving playlists to files."""

    def test_save_playlist_basic(self, tmp_path):
        """Test saving a basic playlist without headers or markers."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(
            header=None,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=False, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=ghi789", downloaded=False, added=False, removed=False),
            ]
        )

        save_playlist(playlist, playlist_file)

        # Read the file and verify content
        content = playlist_file.read_text()
        expected = """https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
https://youtube.com/watch?v=ghi789
"""
        assert content == expected

    def test_save_playlist_with_downloaded_markers(self, tmp_path):
        """Test saving a playlist with downloaded markers."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(
            header=None,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=True, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=ghi789", downloaded=True, added=False, removed=False),
            ]
        )

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        expected = """# https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
# https://youtube.com/watch?v=ghi789
"""
        assert content == expected

    def test_save_playlist_with_added_markers(self, tmp_path):
        """Test saving a playlist with added markers."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(
            header=None,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=False, added=True, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=False, removed=False),
            ]
        )

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        expected = """A https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
"""
        assert content == expected

    def test_save_playlist_with_removed_markers(self, tmp_path):
        """Test saving a playlist with removed markers."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(
            header=None,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=False, added=False, removed=True),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=False, removed=False),
            ]
        )

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        expected = """D https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
"""
        assert content == expected

    def test_save_playlist_with_multiple_markers(self, tmp_path):
        """Test saving a playlist with multiple markers on the same video."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(
            header=None,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=True, added=True, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=True, added=False, removed=True),
            ]
        )

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        expected = """A # https://youtube.com/watch?v=abc123
D # https://youtube.com/watch?v=def456
"""
        assert content == expected

    def test_save_playlist_with_header(self, tmp_path):
        """Test saving a playlist with header metadata."""
        from yt_grabber.playlist_header import HeaderMetadata

        playlist_file = tmp_path / "test_playlist.txt"

        header = HeaderMetadata(
            source_url="https://youtube.com/playlist?list=PLtest",
            extraction_timestamp="2024-01-20T10:30:00",
            total_videos=2,
            source_type="playlist",
            title="Test Playlist",
            extractor_version="1.0.0"
        )

        playlist = Playlist(
            header=header,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=False, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=False, removed=False),
            ]
        )

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        lines = content.strip().split("\n")

        # Check header lines
        assert lines[0] == ": Source URL: https://youtube.com/playlist?list=PLtest"
        assert lines[1] == ": Extraction Timestamp: 2024-01-20T10:30:00"
        assert lines[2] == ": Total Videos: 2"
        assert lines[3] == ": Source Type: playlist"
        assert lines[4] == ": Title: Test Playlist"
        assert lines[5] == ": Extractor Version: 1.0.0"
        assert lines[6] == ":"

        # Check video lines
        assert lines[7] == "https://youtube.com/watch?v=abc123"
        assert lines[8] == "https://youtube.com/watch?v=def456"

    def test_save_playlist_empty(self, tmp_path):
        """Test saving an empty playlist."""
        playlist_file = tmp_path / "test_playlist.txt"

        playlist = Playlist(header=None, videos=[])

        save_playlist(playlist, playlist_file)

        content = playlist_file.read_text()
        assert content == "\n"

    def test_save_and_load_roundtrip(self, tmp_path):
        """Test that saving and loading a playlist preserves all data."""
        from yt_grabber.playlist_header import HeaderMetadata

        playlist_file = tmp_path / "test_playlist.txt"

        header = HeaderMetadata(
            source_url="https://youtube.com/playlist?list=PLtest",
            extraction_timestamp="2024-01-20T10:30:00",
            total_videos=3,
            source_type="playlist",
            title="Test Playlist",
            extractor_version="1.0.0"
        )

        original_playlist = Playlist(
            header=header,
            videos=[
                Video(url="https://youtube.com/watch?v=abc123", downloaded=True, added=False, removed=False),
                Video(url="https://youtube.com/watch?v=def456", downloaded=False, added=True, removed=False),
                Video(url="https://youtube.com/watch?v=ghi789", downloaded=False, added=False, removed=True),
            ]
        )

        # Save the playlist
        save_playlist(original_playlist, playlist_file)

        # Load it back
        loaded_playlist = load_playlist(playlist_file)

        # Verify header
        assert loaded_playlist.header is not None
        assert loaded_playlist.header.source_url == header.source_url
        assert loaded_playlist.header.extraction_timestamp == header.extraction_timestamp
        assert loaded_playlist.header.total_videos == header.total_videos
        assert loaded_playlist.header.source_type == header.source_type
        assert loaded_playlist.header.title == header.title
        assert loaded_playlist.header.extractor_version == header.extractor_version

        # Verify videos
        assert len(loaded_playlist.videos) == 3

        assert loaded_playlist.videos[0].url == "https://youtube.com/watch?v=abc123"
        assert loaded_playlist.videos[0].downloaded is True
        assert loaded_playlist.videos[0].added is False
        assert loaded_playlist.videos[0].removed is False

        assert loaded_playlist.videos[1].url == "https://youtube.com/watch?v=def456"
        assert loaded_playlist.videos[1].downloaded is False
        assert loaded_playlist.videos[1].added is True
        assert loaded_playlist.videos[1].removed is False

        assert loaded_playlist.videos[2].url == "https://youtube.com/watch?v=ghi789"
        assert loaded_playlist.videos[2].downloaded is False
        assert loaded_playlist.videos[2].added is False
        assert loaded_playlist.videos[2].removed is True
