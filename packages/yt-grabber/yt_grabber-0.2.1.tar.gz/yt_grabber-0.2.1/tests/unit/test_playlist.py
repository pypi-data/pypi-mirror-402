"""Unit tests for playlist module."""

from pathlib import Path

import pytest

from yt_grabber.playlist import PlaylistManager


@pytest.mark.unit
class TestPlaylistManager:
    """Test PlaylistManager class."""

    def test_init(self, tmp_path: Path):
        """Test PlaylistManager initialization."""
        playlist_path = tmp_path / "test.txt"
        manager = PlaylistManager(playlist_path)

        assert manager.playlist_path == playlist_path

    def test_read_urls_file_not_found(self, tmp_path: Path):
        """Test read_urls raises FileNotFoundError when file doesn't exist."""
        playlist_path = tmp_path / "nonexistent.txt"
        manager = PlaylistManager(playlist_path)

        with pytest.raises(FileNotFoundError, match="Playlist file not found"):
            manager.read_urls()

    def test_read_urls_with_header(self, playlist_file_with_header: Path):
        """Test reading URLs from playlist with header."""
        manager = PlaylistManager(playlist_file_with_header)
        urls_with_indices = manager.read_urls()

        # Should have 2 URLs (video1 not downloaded, video2 is downloaded, video3 added but not downloaded)
        assert len(urls_with_indices) == 2
        assert urls_with_indices[0] == ("https://example.com/video1", 1)
        assert urls_with_indices[1] == ("https://example.com/video3", 3)

    def test_read_urls_without_header(self, playlist_file_without_header: Path):
        """Test reading URLs from playlist without header."""
        manager = PlaylistManager(playlist_file_without_header)
        urls_with_indices = manager.read_urls()

        # Should have 2 URLs (video1 and video3, video2 is downloaded)
        assert len(urls_with_indices) == 2
        assert urls_with_indices[0] == ("https://example.com/video1", 1)
        assert urls_with_indices[1] == ("https://example.com/video3", 3)

    def test_read_urls_preserves_indices(self, tmp_path: Path):
        """Test that read_urls returns correct indices from full playlist."""
        playlist_content = """https://example.com/video1
# https://example.com/video2
https://example.com/video3
# https://example.com/video4
https://example.com/video5
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)
        urls_with_indices = manager.read_urls()

        # Should return indices 1, 3, 5 (not 1, 2, 3)
        assert len(urls_with_indices) == 3
        assert urls_with_indices[0] == ("https://example.com/video1", 1)
        assert urls_with_indices[1] == ("https://example.com/video3", 3)
        assert urls_with_indices[2] == ("https://example.com/video5", 5)

    def test_read_urls_skips_removed_videos(self, tmp_path: Path):
        """Test that read_urls skips removed videos."""
        playlist_content = """https://example.com/video1
D https://example.com/video2
https://example.com/video3
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)
        urls_with_indices = manager.read_urls()

        # Should skip removed video2
        assert len(urls_with_indices) == 2
        assert urls_with_indices[0] == ("https://example.com/video1", 1)
        assert urls_with_indices[1] == ("https://example.com/video3", 3)

    def test_read_urls_empty_playlist(self, tmp_path: Path):
        """Test reading URLs from empty playlist."""
        playlist_file = tmp_path / "empty.txt"
        playlist_file.write_text("")

        manager = PlaylistManager(playlist_file)
        urls_with_indices = manager.read_urls()

        assert len(urls_with_indices) == 0

    def test_mark_as_downloaded(self, tmp_path: Path):
        """Test marking a URL as downloaded."""
        playlist_content = """https://example.com/video1
https://example.com/video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)
        manager.mark_as_downloaded("https://example.com/video1")

        # Read back and verify
        urls_with_indices = manager.read_urls()
        assert len(urls_with_indices) == 1
        assert urls_with_indices[0] == ("https://example.com/video2", 2)

        # Check file content
        content = playlist_file.read_text()
        assert "# https://example.com/video1" in content
        assert "https://example.com/video2" in content

    def test_mark_as_downloaded_clears_added_marker(self, tmp_path: Path):
        """Test that mark_as_downloaded clears the added marker."""
        playlist_content = """A https://example.com/video1
https://example.com/video2
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)
        manager.mark_as_downloaded("https://example.com/video1")

        # Check that A marker is removed (just # marker remains)
        content = playlist_file.read_text()
        assert "A # https://example.com/video1" not in content
        assert "# https://example.com/video1" in content

    def test_mark_as_downloaded_url_not_found(self, tmp_path: Path):
        """Test mark_as_downloaded raises ValueError when URL not found."""
        playlist_content = """https://example.com/video1
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)

        with pytest.raises(ValueError, match="URL not found in playlist"):
            manager.mark_as_downloaded("https://example.com/nonexistent")

    def test_mark_as_downloaded_multiple_times(self, tmp_path: Path):
        """Test marking multiple URLs as downloaded."""
        playlist_content = """https://example.com/video1
https://example.com/video2
https://example.com/video3
"""
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text(playlist_content)

        manager = PlaylistManager(playlist_file)

        # Mark first and third as downloaded
        manager.mark_as_downloaded("https://example.com/video1")
        manager.mark_as_downloaded("https://example.com/video3")

        # Only video2 should remain
        urls_with_indices = manager.read_urls()
        assert len(urls_with_indices) == 1
        assert urls_with_indices[0] == ("https://example.com/video2", 2)

    def test_mark_as_downloaded_with_header(self, playlist_file_with_header: Path):
        """Test marking URL as downloaded preserves header."""
        manager = PlaylistManager(playlist_file_with_header)
        manager.mark_as_downloaded("https://example.com/video1")

        # Verify header is preserved
        content = playlist_file_with_header.read_text()
        assert ": Source URL: https://example.com/playlist" in content
        assert ": Title: Sample Playlist" in content

        # Verify URL is marked as downloaded
        assert "# https://example.com/video1" in content
