"""Telegram notification module."""

import asyncio
from typing import Optional

from loguru import logger
from telegram import Bot
from telegram.error import TelegramError


class TelegramNotifier:
    """Sends notifications via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID to send messages to
            enabled: Whether notifications are enabled
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled

        if self.enabled and (not bot_token or not chat_id):
            logger.warning("Telegram notifications enabled but token or chat_id missing")
            self.enabled = False

    async def _send_message(self, message: str) -> None:
        """Send message via Telegram bot.

        Args:
            message: Message text to send
        """
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.debug("Telegram notification sent successfully")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {e}")

    def send_success_notification(self, total_videos: int, playlist_name: str) -> None:
        """Send success notification.

        Args:
            total_videos: Number of videos downloaded
            playlist_name: Name of the playlist
        """
        if not self.enabled:
            return

        message = (
            "✅ *Download Complete*\n\n"
            f"Playlist: `{playlist_name}`\n"
            f"Videos downloaded: *{total_videos}*"
        )

        try:
            asyncio.run(self._send_message(message))
        except Exception as e:
            logger.error(f"Error in send_success_notification: {e}")

    def send_error_notification(self, error_message: str, playlist_name: str) -> None:
        """Send error notification.

        Args:
            error_message: Error message text
            playlist_name: Name of the playlist
        """
        if not self.enabled:
            return

        # Escape markdown special characters in error message
        escaped_error = error_message.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

        message = (
            "❌ *Download Failed*\n\n"
            f"Playlist: `{playlist_name}`\n"
            f"Error: {escaped_error}"
        )

        try:
            asyncio.run(self._send_message(message))
        except Exception as e:
            logger.error(f"Error in send_error_notification: {e}")

    def send_playlist_started_notification(self, playlist_name: str, current: int, total: int) -> None:
        """Send notification when starting a new playlist.

        Args:
            playlist_name: Name of the playlist
            current: Current playlist number
            total: Total number of playlists
        """
        if not self.enabled:
            return

        message = (
            f"📥 *Starting Download* \\[{current}/{total}]\n\n"
            f"Playlist: `{playlist_name}`"
        )

        try:
            asyncio.run(self._send_message(message))
        except Exception as e:
            logger.error(f"Error in send_playlist_started_notification: {e}")

    def send_batch_success_notification(self, total_playlists: int) -> None:
        """Send batch completion success notification.

        Args:
            total_playlists: Number of playlists downloaded
        """
        if not self.enabled:
            return

        message = (
            "✅ *Batch Complete*\n\n"
            f"Successfully downloaded *{total_playlists}* playlists"
        )

        try:
            asyncio.run(self._send_message(message))
        except Exception as e:
            logger.error(f"Error in send_batch_success_notification: {e}")

    def send_batch_error_notification(self, error_context: str) -> None:
        """Send batch download error notification.

        Args:
            error_context: Error context including playlist info
        """
        if not self.enabled:
            return

        # Escape markdown special characters
        escaped_context = error_context.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

        message = (
            "❌ *Batch Download Failed*\n\n"
            f"{escaped_context}"
        )

        try:
            asyncio.run(self._send_message(message))
        except Exception as e:
            logger.error(f"Error in send_batch_error_notification: {e}")
