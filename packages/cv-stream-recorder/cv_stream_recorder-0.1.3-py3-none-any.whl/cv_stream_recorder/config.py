from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    SEGMENT_LENGTH: int = Field(default=60, description="Default length of each segment in seconds")
    MAX_DURATION: int = Field(default=180, description="Default maximum duration of recording in seconds")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton accessor.
    - Lazily creates a single Settings instance on first call.
    - Subsequent calls return the same instance (per process).
    - Safe for typical multi-threaded use.
    """
    return Settings()


def reset_settings_cache() -> None:
    """
    Clear the singleton cache.
    Useful for unit tests or hot-reloading after changing ENV/.env.
    """
    get_settings.cache_clear()


settings = get_settings()
