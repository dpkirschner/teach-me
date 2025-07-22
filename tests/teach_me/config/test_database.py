"""Tests for database configuration."""

import os
from unittest.mock import Mock, patch

import pytest

from teach_me.config.database import (
    DatabaseSettings,
    get_database_settings,
    get_supabase_client,
)


@pytest.mark.unit
class TestDatabaseSettings:
    """Test cases for DatabaseSettings."""

    def test_database_settings_from_env(self):
        """Test DatabaseSettings loading from environment variables."""
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"},
        ):
            settings = DatabaseSettings()

            assert settings.supabase_url == "https://test.supabase.co"
            assert settings.supabase_key == "test-key"

    def test_database_settings_ignores_extra_fields(self):
        """Test DatabaseSettings ignores unknown environment variables."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
                "UNKNOWN_VAR": "should-be-ignored",
            },
        ):
            settings = DatabaseSettings()

            assert settings.supabase_url == "https://test.supabase.co"
            assert settings.supabase_key == "test-key"
            assert not hasattr(settings, "unknown_var")

    def test_get_database_settings_cached(self):
        """Test that get_database_settings returns cached instance."""
        # Clear the cache first
        get_database_settings.cache_clear()

        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"},
        ):
            # First call
            result1 = get_database_settings()
            # Second call
            result2 = get_database_settings()

            # Should return same instance (cached)
            assert result1 is result2

    def test_get_supabase_client_with_mocker(self, mocker):
        """Test get_supabase_client creates client with correct settings."""
        mock_settings = Mock(supabase_url="https://test.supabase.co", supabase_key="test-key")
        mocker.patch("teach_me.config.database.get_database_settings", return_value=mock_settings)

        mock_client = Mock()
        mock_create_client = mocker.patch("teach_me.config.database.create_client", return_value=mock_client)

        result = get_supabase_client()

        assert result is mock_client
        mock_create_client.assert_called_once_with("https://test.supabase.co", "test-key")
