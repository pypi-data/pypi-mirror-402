"""Integration tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from yt_grabber.cli import app

runner = CliRunner()


@pytest.mark.integration
class TestExtractPlaylistCommand:
    """Test extract-playlist CLI command."""

    @patch("yt_grabber.cli.PlaylistExtractor")
    def test_extract_playlist_success(self, mock_extractor_class, tmp_path: Path):
        """Test successful playlist extraction."""
        output_file = tmp_path / "playlist.txt"

        # Setup mocks
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        result = runner.invoke(
            app,
            ["extract-playlist", "PLtest123", str(output_file)]
        )

        assert result.exit_code == 0
        mock_extractor.extract_urls.assert_called_once()

    @patch("yt_grabber.cli.PlaylistExtractor")
    def test_extract_playlist_error(self, mock_extractor_class, tmp_path: Path):
        """Test playlist extraction with error."""
        output_file = tmp_path / "playlist.txt"

        # Setup mock to raise error
        mock_extractor = MagicMock()
        mock_extractor.extract_urls.side_effect = Exception("Extraction failed")
        mock_extractor_class.return_value = mock_extractor

        result = runner.invoke(
            app,
            ["extract-playlist", "PLtest123", str(output_file)]
        )

        assert result.exit_code == 1


@pytest.mark.integration
class TestExtractChannelCommand:
    """Test extract-channel CLI command."""

    @patch("yt_grabber.cli.ChannelExtractor")
    def test_extract_channel_success(self, mock_extractor_class, tmp_path: Path):
        """Test successful channel extraction."""
        output_file = tmp_path / "channel.txt"

        # Setup mocks
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        result = runner.invoke(
            app,
            ["extract-channel", "@TestChannel", str(output_file)]
        )

        assert result.exit_code == 0
        mock_extractor.extract_urls.assert_called_once()

    @patch("yt_grabber.cli.ChannelExtractor")
    def test_extract_channel_error(self, mock_extractor_class, tmp_path: Path):
        """Test channel extraction with error."""
        output_file = tmp_path / "channel.txt"

        # Setup mock to raise error
        mock_extractor = MagicMock()
        mock_extractor.extract_urls.side_effect = Exception("Extraction failed")
        mock_extractor_class.return_value = mock_extractor

        result = runner.invoke(
            app,
            ["extract-channel", "@TestChannel", str(output_file)]
        )

        assert result.exit_code == 1


@pytest.mark.integration
class TestDownloadCommand:
    """Test download CLI command."""

    @patch("yt_grabber.cli.VideoDownloader")
    @patch("yt_grabber.cli.PlaylistManager")
    @patch("yt_grabber.cli.Settings")
    def test_download_success(self, mock_settings_class, mock_pm_class, mock_vd_class, tmp_path: Path):
        """Test successful download command."""
        # Create playlist file
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text("https://example.com/video1\n")

        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        result = runner.invoke(app, ["download", str(playlist_file)])

        assert result.exit_code == 0
        mock_vd.download_playlist.assert_called_once_with(mock_pm)

    @patch("yt_grabber.cli.Settings")
    def test_download_file_not_found(self, mock_settings_class, tmp_path: Path):
        """Test download with non-existent playlist file."""
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        non_existent = tmp_path / "nonexistent.txt"

        result = runner.invoke(app, ["download", str(non_existent)])

        assert result.exit_code == 1

    @patch("yt_grabber.cli.VideoDownloader")
    @patch("yt_grabber.cli.PlaylistManager")
    @patch("yt_grabber.cli.Settings")
    def test_download_error(self, mock_settings_class, mock_pm_class, mock_vd_class, tmp_path: Path):
        """Test download with error during download."""
        # Create playlist file
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text("https://example.com/video1\n")

        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd.download_playlist.side_effect = Exception("Download failed")
        mock_vd_class.return_value = mock_vd

        result = runner.invoke(app, ["download", str(playlist_file)])

        assert result.exit_code == 1


@pytest.mark.integration
class TestSyncCommand:
    """Test sync CLI command."""

    @patch("yt_grabber.cli.sync_playlist")
    def test_sync_success(self, mock_sync, tmp_path: Path):
        """Test successful sync command."""
        # Create playlist file with header
        playlist_file = tmp_path / "test.txt"
        playlist_content = """: Source URL: https://example.com/playlist
