"""Unit tests for models module."""

import pytest

from yt_grabber.models import HeaderChange, Playlist, SyncResult, Video
from yt_grabber.playlist_header import HeaderMetadata


@pytest.mark.unit
class TestVideo:
    """Test Video dataclass."""

    def test_create_basic_video(self):
        """Test creating a basic video with only URL."""
        video = Video(url="https://example.com/video")

        assert video.url == "https://example.com/video"
        assert video.downloaded is False
        assert video.added is False
        assert video.removed is False

    def test_create_downloaded_video(self):
        """Test creating a downloaded video."""
        video = Video(url="https://example.com/video", downloaded=True)

        assert video.url == "https://example.com/video"
        assert video.downloaded is True
        assert video.added is False
        assert video.removed is False

    def test_create_added_video(self):
        """Test creating a newly added video."""
        video = Video(url="https://example.com/video", added=True)

        assert video.url == "https://example.com/video"
        assert video.downloaded is False
        assert video.added is True
        assert video.removed is False

    def test_create_removed_video(self):
        """Test creating a removed video."""
        video = Video(url="https://example.com/video", removed=True)

        assert video.url == "https://example.com/video"
        assert video.downloaded is False
        assert video.added is False
        assert video.removed is True

    def test_video_with_all_markers(self):
        """Test video with all markers set."""
        video = Video(
            url="https://example.com/video",
            downloaded=True,
            added=True,
            removed=True,
        )

        assert video.url == "https://example.com/video"
        assert video.downloaded is True
        assert video.added is True
        assert video.removed is True


@pytest.mark.unit
class TestPlaylist:
    """Test Playlist dataclass."""

    def test_create_playlist_with_header(self, sample_header, sample_videos):
        """Test creating a playlist with header."""
        playlist = Playlist(header=sample_header, videos=sample_videos)

        assert playlist.header == sample_header
        assert len(playlist.videos) == 3
        assert playlist.videos[0].url == "https://example.com/video1"

    def test_create_playlist_without_header(self, sample_videos):
        """Test creating a playlist without header."""
        playlist = Playlist(header=None, videos=sample_videos)

        assert playlist.header is None
        assert len(playlist.videos) == 3

    def test_empty_playlist(self):
        """Test creating an empty playlist."""
        playlist = Playlist(header=None, videos=[])

        assert playlist.header is None
        assert len(playlist.videos) == 0


@pytest.mark.unit
class TestHeaderChange:
    """Test HeaderChange dataclass."""

    def test_create_header_change(self):
        """Test creating a header change."""
        change = HeaderChange(
            field="Title",
            old_value="Old Title",
            new_value="New Title",
        )

        assert change.field == "Title"
        assert change.old_value == "Old Title"
        assert change.new_value == "New Title"

    def test_header_change_video_count(self):
        """Test header change for video count."""
        change = HeaderChange(
            field="Total Videos",
            old_value="10",
            new_value="12",
        )

        assert change.field == "Total Videos"
        assert change.old_value == "10"
        assert change.new_value == "12"


@pytest.mark.unit
class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_create_empty_sync_result(self):
        """Test creating an empty sync result."""
        result = SyncResult()

        assert result.added_urls == []
        assert result.removed_urls == []
        assert result.header_changes == []

    def test_sync_result_with_additions(self):
        """Test sync result with added videos."""
        result = SyncResult(
            added_urls=["https://example.com/video1", "https://example.com/video2"]
        )

        assert len(result.added_urls) == 2
        assert result.added_urls[0] == "https://example.com/video1"
        assert result.removed_urls == []
        assert result.header_changes == []

    def test_sync_result_with_removals(self):
        """Test sync result with removed videos."""
        result = SyncResult(
            removed_urls=["https://example.com/video1"]
        )

        assert result.added_urls == []
        assert len(result.removed_urls) == 1
        assert result.removed_urls[0] == "https://example.com/video1"
        assert result.header_changes == []

    def test_sync_result_with_header_changes(self):
        """Test sync result with header changes."""
        changes = [
            HeaderChange(field="Title", old_value="Old", new_value="New"),
            HeaderChange(field="Total Videos", old_value="5", new_value="7"),
        ]
        result = SyncResult(header_changes=changes)

        assert result.added_urls == []
        assert result.removed_urls == []
        assert len(result.header_changes) == 2
        assert result.header_changes[0].field == "Title"
        assert result.header_changes[1].field == "Total Videos"

    def test_sync_result_with_all_changes(self):
        """Test sync result with all types of changes."""
        changes = [
            HeaderChange(field="Title", old_value="Old", new_value="New")
        ]
        result = SyncResult(
            added_urls=["https://example.com/new"],
            removed_urls=["https://example.com/old"],
            header_changes=changes,
        )

        assert len(result.added_urls) == 1
        assert len(result.removed_urls) == 1
        assert len(result.header_changes) == 1
