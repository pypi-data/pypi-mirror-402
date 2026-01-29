"""YouTube video downloader using yt-dlp."""

import csv
import random
import time
from datetime import datetime
from pathlib import Path

import yt_dlp
from loguru import logger

from yt_grabber.config import Settings
from yt_grabber.notifier import TelegramNotifier
from yt_grabber.playlist import PlaylistManager


class VideoDownloader:
    """Downloads YouTube videos using yt-dlp."""

    def __init__(self, settings: Settings, playlist_path: Path):
        """Initialize the video downloader.

        Args:
            settings: Application settings
            playlist_path: Path to the playlist file
        """
        self.settings = settings
        self.playlist_path = playlist_path

        # Create subdirectory based on playlist filename (without extension)
        playlist_name = playlist_path.stem
        self.download_dir = Path("download") / playlist_name

        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metadata CSV file
        self.metadata_file = self.download_dir / "metadata.csv"
        self._initialize_metadata_file()

        # Initialize Telegram notifier
        self.notifier = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            enabled=settings.telegram_notifications_enabled
        )

        logger.info(f"Download directory: {self.download_dir}")

    def _initialize_metadata_file(self) -> None:
        """Initialize metadata CSV file with headers if it doesn't exist."""
        if not self.metadata_file.exists():
            with open(self.metadata_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["url", "filename", "timestamp"])
            logger.info(f"Created metadata file: {self.metadata_file}")

    def _append_metadata(self, url: str, filename: str) -> None:
        """Append metadata row to CSV file.

        Args:
            url: Video URL
            filename: Downloaded filename
        """
        timestamp = datetime.now().isoformat()
        with open(self.metadata_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([url, filename, timestamp])

    def _get_ydl_opts(self) -> dict:
        """Get yt-dlp options based on settings.

        Returns:
            Dictionary of yt-dlp options
        """
        # Format selection based on quality setting
        if self.settings.video_quality == "1080":
            format_string = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        else:  # 720
            format_string = "bestvideo[height<=720]+bestaudio/best[height<=720]"

        return {
            "format": format_string,
            "outtmpl": str(self.download_dir / "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [],
        }

    def download_video(self, url: str, video_index: int) -> None:
        """Download a single video from URL with retry mechanism.

        Args:
            url: YouTube video URL
            video_index: Index of the video in the playlist (1-based)

        Raises:
            Exception: If download fails after all retry attempts
        """
        max_attempts = self.settings.retry_attempts + 1  # Initial attempt + retries

        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    logger.warning(f"Retry attempt {attempt - 1}/{self.settings.retry_attempts} for: {url}")
                else:
                    logger.info(f"Starting download: {url}")

                start_time = time.time()
                ydl_opts = self._get_ydl_opts()

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # Extract video information
                    video_id = info.get("id", "Unknown")
                    video_title = info.get("title", "Unknown")
                    filename = ydl.prepare_filename(info)
                    original_path = Path(filename)
                    filename_only = original_path.name

                    # Rename file with index if enabled
                    if self.settings.index_videos:
                        index_str = f"{video_index:02d}"
                        new_filename = f"{index_str} {filename_only}"
                        new_path = original_path.parent / new_filename
                        original_path.rename(new_path)
                        filename_only = new_filename
                        logger.debug(f"Renamed file to: {new_filename}")

                    # Calculate download time
                    download_time = time.time() - start_time

                    # Append to metadata CSV
                    self._append_metadata(url, filename_only)

                    # Log statistics
                    logger.success(f"Downloaded: {video_title}")
                    logger.info(f"Statistics:")
                    logger.info(f"  Video ID: {video_id}")
                    logger.info(f"  File: {filename_only}")
                    logger.info(f"  Download time: {download_time:.2f}s")

                    # Success - break out of retry loop
                    return

            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")

                # Check if we should retry
                if attempt < max_attempts:
                    logger.warning(f"Waiting {self.settings.retry_delay} seconds before retry...")
                    time.sleep(self.settings.retry_delay)
                else:
                    # All attempts failed
                    logger.error(f"All {max_attempts} attempts failed for {url}")
                    raise

    def _random_delay(self) -> None:
        """Wait for a random delay between min_delay and max_delay."""
        if self.settings.max_delay <= 0:
            return

        delay = random.uniform(self.settings.min_delay, self.settings.max_delay)
        logger.info(f"Waiting {delay:.2f} seconds before next download...")
        time.sleep(delay)

    def download_playlist(self, playlist_manager: PlaylistManager, delay_after_last: bool = False) -> None:
        """Download all videos from a playlist file.

        Args:
            playlist_manager: PlaylistManager instance
            delay_after_last: If True, add delay after last video (for batch processing)

        Raises:
            Exception: If any download fails (stops entire process)
        """
        urls_with_indices = playlist_manager.read_urls()
        playlist_name = self.playlist_path.stem

        if not urls_with_indices:
            logger.warning("No URLs to download")
            return

        logger.info(f"Starting download of {len(urls_with_indices)} videos")

        try:
            for progress_idx, (url, playlist_index) in enumerate(urls_with_indices, start=1):
                logger.info(f"Progress: {progress_idx}/{len(urls_with_indices)} (playlist position: {playlist_index})")

                try:
                    # Download the video using its position in full playlist
                    self.download_video(url, video_index=playlist_index)

                    # Mark as downloaded
                    playlist_manager.mark_as_downloaded(url)

                    # Add delay after download
                    is_last_video = (progress_idx == len(urls_with_indices))

                    if not is_last_video:
                        # Always delay between videos in same playlist
                        self._random_delay()
                    elif delay_after_last:
                        # Delay after last video if requested (batch mode)
                        self._random_delay()

                except Exception as e:
                    logger.error(f"Error downloading video {progress_idx}/{len(urls_with_indices)}: {e}")
                    logger.error("Stopping download process due to error")

                    # Send error notification
                    self.notifier.send_error_notification(str(e), playlist_name)
                    raise

            logger.success(f"All {len(urls_with_indices)} videos downloaded successfully!")

            # Send success notification
            self.notifier.send_success_notification(len(urls_with_indices), playlist_name)

        except Exception:
            # Re-raise the exception after notification has been sent
            raise
