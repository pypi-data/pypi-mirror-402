"""Unit tests for batch module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_grabber.batch import BatchDownloader


@pytest.mark.unit
class TestBatchDownloader:
    """Test BatchDownloader class."""

    def test_init(self, mock_settings):
        """Test BatchDownloader initialization."""
        batch = BatchDownloader(mock_settings)

        assert batch.settings == mock_settings
        assert batch.notifier is not None

    def test_find_playlists_empty_directory(self, mock_settings, tmp_path: Path):
        """Test finding playlists in empty directory."""
        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path)

        assert len(playlists) == 0

    def test_find_playlists_no_matches(self, mock_settings, tmp_path: Path):
        """Test finding playlists with pattern that matches nothing."""
        # Create some files that don't match pattern
        (tmp_path / "file1.md").touch()
        (tmp_path / "file2.py").touch()

        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path, pattern="*.txt")

        assert len(playlists) == 0

    def test_find_playlists_basic(self, mock_settings, tmp_path: Path):
        """Test finding playlist files with default pattern."""
        # Create playlist files
        (tmp_path / "playlist1.txt").touch()
        (tmp_path / "playlist2.txt").touch()
        (tmp_path / "other.md").touch()

        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path)

        assert len(playlists) == 2
        assert all(p.suffix == ".txt" for p in playlists)

    def test_find_playlists_with_pattern(self, mock_settings, tmp_path: Path):
        """Test finding playlists with custom glob pattern."""
        # Create various files
        (tmp_path / "gmm_s01.txt").touch()
        (tmp_path / "gmm_s02.txt").touch()
        (tmp_path / "other_playlist.txt").touch()

        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path, pattern="gmm*.txt")

        assert len(playlists) == 2
        assert all("gmm" in p.name for p in playlists)

    def test_find_playlists_ascending_order(self, mock_settings, tmp_path: Path):
        """Test playlists sorted in ascending order."""
        # Create files (will sort alphabetically)
        (tmp_path / "playlist_c.txt").touch()
        (tmp_path / "playlist_a.txt").touch()
        (tmp_path / "playlist_b.txt").touch()

        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path, sort_order="asc")

        assert len(playlists) == 3
        assert playlists[0].name == "playlist_a.txt"
        assert playlists[1].name == "playlist_b.txt"
        assert playlists[2].name == "playlist_c.txt"

    def test_find_playlists_descending_order(self, mock_settings, tmp_path: Path):
        """Test playlists sorted in descending order."""
        # Create files
        (tmp_path / "playlist_c.txt").touch()
        (tmp_path / "playlist_a.txt").touch()
        (tmp_path / "playlist_b.txt").touch()

        batch = BatchDownloader(mock_settings)
        playlists = batch.find_playlists(tmp_path, sort_order="desc")

        assert len(playlists) == 3
        assert playlists[0].name == "playlist_c.txt"
        assert playlists[1].name == "playlist_b.txt"
        assert playlists[2].name == "playlist_a.txt"

    def test_find_playlists_directory_not_found(self, mock_settings, tmp_path: Path):
        """Test error when directory doesn't exist."""
        batch = BatchDownloader(mock_settings)
        non_existent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            batch.find_playlists(non_existent)

    def test_find_playlists_not_a_directory(self, mock_settings, tmp_path: Path):
        """Test error when path is a file, not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        batch = BatchDownloader(mock_settings)

        with pytest.raises(NotADirectoryError):
            batch.find_playlists(file_path)

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_success(self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path):
        """Test successfully downloading all playlists."""
        # Create playlist files
        (tmp_path / "playlist1.txt").write_text("https://example.com/video1\n")
        (tmp_path / "playlist2.txt").write_text("https://example.com/video2\n")

        # Setup mocks
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)
        batch.download_all_playlists(tmp_path)

        # Verify both playlists processed
        assert mock_pm_class.call_count == 2
        assert mock_vd_class.call_count == 2
        assert mock_vd.download_playlist.call_count == 2

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_delay_between_playlists(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test delay_after_last parameter for playlists."""
        # Create 3 playlist files
        (tmp_path / "p1.txt").write_text("url1\n")
        (tmp_path / "p2.txt").write_text("url2\n")
        (tmp_path / "p3.txt").write_text("url3\n")

        # Setup mocks
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)
        batch.download_all_playlists(tmp_path)

        # Verify delay_after_last parameter
        calls = mock_vd.download_playlist.call_args_list
        assert len(calls) == 3

        # First two should have delay_after_last=True
        assert calls[0][1]["delay_after_last"] is True
        assert calls[1][1]["delay_after_last"] is True
        # Last should have delay_after_last=False
        assert calls[2][1]["delay_after_last"] is False

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_error_stops_batch(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test that error in one playlist stops entire batch."""
        # Create playlist files
        (tmp_path / "playlist1.txt").write_text("url1\n")
        (tmp_path / "playlist2.txt").write_text("url2\n")
        (tmp_path / "playlist3.txt").write_text("url3\n")

        # Setup mocks - fail on second playlist
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd.download_playlist.side_effect = [None, Exception("Download failed"), None]
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)

        with pytest.raises(Exception, match="Download failed"):
            batch.download_all_playlists(tmp_path)

        # Should only process 2 playlists
        assert mock_vd.download_playlist.call_count == 2

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_with_pattern(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test downloading with pattern filter."""
        # Create various files
        (tmp_path / "season_01.txt").write_text("url1\n")
        (tmp_path / "season_02.txt").write_text("url2\n")
        (tmp_path / "other.txt").write_text("url3\n")

        # Setup mocks
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)
        batch.download_all_playlists(tmp_path, pattern="season*.txt")

        # Should only process 2 playlists matching pattern
        assert mock_vd.download_playlist.call_count == 2

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_notifications(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test notifications are sent during batch download."""
        # Create playlist files
        (tmp_path / "p1.txt").write_text("url1\n")
        (tmp_path / "p2.txt").write_text("url2\n")

        # Setup mocks
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)

        with patch.object(batch.notifier, "send_playlist_started_notification") as mock_started, \
             patch.object(batch.notifier, "send_batch_success_notification") as mock_success:
            batch.download_all_playlists(tmp_path)

            # Verify notifications
            assert mock_started.call_count == 2
            mock_success.assert_called_once_with(2)

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_error_notification(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test error notification sent on failure."""
        # Create playlist file
        (tmp_path / "playlist1.txt").write_text("url1\n")

        # Setup mocks to fail
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd.download_playlist.side_effect = Exception("Test error")
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)

        with patch.object(batch.notifier, "send_batch_error_notification") as mock_error:
            with pytest.raises(Exception):
                batch.download_all_playlists(tmp_path)

            # Verify error notification sent
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "playlist1" in call_args
            assert "Test error" in call_args

    def test_download_all_playlists_no_playlists(self, mock_settings, tmp_path: Path):
        """Test batch download with no matching playlists."""
        batch = BatchDownloader(mock_settings)

        # Should not raise, just return
        batch.download_all_playlists(tmp_path)

    @patch("yt_grabber.batch.VideoDownloader")
    @patch("yt_grabber.batch.PlaylistManager")
    def test_download_all_playlists_respects_sort_order(
        self, mock_pm_class, mock_vd_class, mock_settings, tmp_path: Path
    ):
        """Test playlists processed in correct sort order."""
        # Create files with specific names
        (tmp_path / "c_playlist.txt").write_text("url\n")
        (tmp_path / "a_playlist.txt").write_text("url\n")
        (tmp_path / "b_playlist.txt").write_text("url\n")

        # Setup mocks
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        mock_vd = MagicMock()
        mock_vd_class.return_value = mock_vd

        batch = BatchDownloader(mock_settings)
        batch.download_all_playlists(tmp_path, sort_order="desc")

        # Verify order by checking PlaylistManager calls
        calls = mock_pm_class.call_args_list
        assert "c_playlist.txt" in str(calls[0])
        assert "b_playlist.txt" in str(calls[1])
        assert "a_playlist.txt" in str(calls[2])
