# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2026-01-21

### Fixed
- **HTTP 503 error classification:** Fixed bug where "HTTP Error 503: Service Unavailable" was incorrectly classified as non-retryable error. HTTP 503 errors are now properly treated as retryable (temporary server issues) and will trigger the retry mechanism with linear backoff.
- **Error pattern specificity:** Refined non-retryable error patterns to be more specific (`"unavailable"` → `"video unavailable"`) to avoid false positives with HTTP errors while maintaining detection of actual video unavailability.

## [0.3.1] - 2026-01-21

### Added
- **CLI version command:** Added `--version` / `-v` flag to display current version

### Changed
- **Error log location:** `error_log.csv` is now saved in the current directory (where the utility is launched) instead of inside each playlist's download directory for easier access and centralized error tracking
- **Version management:** Version is now defined only in `pyproject.toml` and automatically loaded via `importlib.metadata` (no need to update `__init__.py` manually)

### Fixed
- Added `error_log.csv` to `.gitignore` to prevent committing error logs

## [0.3.0] - 2026-01-21

### Added
- **Development tooling:**
  - Added ruff for code formatting and linting (replaces Black, isort, flake8)
  - Added mypy for static type checking with strict mode
  - Added pre-commit hooks for automated code quality checks
  - Added Taskfile for task management (lint, format, type-check, test, ci, fix)
- **Smart error handling for non-retryable errors:**
  - Automatic detection of errors that won't benefit from retry (age verification, login required, private videos, etc.)
  - Special notification when video is skipped due to non-retryable error
  - Error logging to CSV with classification (RETRYABLE vs NON_RETRYABLE)
  - Videos with non-retryable errors are marked as downloaded and skipped in future runs
  - Download process continues after skipping non-retryable errors (doesn't halt entire playlist)
- **Enhanced batch error notifications:**
  - Batch failure notifications now include the URL of the video that caused the failure

### Changed
- **Linear backoff for retry mechanism:**
  - Retry delays now increase proportionally to attempt number (5s, 10s, 15s, etc.)
  - Gives rate-limited services more time to reset between attempts
- **Improved test coverage:**
  - Added comprehensive tests for non-retryable error handling
  - Added tests for linear backoff retry mechanism
  - Added tests for Telegram notifications
  - Achieved 94% test coverage (167 tests)

### Fixed
- Bot detection errors (e.g., "confirm you're not a bot") are now treated as retryable (was incorrectly classified as non-retryable)
- Removed pytest warnings from async notification tests

### Technical
- Code quality improvements with ruff (line length: 100, Python 3.12 target)
- Type safety with mypy strict mode
- Pre-commit hooks ensure code quality before commits
- Custom exception `NonRetryableError` for better error handling

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
