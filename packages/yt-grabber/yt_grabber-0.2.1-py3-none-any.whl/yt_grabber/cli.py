"""Command-line interface for YouTube video downloader."""

import sys
from pathlib import Path

import typer
from loguru import logger

from yt_grabber.batch import BatchDownloader
from yt_grabber.config import Settings
from yt_grabber.downloader import VideoDownloader
from yt_grabber.extractors import ChannelExtractor, PlaylistExtractor
from yt_grabber.models import SyncResult
from yt_grabber.playlist import PlaylistManager
from yt_grabber.sync import sync_playlist

app = typer.Typer(help="YouTube video downloader and content extractor")


def setup_logging() -> None:
    """Configure Loguru logging with colors."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
        level="INFO",
    )


@app.command(name="extract-playlist")
def extract_playlist(
    playlist_url: str = typer.Argument(
        ...,
        help="YouTube playlist URL or playlist ID (e.g., PLTj8zGbtGsjHQWtKYupS1CdZzrbbYKkoz)",
    ),
    output: str = typer.Argument(
        ...,
        help="Output file path to save video URLs",
    ),
) -> None:
    """Extract video URLs from a YouTube playlist."""
    setup_logging()

    try:
        output_path = Path(output)
        extractor = PlaylistExtractor()
        extractor.extract_urls(playlist_url, output_path)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(1)


@app.command(name="extract-channel")
def extract_channel(
    channel_url: str = typer.Argument(
        ...,
        help="YouTube channel URL, @handle, or channel ID (e.g., @ChannelName or UC...)",
    ),
    output: str = typer.Argument(
        ...,
        help="Output file path to save video URLs",
    ),
) -> None:
    """Extract video URLs from a YouTube channel (regular videos only, oldest first)."""
    setup_logging()

    try:
        output_path = Path(output)
        extractor = ChannelExtractor()
        extractor.extract_urls(channel_url, output_path)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(1)


@app.command()
def download(
    playlist_file: str = typer.Argument(
        ...,
        help="Path to playlist file",
    ),
) -> None:
    """Download videos from a playlist file."""
    setup_logging()

    try:
        # Load settings
        settings = Settings()
        logger.info(f"Video quality: {settings.video_quality}p")
        logger.info(f"Delay range: {settings.min_delay}-{settings.max_delay}s")

        # Get playlist file path
        playlist_path = Path(playlist_file)
        logger.info(f"Using playlist file: {playlist_path}")

        # Initialize components
        playlist_manager = PlaylistManager(playlist_path)
        downloader = VideoDownloader(settings, playlist_path)

        # Start downloading
        downloader.download_playlist(playlist_manager)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(1)


@app.command(name="download-batch")
def download_batch(
    directory: str = typer.Argument(
        ".",
        help="Directory containing playlist files",
    ),
    pattern: str = typer.Option(
        "*.txt",
        "--pattern",
        "-p",
        help="Glob pattern for filtering playlist files (e.g., 'gmm*.txt', 'season_*.txt')",
    ),
    sort: str = typer.Option(
        "asc",
        "--sort",
        "-s",
        help="Sort order: 'asc' for ascending, 'desc' for descending",
    ),
) -> None:
    """Download videos from multiple playlist files in a directory.

    Processes all playlist files matching the pattern in the specified directory.
    Stops on first error.
    """
    setup_logging()

    try:
        # Validate sort option
        if sort not in ["asc", "desc"]:
            logger.error(f"Invalid sort option: {sort}. Use 'asc' or 'desc'")
            raise typer.Exit(1)

        # Load settings
        settings = Settings()
        logger.info(f"Video quality: {settings.video_quality}p")
        logger.info(f"Delay range: {settings.min_delay}-{settings.max_delay}s")

        # Get directory path
        dir_path = Path(directory)
        logger.info(f"Directory: {dir_path}")
        logger.info(f"Pattern: {pattern}")
        logger.info(f"Sort: {sort}ending")

        # Initialize batch downloader
        batch_downloader = BatchDownloader(settings)

        # Start batch download
        batch_downloader.download_all_playlists(
            directory=dir_path,
            pattern=pattern,
            sort_order=sort  # type: ignore
        )

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(1)

    except NotADirectoryError as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(1)


def format_sync_diff(result: SyncResult) -> None:
    """Format and print sync diff result.

    Args:
        result: SyncResult dataclass containing sync results
    """
    logger.info("=" * 60)
    logger.info("SYNC SUMMARY")
    logger.info("=" * 60)

    # Print added videos
    if result.added_urls:
        logger.info(f"✓ Added ({len(result.added_urls)} videos):")
        for url in result.added_urls:
            logger.info(f"  + {url}")
    else:
        logger.info("✓ No new videos added")

    # Print removed videos
    if result.removed_urls:
        logger.info(f"✗ Removed ({len(result.removed_urls)} videos):")
        for url in result.removed_urls:
            logger.info(f"  - {url}")
    else:
        logger.info("✗ No videos removed")

    # Print header changes
    if result.header_changes:
        logger.info("⚙ Header changes:")
        for change in result.header_changes:
            if change.field == "extraction_timestamp":
                logger.info(f"  • {change.field}: updated to {change.new_value}")
            else:
                logger.info(f"  • {change.field}: {change.old_value} → {change.new_value}")
    else:
        logger.info("⚙ No header changes")

    logger.info("\n" + "=" * 60)


@app.command()
def sync(
    playlist_file: str = typer.Argument(
        ...,
        help="Path to playlist file",
    ),
) -> None:
    """Sync playlist with its source and show diff."""
    setup_logging()

    try:
        playlist_path = Path(playlist_file)

        if not playlist_path.exists():
            logger.error(f"Playlist file not found: {playlist_path}")
            raise typer.Exit(1)

        # Sync the playlist
        result = sync_playlist(playlist_path)

        # Format and print diff
        format_sync_diff(result)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        setup_logging()
        logger.warning("Interrupted by user")
        raise typer.Exit(130)


if __name__ == "__main__":
    main()
