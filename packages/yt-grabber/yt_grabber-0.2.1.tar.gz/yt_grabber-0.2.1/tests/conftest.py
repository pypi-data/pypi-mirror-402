"""Shared fixtures for tests."""

from pathlib import Path
from typing import List

import pytest

from yt_grabber.config import Settings
from yt_grabber.models import HeaderMetadata, Playlist, Video


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        video_quality="720",
        min_delay=0,
        max_delay=0,
        retry_attempts=1,
        retry_delay=0,
        telegram_notifications_enabled=False,
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat_id",
        index_videos=True,
    )


@pytest.fixture
def sample_header() -> HeaderMetadata:
    """Create sample header metadata."""
    return HeaderMetadata(
        source_url="https://example.com/playlist",
        extraction_timestamp="2026-01-18T12:00:00",
        total_videos=3,
        source_type="playlist",
        title="Sample Playlist",
        extractor_version="0.1.0",
    )


@pytest.fixture
def sample_videos() -> List[Video]:
    """Create sample videos list."""
    return [
        Video(url="https://example.com/video1", downloaded=False),
        Video(url="https://example.com/video2", downloaded=True),
        Video(url="https://example.com/video3", downloaded=False, added=True),
    ]


@pytest.fixture
def sample_playlist(sample_header: HeaderMetadata, sample_videos: List[Video]) -> Playlist:
    """Create sample playlist."""
    return Playlist(header=sample_header, videos=sample_videos)


@pytest.fixture
def playlist_content_with_header() -> str:
    """Sample playlist file content with header."""
    return """: Source URL: https://example.com/playlist
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 3
: Source Type: playlist
: Title: Sample Playlist
: Extractor Version: 0.1.0
:
https://example.com/video1
# https://example.com/video2
A https://example.com/video3
"""


@pytest.fixture
def playlist_content_without_header() -> str:
    """Sample playlist file content without header."""
    return """https://example.com/video1
# https://example.com/video2
https://example.com/video3
"""


@pytest.fixture
def playlist_file_with_header(tmp_path: Path, playlist_content_with_header: str) -> Path:
    """Create temporary playlist file with header."""
    playlist_file = tmp_path / "playlist.txt"
    playlist_file.write_text(playlist_content_with_header)
    return playlist_file


@pytest.fixture
def playlist_file_without_header(tmp_path: Path, playlist_content_without_header: str) -> Path:
    """Create temporary playlist file without header."""
    playlist_file = tmp_path / "playlist.txt"
    playlist_file.write_text(playlist_content_without_header)
    return playlist_file


@pytest.fixture
def mock_ydl_info() -> dict:
    """Mock yt-dlp info dict."""
    return {
        "id": "test_video_id",
        "title": "Test Video Title",
        "url": "https://example.com/video.mp4",
        "ext": "mp4",
        "entries": None,
    }


@pytest.fixture
def mock_playlist_info() -> dict:
    """Mock yt-dlp playlist info dict."""
    return {
        "id": "test_playlist_id",
        "title": "Test Playlist",
        "entries": [
            {
                "id": "video1",
                "title": "Video 1",
                "url": "https://example.com/video1",
                "webpage_url": "https://example.com/watch?v=video1",
            },
            {
                "id": "video2",
                "title": "Video 2",
                "url": "https://example.com/video2",
                "webpage_url": "https://example.com/watch?v=video2",
            },
        ],
    }
