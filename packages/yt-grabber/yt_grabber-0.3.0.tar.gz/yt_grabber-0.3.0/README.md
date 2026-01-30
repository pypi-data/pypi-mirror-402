# YouTube Grabber

A Python CLI tool for managing and downloading YouTube videos from playlists and channels with automatic progress tracking and synchronization.

## Features

- **Extract videos** from YouTube playlists and channels
- **Sync playlists** with their source to track new and removed videos
- **Download videos** at configurable quality (720p or 1080p)
- **Automatic progress tracking** - marks downloaded, added, and removed videos
- **Smart resume** - skips already downloaded videos
- **Playlist headers** - stores metadata about source, title, and extraction time
- **Random delays** between downloads to avoid rate limiting
- **Colorized logging** with detailed progress information

## Installation

```bash
# Clone or navigate to the project directory
cd yt-grabber

# Install dependencies using uv
uv sync
```

## Commands

### Extract Playlist

Extract video URLs from a YouTube playlist:

```bash
uv run yt-grabber extract-playlist <playlist_url> <output_file>
```

**Examples:**

```bash
# Using full URL
uv run yt-grabber extract-playlist "https://www.youtube.com/playlist?list=PLTj8zGbtGsjHQWtKYupS1CdZzrbbYKkoz" my_playlist.txt

# Using playlist ID only
uv run yt-grabber extract-playlist PLTj8zGbtGsjHQWtKYupS1CdZzrbbYKkoz my_playlist.txt
```

### Extract Channel

Extract video URLs from a YouTube channel (regular videos only, oldest first):

```bash
uv run yt-grabber extract-channel <channel_url> <output_file>
```

**Examples:**

```bash
# Using channel handle
uv run yt-grabber extract-channel @ChannelName channel_videos.txt

# Using full URL
uv run yt-grabber extract-channel "https://www.youtube.com/@ChannelName" channel_videos.txt

# Using channel ID
uv run yt-grabber extract-channel UCxxxxxxxxxxxxxxxxxx channel_videos.txt
```

### Sync Playlist

Synchronize a playlist file with its source to detect new and removed videos:

```bash
uv run yt-grabber sync <playlist_file>
```

**Example:**

```bash
uv run yt-grabber sync my_playlist.txt
```

**What it does:**
- Fetches current videos from the source URL (stored in the playlist header)
- Compares with the existing playlist
- Marks new videos with `A` (added)
- Marks removed videos with `D` (deleted)
- Updates playlist header metadata (timestamp, count, title)
- Shows a diff summary of what changed

### Download

Download videos from a playlist file:

```bash
uv run yt-grabber download <playlist_file>
```

**Example:**

```bash
uv run yt-grabber download my_playlist.txt
```

**What it does:**
- Reads undownloaded and non-removed videos from the playlist
- Downloads each video at configured quality
- Marks successful downloads with `#`
- Creates a metadata CSV file with download information
- Stops on any error

### Download Batch

Download videos from multiple playlist files in a directory:

```bash
uv run yt-grabber download-batch [directory] [--pattern PATTERN] [--sort {asc,desc}]
```

**Arguments:**
- `directory` - Directory containing playlist files (default: current directory `.`)
- `--pattern` / `-p` - Glob pattern for filtering files (default: `*.txt`)
- `--sort` / `-s` - Sort order: `asc` (ascending, default) or `desc` (descending)

**Examples:**

```bash
# Download all .txt playlists in current directory (ascending order)
uv run yt-grabber download-batch

# Download all playlists in 'playlists' directory
uv run yt-grabber download-batch playlists/

# Download only playlists matching pattern
uv run yt-grabber download-batch playlists/ --pattern "gmm*.txt"

# Download season playlists in descending order
uv run yt-grabber download-batch . --pattern "season*.txt" --sort desc
```

**What it does:**
- Finds all playlist files matching the pattern
- Sorts files alphabetically (ascending or descending)
- Processes each playlist in order
- Sends Telegram notification when starting each playlist (if enabled)
- Stops immediately if any playlist fails
- Sends summary notification when all complete

