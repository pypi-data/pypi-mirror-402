"""Unit tests for config module."""

import os
from pathlib import Path

import pytest

from yt_grabber.config import Settings


@pytest.mark.unit
class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self, monkeypatch, tmp_path):
        """Test default settings values."""
        # Change to tmp directory to avoid loading project .env
        monkeypatch.chdir(tmp_path)

        settings = Settings()

        assert settings.video_quality == "1080"
        assert settings.min_delay == 30
        assert settings.max_delay == 60
        assert settings.index_videos is True
        assert settings.retry_attempts == 1
        assert settings.retry_delay == 300
        assert settings.telegram_notifications_enabled is False
        assert settings.telegram_bot_token == ""
        assert settings.telegram_chat_id == ""

    def test_custom_video_quality_720(self):
        """Test setting video quality to 720."""
        settings = Settings(video_quality="720")

        assert settings.video_quality == "720"

    def test_custom_video_quality_1080(self):
        """Test setting video quality to 1080."""
        settings = Settings(video_quality="1080")

        assert settings.video_quality == "1080"

    def test_custom_delays(self):
        """Test custom delay settings."""
        settings = Settings(min_delay=10, max_delay=20)

        assert settings.min_delay == 10
        assert settings.max_delay == 20

    def test_zero_delays(self):
        """Test zero delay settings (no delay)."""
        settings = Settings(min_delay=0, max_delay=0)

        assert settings.min_delay == 0
        assert settings.max_delay == 0

    def test_index_videos_disabled(self):
        """Test disabling video indexing."""
        settings = Settings(index_videos=False)

        assert settings.index_videos is False

    def test_retry_settings(self):
        """Test retry configuration."""
        settings = Settings(retry_attempts=3, retry_delay=600)

        assert settings.retry_attempts == 3
        assert settings.retry_delay == 600

    def test_retry_disabled(self):
        """Test retry disabled (0 attempts)."""
        settings = Settings(retry_attempts=0, retry_delay=0)

        assert settings.retry_attempts == 0
        assert settings.retry_delay == 0

    def test_telegram_notifications_enabled(self):
        """Test enabling Telegram notifications."""
        settings = Settings(
            telegram_notifications_enabled=True,
            telegram_bot_token="test_token_123",
            telegram_chat_id="123456789",
        )

        assert settings.telegram_notifications_enabled is True
        assert settings.telegram_bot_token == "test_token_123"
        assert settings.telegram_chat_id == "123456789"

    def test_settings_from_env(self, tmp_path: Path, monkeypatch):
        """Test loading settings from environment variables."""
        # Set environment variables
        monkeypatch.setenv("VIDEO_QUALITY", "720")
        monkeypatch.setenv("MIN_DELAY", "5")
        monkeypatch.setenv("MAX_DELAY", "10")
        monkeypatch.setenv("INDEX_VIDEOS", "false")
        monkeypatch.setenv("RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("RETRY_DELAY", "120")
        monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "true")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "env_chat_id")

        settings = Settings()

        assert settings.video_quality == "720"
        assert settings.min_delay == 5
        assert settings.max_delay == 10
        assert settings.index_videos is False
        assert settings.retry_attempts == 5
        assert settings.retry_delay == 120
        assert settings.telegram_notifications_enabled is True
        assert settings.telegram_bot_token == "env_token"
        assert settings.telegram_chat_id == "env_chat_id"

    def test_settings_from_env_file(self, tmp_path: Path, monkeypatch):
        """Test loading settings from .env file."""
        # Clear any environment variables first
        for key in ['VIDEO_QUALITY', 'MIN_DELAY', 'MAX_DELAY', 'INDEX_VIDEOS',
                    'RETRY_ATTEMPTS', 'RETRY_DELAY', 'TELEGRAM_NOTIFICATIONS_ENABLED',
                    'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']:
            monkeypatch.delenv(key, raising=False)

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """VIDEO_QUALITY=720
MIN_DELAY=15
MAX_DELAY=30
INDEX_VIDEOS=false
RETRY_ATTEMPTS=2
RETRY_DELAY=180
TELEGRAM_NOTIFICATIONS_ENABLED=true
TELEGRAM_BOT_TOKEN=file_token
TELEGRAM_CHAT_ID=file_chat_id
"""
        )

        # Change to tmp directory so Settings finds the .env file
        monkeypatch.chdir(tmp_path)

        settings = Settings()

        assert settings.video_quality == "720"
        assert settings.min_delay == 15
        assert settings.max_delay == 30
        assert settings.index_videos is False
        assert settings.retry_attempts == 2
        assert settings.retry_delay == 180
        assert settings.telegram_notifications_enabled is True
        assert settings.telegram_bot_token == "file_token"
        assert settings.telegram_chat_id == "file_chat_id"

    def test_explicit_values_override_defaults(self):
        """Test that explicitly provided values override defaults."""
        settings = Settings(
            video_quality="720",
            min_delay=0,
            max_delay=0,
            index_videos=False,
            retry_attempts=0,
            retry_delay=0,
        )

        assert settings.video_quality == "720"
        assert settings.min_delay == 0
        assert settings.max_delay == 0
        assert settings.index_videos is False
        assert settings.retry_attempts == 0
        assert settings.retry_delay == 0