: Extraction Timestamp: 2026-01-18T12:00:00
: Total Videos: 2
: Source Type: playlist
: Title: Test
: Extractor Version: 0.1.0
:
https://example.com/video1
"""
        playlist_file.write_text(playlist_content)

        # Setup mock
        from yt_grabber.models import SyncResult
        mock_sync.return_value = SyncResult(
            added_urls=[],
            removed_urls=[],
            header_changes=[]
        )

        result = runner.invoke(app, ["sync", str(playlist_file)])

        assert result.exit_code == 0
        mock_sync.assert_called_once()

    def test_sync_file_not_found(self, tmp_path: Path):
        """Test sync with non-existent file."""
        non_existent = tmp_path / "nonexistent.txt"

        result = runner.invoke(app, ["sync", str(non_existent)])

        assert result.exit_code == 1

    @patch("yt_grabber.cli.sync_playlist")
    def test_sync_error(self, mock_sync, tmp_path: Path):
        """Test sync with error."""
        # Create playlist file
        playlist_file = tmp_path / "test.txt"
        playlist_file.write_text("url1\n")

        # Setup mock to raise error
        mock_sync.side_effect = Exception("Sync failed")

        result = runner.invoke(app, ["sync", str(playlist_file)])

        assert result.exit_code == 1


@pytest.mark.integration
class TestDownloadBatchCommand:
    """Test download-batch CLI command."""

    @patch("yt_grabber.cli.BatchDownloader")
    @patch("yt_grabber.cli.Settings")
    def test_download_batch_success(self, mock_settings_class, mock_batch_class, tmp_path: Path):
        """Test successful batch download."""
        # Create playlist files
        (tmp_path / "p1.txt").write_text("url1\n")
        (tmp_path / "p2.txt").write_text("url2\n")

        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_batch = MagicMock()
        mock_batch_class.return_value = mock_batch

        result = runner.invoke(app, ["download-batch", str(tmp_path)])

        assert result.exit_code == 0
        mock_batch.download_all_playlists.assert_called_once()

    @patch("yt_grabber.cli.BatchDownloader")
    @patch("yt_grabber.cli.Settings")
    def test_download_batch_with_pattern(self, mock_settings_class, mock_batch_class, tmp_path: Path):
        """Test batch download with pattern."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_batch = MagicMock()
        mock_batch_class.return_value = mock_batch

        result = runner.invoke(
            app,
            ["download-batch", str(tmp_path), "--pattern", "gmm*.txt"]
        )

        assert result.exit_code == 0
        call_args = mock_batch.download_all_playlists.call_args
        assert call_args[1]["pattern"] == "gmm*.txt"

    @patch("yt_grabber.cli.BatchDownloader")
    @patch("yt_grabber.cli.Settings")
    def test_download_batch_with_sort_ascending(self, mock_settings_class, mock_batch_class, tmp_path: Path):
        """Test batch download with ascending sort."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_batch = MagicMock()
        mock_batch_class.return_value = mock_batch

        result = runner.invoke(
            app,
            ["download-batch", str(tmp_path), "--sort", "asc"]
        )

        assert result.exit_code == 0
        call_args = mock_batch.download_all_playlists.call_args
        assert call_args[1]["sort_order"] == "asc"

    @patch("yt_grabber.cli.BatchDownloader")
    @patch("yt_grabber.cli.Settings")
    def test_download_batch_with_sort_descending(self, mock_settings_class, mock_batch_class, tmp_path: Path):
        """Test batch download with descending sort."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_batch = MagicMock()
        mock_batch_class.return_value = mock_batch

        result = runner.invoke(
            app,
            ["download-batch", str(tmp_path), "--sort", "desc"]
        )

        assert result.exit_code == 0
        call_args = mock_batch.download_all_playlists.call_args
        assert call_args[1]["sort_order"] == "desc"

    @patch("yt_grabber.cli.Settings")
    def test_download_batch_invalid_sort(self, mock_settings_class, tmp_path: Path):
        """Test batch download with invalid sort option."""
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        result = runner.invoke(
            app,
            ["download-batch", str(tmp_path), "--sort", "invalid"]
        )

        assert result.exit_code == 1

    @patch("yt_grabber.cli.BatchDownloader")
    @patch("yt_grabber.cli.Settings")
    def test_download_batch_error(self, mock_settings_class, mock_batch_class, tmp_path: Path):
        """Test batch download with error."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.video_quality = "720"
        mock_settings.min_delay = 0
        mock_settings.max_delay = 0
        mock_settings_class.return_value = mock_settings

        mock_batch = MagicMock()
        mock_batch.download_all_playlists.side_effect = Exception("Batch failed")
        mock_batch_class.return_value = mock_batch

        result = runner.invoke(app, ["download-batch", str(tmp_path)])

        assert result.exit_code == 1


@pytest.mark.integration
class TestCLIHelp:
    """Test CLI help commands."""

    def test_main_help(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "YouTube video downloader" in result.stdout

    def test_extract_playlist_help(self):
        """Test extract-playlist help."""
        result = runner.invoke(app, ["extract-playlist", "--help"])

        assert result.exit_code == 0
        assert "Extract video URLs from a YouTube playlist" in result.stdout

    def test_extract_channel_help(self):
        """Test extract-channel help."""
        result = runner.invoke(app, ["extract-channel", "--help"])

        assert result.exit_code == 0
        assert "Extract video URLs from a YouTube channel" in result.stdout

    def test_download_help(self):
        """Test download help."""
        result = runner.invoke(app, ["download", "--help"])

        assert result.exit_code == 0
        assert "Download videos from a playlist file" in result.stdout

    def test_sync_help(self):
        """Test sync help."""
        result = runner.invoke(app, ["sync", "--help"])

        assert result.exit_code == 0
        assert "Sync playlist with its source" in result.stdout

    def test_download_batch_help(self):
        """Test download-batch help."""
        result = runner.invoke(app, ["download-batch", "--help"])

        assert result.exit_code == 0
        assert "Download videos from multiple playlist files" in result.stdout
