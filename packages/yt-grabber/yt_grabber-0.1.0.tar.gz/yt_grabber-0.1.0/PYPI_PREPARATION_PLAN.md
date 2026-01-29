# PyPI Publishing Preparation Plan

## Overview
This document outlines the steps needed to prepare yt-grabber for publishing to PyPI.

## Tasks

### 1. Create MIT LICENSE file ✓
- Add the full MIT license text
- Include copyright notice with author "Elisei" and current year

### 2. Update pyproject.toml
- Add `authors = [{name = "Elisei"}]`
- Add `license = {text = "MIT"}`
- Add `repository = "https://github.com/elisey/yt-grabber"`
- Add `keywords` array: ["video", "downloader", "playlist", "cli", "yt-dlp", "media"]
- Add `classifiers`:
  - Development Status :: 4 - Beta
  - Intended Audience :: End Users/Desktop
  - License :: OSI Approved :: MIT License
  - Programming Language :: Python :: 3
  - Programming Language :: Python :: 3.14
  - Topic :: Multimedia :: Video
  - Environment :: Console
  - Operating System :: OS Independent

### 3. Update package description in pyproject.toml
- Change description to avoid trademark: "A CLI tool for downloading videos from playlists and channels"

### 4. Create CHANGELOG.md
- Document version 0.1.0 with current features (avoid trademark)
- Features: extract playlist/channel, sync, download, progress tracking

### 5. Verify .gitignore for packaging
- Ensure dist/ and build/ directories are ignored
- Ensure *.egg-info is ignored

### 6. Create PUBLISHING.md
- Build instructions: `uv build`
- Publish instructions: `uv publish` or `twine upload dist/*`
- Install instructions: `pip install yt-grabber`

## Notes
- Avoid mentioning specific video platform trademarks in package metadata
- Use MIT license as requested
- Repository URL: https://github.com/elisey/yt-grabber
- Author: Elisei (no email)
