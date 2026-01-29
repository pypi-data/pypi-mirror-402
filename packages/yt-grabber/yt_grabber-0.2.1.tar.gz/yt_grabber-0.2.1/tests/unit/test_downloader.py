"""Unit tests for downloader module."""

import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from yt_grabber.downloader import VideoDownloader


@pytest.mark.unit
class TestVideoDownloader:
    """Test VideoDownloader class."""

    def test_init(self, mock_settings, tmp_path: Path):
        """Test VideoDownloader initialization."""
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("https://example.com/video1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)

        assert downloader.settings == mock_settings
        assert downloader.playlist_path == playlist_path
        assert downloader.download_dir == Path("download") / "test"
        assert downloader.download_dir.exists()
        assert downloader.metadata_file.exists()

    def test_init_creates_download_directory(self, mock_settings, tmp_path: Path):
        """Test that init creates download directory."""
        playlist_path = tmp_path / "my_playlist.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)

        expected_dir = Path("download") / "my_playlist"
        assert downloader.download_dir == expected_dir
        assert expected_dir.exists()

    def test_init_creates_metadata_file(self, mock_settings, tmp_path: Path):
        """Test that init creates metadata CSV file with headers."""
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)

        metadata_file = downloader.metadata_file
        assert metadata_file.exists()

        content = metadata_file.read_text()
        assert "url,filename,timestamp" in content

    def test_get_ydl_opts_quality_720(self, mock_settings, tmp_path: Path):
        """Test yt-dlp options for 720p quality."""
        mock_settings.video_quality = "720"
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)
        opts = downloader._get_ydl_opts()

        assert opts["format"] == "bestvideo[height<=720]+bestaudio/best[height<=720]"
        assert opts["merge_output_format"] == "mp4"

    def test_get_ydl_opts_quality_1080(self, mock_settings, tmp_path: Path):
        """Test yt-dlp options for 1080p quality."""
        mock_settings.video_quality = "1080"
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)
        opts = downloader._get_ydl_opts()

        assert opts["format"] == "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    @patch("yt_grabber.downloader.yt_dlp.YoutubeDL")
    @patch("yt_grabber.downloader.time.time")
    def test_download_video_success(self, mock_time, mock_ydl_class, mock_settings, tmp_path: Path):
        """Test successful video download."""
        # Setup time mock
        mock_time.side_effect = [0, 10]  # Start, end

        # Setup playlist
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        # Setup YoutubeDL mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "id": "test123",
            "title": "Test Video",
        }
        mock_ydl.prepare_filename.return_value = str(Path("download/test/Test Video.mp4"))
        mock_ydl_class.return_value = mock_ydl

        # Create the expected file
        download_dir = Path("download") / "test"
        download_dir.mkdir(parents=True, exist_ok=True)
        video_file = download_dir / "Test Video.mp4"
        video_file.touch()

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader.download_video("https://example.com/watch?v=test123", video_index=1)

        # Verify download was called
        mock_ydl.extract_info.assert_called_once()

    @patch("yt_grabber.downloader.yt_dlp.YoutubeDL")
    @patch("yt_grabber.downloader.time.time")
    def test_download_video_with_index(self, mock_time, mock_ydl_class, mock_settings, tmp_path: Path):
        """Test video download with indexing enabled."""
        # Setup time mock
        mock_time.side_effect = [0, 10]

        # Enable indexing
        mock_settings.index_videos = True

        # Setup playlist
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        # Setup YoutubeDL mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.return_value = {
            "id": "test123",
            "title": "Test Video",
        }

        download_dir = Path("download") / "test"
        download_dir.mkdir(parents=True, exist_ok=True)
        original_file = download_dir / "Test Video.mp4"
        mock_ydl.prepare_filename.return_value = str(original_file)
        mock_ydl_class.return_value = mock_ydl

        # Create the file
        original_file.touch()

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader.download_video("https://example.com/watch?v=test123", video_index=5)

        # Verify file was renamed with index
        indexed_file = download_dir / "05 Test Video.mp4"
        assert indexed_file.exists()
        assert not original_file.exists()

    @patch("yt_grabber.downloader.yt_dlp.YoutubeDL")
    @patch("yt_grabber.downloader.time.sleep")
    def test_download_video_retry_on_failure(self, mock_sleep, mock_ydl_class, mock_settings, tmp_path: Path):
        """Test retry mechanism on download failure."""
        # Setup settings with retry
        mock_settings.retry_attempts = 2
        mock_settings.retry_delay = 5

        # Setup playlist
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        # Setup YoutubeDL mock to fail twice then succeed
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.side_effect = [
            Exception("HTTP 403"),  # First attempt fails
            Exception("HTTP 403"),  # First retry fails
            {  # Second retry succeeds
                "id": "test123",
                "title": "Test Video",
            }
        ]

        download_dir = Path("download") / "test"
        download_dir.mkdir(parents=True, exist_ok=True)
        video_file = download_dir / "Test Video.mp4"
        mock_ydl.prepare_filename.return_value = str(video_file)
        mock_ydl_class.return_value = mock_ydl

        # Create file for final success
        video_file.touch()

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader.download_video("https://example.com/watch?v=test123", video_index=1)

        # Verify retries occurred
        assert mock_ydl.extract_info.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(5)

    @patch("yt_grabber.downloader.yt_dlp.YoutubeDL")
    @patch("yt_grabber.downloader.time.sleep")
    def test_download_video_all_retries_fail(self, mock_sleep, mock_ydl_class, mock_settings, tmp_path: Path):
        """Test download fails after all retry attempts."""
        # Setup settings with retry
        mock_settings.retry_attempts = 1
        mock_settings.retry_delay = 5

        # Setup playlist
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        # Setup YoutubeDL mock to always fail
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=None)
        mock_ydl.extract_info.side_effect = Exception("HTTP 403")
        mock_ydl_class.return_value = mock_ydl

        downloader = VideoDownloader(mock_settings, playlist_path)

        # Should raise after all attempts
        with pytest.raises(Exception, match="HTTP 403"):
            downloader.download_video("https://example.com/watch?v=test123", video_index=1)

        # Verify all attempts were made
        assert mock_ydl.extract_info.call_count == 2  # Initial + 1 retry
        mock_sleep.assert_called_once_with(5)

    @patch("yt_grabber.downloader.time.sleep")
    @patch("yt_grabber.downloader.random.uniform")
    def test_random_delay(self, mock_uniform, mock_sleep, mock_settings, tmp_path: Path):
        """Test random delay between downloads."""
        mock_settings.min_delay = 10
        mock_settings.max_delay = 20
        mock_uniform.return_value = 15.5

        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader._random_delay()

        mock_uniform.assert_called_once_with(10, 20)
        mock_sleep.assert_called_once_with(15.5)

    def test_random_delay_disabled(self, mock_settings, tmp_path: Path):
        """Test no delay when max_delay is 0."""
        mock_settings.max_delay = 0

        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)

        with patch("yt_grabber.downloader.time.sleep") as mock_sleep:
            downloader._random_delay()
            mock_sleep.assert_not_called()

    @patch("yt_grabber.downloader.VideoDownloader.download_video")
    @patch("yt_grabber.downloader.VideoDownloader._random_delay")
    def test_download_playlist_success(self, mock_delay, mock_download, mock_settings, tmp_path: Path):
        """Test downloading all videos from playlist."""
        # Create playlist with 3 URLs
        playlist_content = """https://example.com/video1
https://example.com/video2
https://example.com/video3
"""
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text(playlist_content)

        from yt_grabber.playlist import PlaylistManager
        playlist_manager = PlaylistManager(playlist_path)

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader.download_playlist(playlist_manager, delay_after_last=False)

        # Verify all videos downloaded
        assert mock_download.call_count == 3
        # Verify delay called between videos (not after last)
        assert mock_delay.call_count == 2

    @patch("yt_grabber.downloader.VideoDownloader.download_video")
    @patch("yt_grabber.downloader.VideoDownloader._random_delay")
    def test_download_playlist_with_delay_after_last(self, mock_delay, mock_download, mock_settings, tmp_path: Path):
        """Test delay_after_last parameter."""
        playlist_content = """https://example.com/video1
https://example.com/video2
"""
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text(playlist_content)

        from yt_grabber.playlist import PlaylistManager
        playlist_manager = PlaylistManager(playlist_path)

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader.download_playlist(playlist_manager, delay_after_last=True)

        # Verify delay called after last video too
        assert mock_delay.call_count == 2

    @patch("yt_grabber.downloader.VideoDownloader.download_video")
    def test_download_playlist_error_stops_process(self, mock_download, mock_settings, tmp_path: Path):
        """Test that error stops the download process."""
        # Make download fail on second video
        mock_download.side_effect = [None, Exception("Download failed"), None]

        playlist_content = """https://example.com/video1
https://example.com/video2
https://example.com/video3
"""
        playlist_path = tmp_path / "test.txt"
        playlist_path.write_text(playlist_content)

        from yt_grabber.playlist import PlaylistManager
        playlist_manager = PlaylistManager(playlist_path)

        downloader = VideoDownloader(mock_settings, playlist_path)

        with pytest.raises(Exception):
            downloader.download_playlist(playlist_manager)

        # Only first two should be attempted
        assert mock_download.call_count == 2

    def test_append_metadata(self, mock_settings, tmp_path: Path, monkeypatch):
        """Test metadata appending to CSV file."""
        # Use tmp_path as working directory to isolate download directory
        monkeypatch.chdir(tmp_path)

        playlist_path = tmp_path / "test_metadata.txt"
        playlist_path.write_text("url1\n")

        downloader = VideoDownloader(mock_settings, playlist_path)
        downloader._append_metadata("https://example.com/video1", "video1.mp4")

        # Read metadata file
        content = downloader.metadata_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 2  # Header + 1 data row
        assert "https://example.com/video1" in lines[1]
        assert "video1.mp4" in lines[1]
