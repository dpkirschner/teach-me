"""Database configuration and connection management for Supabase."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    supabase_url: str
    supabase_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings."""
    logger.debug("Loading database settings")
    settings = DatabaseSettings()
    logger.debug(f"Database settings loaded - URL: {settings.supabase_url[:20]}...")
    return settings


def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    logger.debug("Creating Supabase client")
    settings = get_database_settings()
    logger.debug(f"Using URL: {settings.supabase_url}")
    logger.debug(f"Using key: {settings.supabase_key[:10]}...")
    
    client = create_client(settings.supabase_url, settings.supabase_key)
    logger.debug("Supabase client created successfully")
    return client