"""Configuration management using Pydantic Settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    video_quality: Literal["720", "1080"] = "1080"
    min_delay: int = 1
    max_delay: int = 5
    index_videos: bool
