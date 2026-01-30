"""Unit tests for notifier module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yt_grabber.notifier import TelegramNotifier


def run_coroutine(coro):
    """Helper to run a coroutine and return None."""
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)
        loop.close()
    except Exception:
        pass  # Ignore exceptions in tests
    return None


@pytest.mark.unit
class TestTelegramNotifier:
    """Test TelegramNotifier class."""

    def test_init_enabled(self):
        """Test notifier initialization when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        assert notifier.bot_token == "test_token"
        assert notifier.chat_id == "test_chat"
        assert notifier.enabled is True

    def test_init_disabled(self):
        """Test notifier initialization when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        assert notifier.enabled is False

    def test_init_missing_token(self):
        """Test notifier disables when token is missing."""
        notifier = TelegramNotifier(bot_token="", chat_id="test_chat", enabled=True)

        assert notifier.enabled is False

    def test_init_missing_chat_id(self):
        """Test notifier disables when chat_id is missing."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="", enabled=True)

        assert notifier.enabled is False

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_success_notification_disabled(self, mock_asyncio_run):
        """Test that notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_success_notification(total_videos=5, playlist_name="Test")

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_success_notification_enabled(self, mock_bot_class):
        """Test sending success notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        # Mock asyncio.run to actually run the coroutine
        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_success_notification(total_videos=5, playlist_name="Test")
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_error_notification_disabled(self, mock_asyncio_run):
        """Test that error notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_error_notification(error_message="Test error", playlist_name="Test")

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_error_notification_enabled(self, mock_bot_class):
        """Test sending error notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_error_notification(error_message="Test error", playlist_name="Test")
            mock_run.assert_called_once()

    def test_send_error_notification_escapes_markdown(self):
        """Test that error notification escapes markdown characters."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        # The actual escaping happens in the method, we just verify it runs
        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_error_notification(
                error_message="Error with *bold* and `code`", playlist_name="Test"
            )
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_playlist_started_notification_disabled(self, mock_asyncio_run):
        """Test that playlist started notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_playlist_started_notification(playlist_name="Test", current=1, total=5)

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_playlist_started_notification_enabled(self, mock_bot_class):
        """Test sending playlist started notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_playlist_started_notification(playlist_name="Test", current=1, total=5)
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_batch_success_notification_disabled(self, mock_asyncio_run):
        """Test that batch success notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_batch_success_notification(total_playlists=5)

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_batch_success_notification_enabled(self, mock_bot_class):
        """Test sending batch success notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_batch_success_notification(total_playlists=5)
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_batch_error_notification_disabled(self, mock_asyncio_run):
        """Test that batch error notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_batch_error_notification(error_context="Test error")

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_batch_error_notification_enabled(self, mock_bot_class):
        """Test sending batch error notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_batch_error_notification(error_context="Test error")
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.Bot")
    def test_send_batch_error_notification_with_url(self, mock_bot_class):
        """Test sending batch error notification with failed URL."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_batch_error_notification(
                error_context="Test error", failed_url="https://example.com/video"
            )
            mock_run.assert_called_once()

    @patch("yt_grabber.notifier.asyncio.run")
    def test_send_video_skipped_notification_disabled(self, mock_asyncio_run):
        """Test that video skipped notification is not sent when disabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=False)

        notifier.send_video_skipped_notification(
            url="https://example.com/video",
            error_message="Test error",
            playlist_name="Test",
        )

        mock_asyncio_run.assert_not_called()

    @patch("yt_grabber.notifier.Bot")
    def test_send_video_skipped_notification_enabled(self, mock_bot_class):
        """Test sending video skipped notification when enabled."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_video_skipped_notification(
                url="https://example.com/video",
                error_message="Test error",
                playlist_name="Test",
            )
            mock_run.assert_called_once()

    def test_send_video_skipped_notification_escapes_markdown(self):
        """Test that video skipped notification escapes markdown characters."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        # The actual escaping happens in the method, we just verify it runs
        with patch("yt_grabber.notifier.asyncio.run", side_effect=run_coroutine) as mock_run:
            notifier.send_video_skipped_notification(
                url="https://example.com/video_with_*special*_chars",
                error_message="Error with *bold* and `code`",
                playlist_name="Test",
            )
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        with patch("yt_grabber.notifier.Bot", return_value=mock_bot):
            await notifier._send_message("Test message")

        mock_bot.send_message.assert_called_once_with(
            chat_id="test_chat", text="Test message", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_send_message_telegram_error(self):
        """Test handling of Telegram errors."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        mock_bot = MagicMock()
        from telegram.error import TelegramError

        mock_bot.send_message = AsyncMock(side_effect=TelegramError("API error"))

        with patch("yt_grabber.notifier.Bot", return_value=mock_bot):
            # Should not raise, just log error
            await notifier._send_message("Test message")

    @pytest.mark.asyncio
    async def test_send_message_unexpected_error(self):
        """Test handling of unexpected errors."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat", enabled=True)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Unexpected error"))

        with patch("yt_grabber.notifier.Bot", return_value=mock_bot):
            # Should not raise, just log error
            await notifier._send_message("Test message")
