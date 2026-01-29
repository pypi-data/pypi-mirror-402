# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-18

### Changed
- Relaxed Python version requirement from >=3.14 to >=3.12
- Added Python 3.12 and 3.13 to classifiers

## [0.1.0] - 2026-01-18

### Added
- Initial release
- `extract-playlist` command - Extract video URLs from playlists
- `extract-channel` command - Extract video URLs from channels (regular videos only, oldest first)
- `sync` command - Synchronize playlists with their source to detect new and removed videos
- `download` command - Download videos from playlist files with progress tracking
- Playlist header support with metadata (source URL, timestamp, video count, title)
- Progress tracking with markers:
  - `#` marker for downloaded videos
  - `A` marker for newly added videos (detected during sync)
  - `D` marker for removed videos (deleted from source)
- Automatic resume capability - skips already downloaded videos
- Configurable video quality (720p or 1080p)
- Random delays between downloads to avoid rate limiting
- Metadata CSV generation with download information
- Colorized logging with detailed progress information

### Features
- Smart playlist management with sync capability
- Preserves video order during sync
- Keeps removed videos in playlist for history
- Download markers preserved across syncs
- Header metadata automatically updated during sync

[0.1.0]: https://github.com/elisey/yt-grabber/releases/tag/v0.1.0
