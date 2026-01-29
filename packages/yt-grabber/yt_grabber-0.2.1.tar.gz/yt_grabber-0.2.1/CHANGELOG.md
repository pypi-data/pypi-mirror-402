# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-20

### Changed
- Code refactoring for improved maintainability
- Enhanced test coverage with additional unit tests

### Fixed
- Added `.coverage` file to `.gitignore` to prevent committing test coverage artifacts

## [0.2.0] - 2026-01-18

### Added
- **New command:** `download-batch` for processing multiple playlists
  - Batch download from directory with glob pattern support
  - Sort order support (ascending/descending)
  - Automatic playlist processing with error handling
- Telegram notifications for batch operations:
  - Notification when each playlist starts (with progress counter)
  - Notification on batch completion
  - Notification on batch failure with context
- Glob pattern matching for playlist selection (e.g., `gmm*.txt`, `season_*.txt`)

### Changed
- Enhanced notification system with batch operation support
- Improved error handling for batch operations (halt on first failure)

### Use Cases
- Download entire TV show seasons in order
- Process multiple music playlist files
- Batch process all playlists in a directory

## [0.1.4] - 2026-01-18

### Added
- Telegram notifications for download completion and failures
- New configuration options:
  - `TELEGRAM_NOTIFICATIONS_ENABLED` - Enable/disable Telegram notifications
  - `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
  - `TELEGRAM_CHAT_ID` - Chat ID to send messages to
- Automatic notification when all videos downloaded successfully
- Automatic notification when download fails with error details

### Dependencies
- Added `python-telegram-bot>=21.0` for Telegram integration

## [0.1.3] - 2026-01-18

### Added
- Retry mechanism for failed video downloads
- New configuration options:
  - `RETRY_ATTEMPTS` - Number of retry attempts per video (default: 1)
  - `RETRY_DELAY` - Delay in seconds before retry (default: 300 = 5 minutes)
- Clear logging for retry attempts

### Changed
- Download errors now trigger automatic retries before failing
- HTTP 403 and other temporary errors can be recovered with retry mechanism

## [0.1.2] - 2026-01-18

### Fixed
- Fixed video indexing bug: when resuming downloads, video indices now correctly reflect their position in the full playlist, not just among undownloaded videos
- Video filenames now maintain consistent numbering across download sessions

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
