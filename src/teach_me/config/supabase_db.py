"""Database configuration and connection management for Supabase."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import Client, create_client

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    supabase_url: str | None = None
    supabase_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings."""
    logger.debug("Loading database settings")
    settings = DatabaseSettings()
    url_preview = settings.supabase_url[:20] if settings.supabase_url else "None"
    logger.debug(f"Database settings loaded - URL: {url_preview}...")
    return settings


def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    logger.debug("Creating Supabase client")
    settings = get_database_settings()

    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")
    if not settings.supabase_key:
        raise ValueError("SUPABASE_KEY environment variable is required")

    logger.debug(f"Using URL: {settings.supabase_url}")
    logger.debug(f"Using key: {settings.supabase_key[:10]}...")

    client = create_client(settings.supabase_url, settings.supabase_key)
    logger.debug("Supabase client created successfully")
    return client
