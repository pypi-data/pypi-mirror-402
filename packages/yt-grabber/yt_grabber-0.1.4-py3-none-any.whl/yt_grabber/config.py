"""Configuration management using Pydantic Settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    video_quality: Literal["720", "1080"] = "1080"
    min_delay: int = 30
    max_delay: int = 60
    index_videos: bool = True
    retry_attempts: int = 1
    retry_delay: int = 300
    telegram_notifications_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
