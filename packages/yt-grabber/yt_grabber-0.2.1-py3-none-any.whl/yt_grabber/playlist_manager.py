from pathlib import Path

from loguru import logger

from yt_grabber.models import Playlist, Video
from yt_grabber.playlist_header import PlaylistFileHeader


DOWNLOADED_MARKER = "#"
ADDED_MARKER = "A"
REMOVED_MARKER = "D"
HEADER_MARKER = ":"


def load_playlist(file_path: Path) -> Playlist:
    """Parse a playlist file into a Playlist object."""
    if not file_path.exists():
        raise FileNotFoundError(f"Playlist file not found: {file_path}")

    # Read header
    header = PlaylistFileHeader.read_header(file_path)

    # Parse videos
    videos = []

    seen_videos = set()

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip header lines
            if line.startswith(HEADER_MARKER):
                continue

            # Parse markers and URL
            downloaded = False
            added = False
            removed = False
            url = line

            # Check for markers (space-separated)
            parts = line.split()

            # Process markers
            marker_count = 0
            for part in parts:
                if part == ADDED_MARKER:
                    added = True
                    marker_count += 1
                elif part == REMOVED_MARKER:
                    removed = True
                    marker_count += 1
                elif part == DOWNLOADED_MARKER:
                    downloaded = True
                    marker_count += 1
                else:
                    # First non-marker part is the URL
                    url = " ".join(parts[marker_count:])
                    break
            if url in seen_videos:
                logger.warning(f"Duplicate video URL found and skipped: {url}")
                continue
            seen_videos.add(url)

            videos.append(Video(
                url=url,
                downloaded=downloaded,
                added=added,
                removed=removed
            ))

    return Playlist(header=header, videos=videos)


def save_playlist(playlist: Playlist, file_path: Path) -> None:
    """Build and write a playlist file from a Playlist object."""
    lines = []

    # Add header if present
    if playlist.header:
        lines.append(f": Source URL: {playlist.header.source_url}")
        lines.append(f": Extraction Timestamp: {playlist.header.extraction_timestamp}")
        lines.append(f": Total Videos: {playlist.header.total_videos}")
        lines.append(f": Source Type: {playlist.header.source_type}")
        lines.append(f": Title: {playlist.header.title}")
        lines.append(f": Extractor Version: {playlist.header.extractor_version}")
        lines.append(":")

    # Add videos with markers
    for video in playlist.videos:
        markers = []

        if video.added:
            markers.append(ADDED_MARKER)

        if video.removed:
            markers.append(REMOVED_MARKER)

        if video.downloaded:
            markers.append(DOWNLOADED_MARKER)

        # Build line: markers (space-separated) followed by URL
        if markers:
            line = " ".join(markers) + " " + video.url
        else:
            line = video.url

        lines.append(line)

    # Write to file
    with open(file_path, "w") as f:
        f.write("\n".join(lines) + "\n")
