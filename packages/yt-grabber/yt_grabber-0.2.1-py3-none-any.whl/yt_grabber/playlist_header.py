"""Playlist file header management."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class HeaderMetadata:
    """Metadata stored in playlist file header."""

    source_url: str
    extraction_timestamp: str
    total_videos: int
    source_type: str
    title: str
    extractor_version: str


class PlaylistFileHeader:
    """Manages reading and writing playlist file headers."""

    HEADER_MARKER = ":"

    @staticmethod
    def format_header_lines(metadata: HeaderMetadata) -> List[str]:
        """Format header metadata as list of lines.

        Args:
            metadata: Header metadata

        Returns:
            List of formatted header lines
        """
        lines = [
            f": Source URL: {metadata.source_url}",
            f": Extraction Timestamp: {metadata.extraction_timestamp}",
            f": Total Videos: {metadata.total_videos}",
            f": Source Type: {metadata.source_type}",
            f": Title: {metadata.title}",
            f": Extractor Version: {metadata.extractor_version}",
            ":",
        ]
        return lines

    @staticmethod
    def write_header(f, metadata: HeaderMetadata) -> None:
        """Write header to file object.

        Args:
            f: File object opened for writing
            metadata: Header metadata to write
        """
        lines = PlaylistFileHeader.format_header_lines(metadata)
        for line in lines:
            f.write(f"{line}\n")

    @staticmethod
    def parse_header_line(line: str) -> Optional[tuple[str, str]]:
        """Parse a single header line into key-value pair.

        Args:
            line: Header line starting with ':'

        Returns:
            Tuple of (key, value) or None if not a valid header line
        """
        if not line.startswith(PlaylistFileHeader.HEADER_MARKER):
            return None

        # Remove leading ':' and whitespace
        content = line[1:].strip()

        # Empty separator line
        if not content:
            return None

        # Split on first ':'
        parts = content.split(":", 1)
        if len(parts) != 2:
            return None

        key = parts[0].strip()
        value = parts[1].strip()
        return (key, value)

    @staticmethod
    def read_header(file_path: Path) -> Optional[HeaderMetadata]:
        """Read and parse header from playlist file.

        Args:
            file_path: Path to playlist file

        Returns:
            HeaderMetadata object or None if no header found
        """
        if not file_path.exists():
            return None

        header_data = {}

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Stop reading when we hit non-header line
                if not line.startswith(PlaylistFileHeader.HEADER_MARKER):
                    break

                # Parse header line
                parsed = PlaylistFileHeader.parse_header_line(line)
                if parsed:
                    key, value = parsed
                    header_data[key] = value

        if not header_data:
            return None

        return HeaderMetadata(
            source_url=header_data.get("Source URL", ""),
            extraction_timestamp=header_data.get("Extraction Timestamp", ""),
            total_videos=int(header_data.get("Total Videos", 0)),
            source_type=header_data.get("Source Type", ""),
            title=header_data.get("Title", ""),
            extractor_version=header_data.get("Extractor Version", "")
        )