**Use cases:**
- Download entire TV show seasons: `season_01.txt`, `season_02.txt`, etc.
- Process multiple music playlists: `gmm_s27.txt`, `gmm_s28.txt`, etc.
- Batch process all playlists in a directory

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Available settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `VIDEO_QUALITY` | Video quality: `720` or `1080` | `1080` |
| `MIN_DELAY` | Minimum delay between downloads (seconds) | `1` |
| `MAX_DELAY` | Maximum delay between downloads (seconds) | `5` |
| `INDEX_VIDEOS` | Add numeric prefix to filenames | `false` |
| `RETRY_ATTEMPTS` | Number of retry attempts per video | `1` |
| `RETRY_DELAY` | Delay before retry (seconds) | `300` |
| `TELEGRAM_NOTIFICATIONS_ENABLED` | Enable Telegram notifications | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather | - |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | - |

## Playlist File Format

### Header Section (Optional)

Playlists extracted with `extract-playlist` or `extract-channel` contain a header:

```
: Source URL: https://www.youtube.com/playlist?list=PLxxxxx
: Extraction Timestamp: 2026-01-18T14:00:00.000000
: Total Videos: 50
: Source Type: playlist
: Title: My Awesome Playlist
: Extractor Version: 0.1.0
:
```

### Video URLs with Markers

Videos can have status markers (space-separated):

```
https://www.youtube.com/watch?v=VIDEO_ID_1
A https://www.youtube.com/watch?v=VIDEO_ID_2
D https://www.youtube.com/watch?v=VIDEO_ID_3
# https://www.youtube.com/watch?v=VIDEO_ID_4
A # https://www.youtube.com/watch?v=VIDEO_ID_5
D # https://www.youtube.com/watch?v=VIDEO_ID_6
```

**Markers:**
- `#` - Downloaded
- `A` - Added (new video detected during sync)
- `D` - Deleted (removed from source during sync)
- `A #` - Added and downloaded
- `D #` - Deleted but was previously downloaded

**Behavior:**
- Lines starting with `:` are header metadata (skipped during download)
- Videos with `D` marker are skipped during download
- Videos with `#` marker are skipped during download
- Only unmarked or `A`-only videos will be downloaded

## Typical Workflow

### 1. Extract a Playlist

```bash
uv run yt-grabber extract-playlist PLxxxxxxxxxx my_music.txt
```

Creates `my_music.txt` with header and all video URLs.

### 2. Download Videos

```bash
uv run yt-grabber download my_music.txt
```

Downloads all videos and marks them with `#`.

### 3. Sync to Check for Updates

```bash
uv run yt-grabber sync my_music.txt
```

Checks the source playlist and:
- Marks new videos with `A`
- Marks removed videos with `D`
- Shows a summary of changes

### 4. Download New Videos

```bash
uv run yt-grabber download my_music.txt
```

Downloads only the newly added videos (marked with `A`).

## Output

### Download Location

Videos are saved to: `download/{playlist_filename}/`

For example, if playlist file is `my_music.txt`, videos go to: `download/my_music/`

### Metadata

A `metadata.csv` file is created in the download directory with:

```csv
url,filename,timestamp
https://www.youtube.com/watch?v=xxxxx,01 Video Title.mp4,2026-01-18T14:30:00
```

## Requirements

- Python 3.12+
- uv package manager
- Dependencies:
  - yt-dlp (video extraction and download)
  - typer (CLI framework)
  - pydantic-settings (configuration)
  - loguru (logging)

## Error Handling

The program stops immediately if:
- A video fails to download
- The playlist file is not found
- Playlist has no header (for sync command)
- Source URL cannot be accessed
- Any unexpected error occurs

This ensures data integrity and prevents partial operations.

## Telegram Notifications

Get notified when downloads complete or fail.

### Setup

1. **Create a Telegram Bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID:**
   - Message [@userinfobot](https://t.me/userinfobot) or [@getmyid_bot](https://t.me/getmyid_bot)
   - It will reply with your chat ID (a number like `123456789`)

3. **Start a Chat with Your Bot:**
   - Find your bot in Telegram search
   - Press "Start" button

4. **Configure:**
   ```bash
   TELEGRAM_NOTIFICATIONS_ENABLED=true
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

### Notification Examples

**Success:**
```
✅ Download Complete

Playlist: my_music
Videos downloaded: 15
```

**Error:**
```
❌ Download Failed

Playlist: my_music
Error: HTTP Error 403: Forbidden
```

## Tips

- Use `extract-channel` for channels to get oldest videos first
- Run `sync` periodically to track playlist changes
- Videos marked with `D` are kept in the file for history
- The `#` marker is preserved across syncs
- Once a video is downloaded (`#`), the `A` marker is cleared
