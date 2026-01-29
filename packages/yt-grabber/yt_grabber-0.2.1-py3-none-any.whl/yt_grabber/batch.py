"""Batch download module for processing multiple playlists."""

from pathlib import Path
from typing import List, Literal

from loguru import logger

from yt_grabber.config import Settings
from yt_grabber.downloader import VideoDownloader
from yt_grabber.notifier import TelegramNotifier
from yt_grabber.playlist import PlaylistManager


class BatchDownloader:
    """Downloads videos from multiple playlist files."""

    def __init__(self, settings: Settings):
        """Initialize batch downloader.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.notifier = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            enabled=settings.telegram_notifications_enabled
        )

    def find_playlists(
        self,
        directory: Path,
        pattern: str = "*.txt",
        sort_order: Literal["asc", "desc"] = "asc"
    ) -> List[Path]:
        """Find playlist files matching pattern.

        Args:
            directory: Directory to search in
            pattern: Glob pattern for filtering files
            sort_order: Sort order - 'asc' for ascending, 'desc' for descending

        Returns:
            List of playlist file paths, sorted according to sort_order
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        # Find all matching files
        files = list(directory.glob(pattern))

        if not files:
            logger.warning(f"No files matching pattern '{pattern}' found in {directory}")
            return []

        # Sort files
        reverse = (sort_order == "desc")
        sorted_files = sorted(files, reverse=reverse)

        logger.info(f"Found {len(sorted_files)} playlist files")
        for idx, file in enumerate(sorted_files, start=1):
            logger.info(f"  {idx}. {file.name}")

        return sorted_files

    def download_all_playlists(
        self,
        directory: Path,
        pattern: str = "*.txt",
        sort_order: Literal["asc", "desc"] = "asc"
    ) -> None:
        """Download videos from all playlists matching pattern.

        Args:
            directory: Directory containing playlist files
            pattern: Glob pattern for filtering files
            sort_order: Sort order for processing playlists

        Raises:
            Exception: If any playlist download fails
        """
        playlists = self.find_playlists(directory, pattern, sort_order)

        if not playlists:
            logger.warning("No playlists to process")
            return

        total_playlists = len(playlists)
        logger.info(f"Starting batch download of {total_playlists} playlists")
        logger.info(f"Sort order: {sort_order}ending")

        successful_downloads = 0

        try:
            for idx, playlist_path in enumerate(playlists, start=1):
                playlist_name = playlist_path.stem
                logger.info("=" * 60)
                logger.info(f"Processing playlist {idx}/{total_playlists}: {playlist_name}")
                logger.info("=" * 60)

                # Send playlist started notification
                self.notifier.send_playlist_started_notification(
                    playlist_name=playlist_name,
                    current=idx,
                    total=total_playlists
                )

                try:
                    # Initialize components for this playlist
                    playlist_manager = PlaylistManager(playlist_path)
                    downloader = VideoDownloader(self.settings, playlist_path)

                    # Check if this is the last playlist
                    is_last_playlist = (idx == total_playlists)

                    # Download videos from this playlist
                    # Add delay after last video if not the last playlist
                    downloader.download_playlist(
                        playlist_manager,
                        delay_after_last=not is_last_playlist
                    )

                    successful_downloads += 1
                    logger.success(f"Completed playlist {idx}/{total_playlists}: {playlist_name}")

                except Exception as e:
                    logger.error(f"Failed to download playlist {idx}/{total_playlists}: {playlist_name}")
                    logger.error(f"Error: {e}")

                    # Send batch error notification
                    error_msg = f"Playlist: {playlist_name} ({idx}/{total_playlists})\nError: {str(e)}"
                    self.notifier.send_batch_error_notification(error_msg)

                    # Halt batch processing on first failure
                    logger.error("Halting batch download due to error")
                    raise

            # All playlists downloaded successfully
            logger.success("=" * 60)
            logger.success(f"Batch download complete!")
            logger.success(f"Successfully downloaded {successful_downloads}/{total_playlists} playlists")
            logger.success("=" * 60)

            # Send batch success notification
            self.notifier.send_batch_success_notification(successful_downloads)

        except Exception:
            logger.error(f"Batch download failed after {successful_downloads}/{total_playlists} playlists")
            raise
