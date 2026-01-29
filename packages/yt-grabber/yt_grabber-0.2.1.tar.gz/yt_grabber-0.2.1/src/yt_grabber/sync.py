"""Sync playlist with its source."""

from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger

from yt_grabber import __version__
from yt_grabber.extractors.channel import ChannelExtractor
from yt_grabber.extractors.playlist import PlaylistExtractor
from yt_grabber.models import HeaderChange, Playlist, SyncResult, Video
from yt_grabber.playlist_header import HeaderMetadata
from yt_grabber.playlist_manager import save_playlist, load_playlist


def _fetch_current_videos(source_url: str, source_type: str) -> tuple[List[str], str]:
    """Fetch current videos from the source.

    Args:
        source_url: The source URL (playlist or channel)
        source_type: Type of source ("playlist" or "channel")

    Returns:
        Tuple of (list of video URLs, title)
    """
    if source_type == "playlist":
        extractor = PlaylistExtractor()
    elif source_type == "channel":
        extractor = ChannelExtractor()
    else:
        raise ValueError(f"Unknown source type: {source_type}")

    # Extract video IDs and title
    video_ids, title = extractor._extract_video_ids(source_url)

    # Convert to URLs
    urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]

    # Apply transformations (e.g., channel reverses order)
    urls = extractor.transform_urls(urls)

    return urls, title


def sync_playlist(file_path: Path) -> SyncResult:
    """Sync a playlist with its source.

    Args:
        file_path: Path to the playlist file

    Returns:
        SyncResult with sync results and diff information

    Raises:
        ValueError: If playlist has no header or source URL
    """
    logger.info(f"Syncing playlist: {file_path}")

    # Parse existing playlist
    playlist = load_playlist(file_path)

    if not playlist.header:
        raise ValueError("Playlist has no header - cannot determine source URL")

    old_header = playlist.header

    # Fetch current videos from source
    logger.info(f"Fetching videos from source: {old_header.source_url}")
    current_urls, new_title = _fetch_current_videos(
        old_header.source_url,
        old_header.source_type
    )

    # Build sets for comparison
    current_url_set = set(current_urls)
    existing_urls = {v.url for v in playlist.videos}

    # Find additions and removals
    added_urls = current_url_set - existing_urls
    removed_urls = existing_urls - current_url_set

    logger.info(f"Found {len(added_urls)} new videos")
    logger.info(f"Found {len(removed_urls)} removed videos")

    # Update existing videos (mark as removed if needed)
    for video in playlist.videos:
        if video.url in removed_urls:
            video.removed = True
            # Clear added marker if it was previously added
            video.added = False

    # Append new videos at the end
    for url in current_urls:
        if url in added_urls:
            # Check if we should mark as added
            # Only mark as added if it wasn't already in the list
            playlist.videos.append(Video(
                url=url,
                downloaded=False,
                added=True,
                removed=False
            ))

    # Update header metadata
    new_header = HeaderMetadata(
        source_url=old_header.source_url,
        extraction_timestamp=datetime.now().isoformat(),
        total_videos=len(current_urls),  # Count of videos currently in source
        source_type=old_header.source_type,
        title=new_title,
        extractor_version=__version__
    )
    playlist.header = new_header

    # Build and save updated playlist
    save_playlist(playlist, file_path)

    # Build result
    result = SyncResult(
        added_urls=list(added_urls),
        removed_urls=list(removed_urls),
        header_changes=[]
    )

    # Track header changes
    if old_header.title != new_title:
        result.header_changes.append(HeaderChange(
            field="title",
            old_value=old_header.title,
            new_value=new_title
        ))

    if old_header.total_videos != new_header.total_videos:
        result.header_changes.append(HeaderChange(
            field="total_videos",
            old_value=str(old_header.total_videos),
            new_value=str(new_header.total_videos)
        ))

    # Always changed
    result.header_changes.append(HeaderChange(
        field="extraction_timestamp",
        old_value=old_header.extraction_timestamp,
        new_value=new_header.extraction_timestamp
    ))

    logger.success("Sync completed")

    return result
