"""Tests for HuggingFace downloader functionality."""

import os
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
from pydantic import ValidationError

from src.models.huggingface_downloader import (
    HuggingFaceDownloader,
    ModelConfig,
    ModelsConfig,
    download_model,
    download_models_from_config,
)


class TestModelConfig:
    """Test ModelConfig pydantic model."""

    def test_model_config_valid(self):
        """Test valid ModelConfig creation."""
        config = ModelConfig(repo_id="microsoft/DialoGPT-medium")
        assert config.repo_id == "microsoft/DialoGPT-medium"
        assert config.revision is None
        assert config.allow_patterns is None
        assert config.ignore_patterns is None

    def test_model_config_with_all_fields(self):
        """Test ModelConfig with all fields."""
        config = ModelConfig(
            repo_id="microsoft/DialoGPT-medium",
            revision="main",
            allow_patterns=["*.json"],
            ignore_patterns=["*.bin"],
        )
        assert config.repo_id == "microsoft/DialoGPT-medium"
        assert config.revision == "main"
        assert config.allow_patterns == ["*.json"]
        assert config.ignore_patterns == ["*.bin"]

    def test_model_config_missing_repo_id(self):
        """Test ModelConfig fails without repo_id."""
        with pytest.raises(ValidationError):
            ModelConfig()


class TestModelsConfig:
    """Test ModelsConfig pydantic model."""

    def test_models_config_valid(self):
        """Test valid ModelsConfig creation."""
        config = ModelsConfig(
            models=[
                ModelConfig(repo_id="microsoft/DialoGPT-medium"),
                ModelConfig(repo_id="facebook/bart-large-cnn"),
            ]
        )
        assert len(config.models) == 2
        assert config.models[0].repo_id == "microsoft/DialoGPT-medium"
        assert config.models[1].repo_id == "facebook/bart-large-cnn"

    def test_models_config_with_cache_dir(self):
        """Test ModelsConfig with cache directory."""
        config = ModelsConfig(
            models=[ModelConfig(repo_id="microsoft/DialoGPT-medium")], cache_dir="/app/models"
        )
        assert config.cache_dir == "/app/models"


class TestHuggingFaceDownloader:
    """Test HuggingFaceDownloader class."""

    def test_init_with_token(self):
        """Test downloader initialization with token."""
        downloader = HuggingFaceDownloader(token="test_token")
        assert downloader.token == "test_token"
        assert downloader.cache_dir is None

    def test_init_with_cache_dir(self):
        """Test downloader initialization with cache directory."""
        downloader = HuggingFaceDownloader(cache_dir="/tmp/models")
        assert downloader.cache_dir == "/tmp/models"

    @patch.dict(os.environ, {"HUGGINGFACE_HUB_TOKEN": "env_token"})
    def test_init_with_env_token(self):
        """Test downloader gets token from environment."""
        downloader = HuggingFaceDownloader()
        assert downloader.token == "env_token"

    @patch("src.models.huggingface_downloader.snapshot_download")
    def test_download_model_success(self, mock_snapshot):
        """Test successful model download."""
        mock_snapshot.return_value = "/path/to/model"

        downloader = HuggingFaceDownloader(token="test_token")
        result = downloader.download_model("microsoft/DialoGPT-medium")

        assert result == "/path/to/model"
        mock_snapshot.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium",
            cache_dir=None,
            force_download=False,
            local_files_only=False,
            token="test_token",
            revision=None,
            allow_patterns=None,
            ignore_patterns=None,
        )

    @patch("src.models.huggingface_downloader.snapshot_download")
    def test_download_model_with_options(self, mock_snapshot):
        """Test model download with all options."""
        mock_snapshot.return_value = "/path/to/model"

        downloader = HuggingFaceDownloader(token="test_token", cache_dir="/tmp")
        result = downloader.download_model(
            repo_id="microsoft/DialoGPT-medium",
            cache_dir="/custom/cache",
            force_download=True,
            local_files_only=True,
            revision="main",
            allow_patterns=["*.json"],
            ignore_patterns=["*.bin"],
        )

        assert result == "/path/to/model"
        mock_snapshot.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium",
            cache_dir="/custom/cache",
            force_download=True,
            local_files_only=True,
            token="test_token",
            revision="main",
            allow_patterns=["*.json"],
            ignore_patterns=["*.bin"],
        )

    def test_download_model_empty_repo_id(self):
        """Test download fails with empty repo_id."""
        downloader = HuggingFaceDownloader()

        with pytest.raises(ValueError, match="repo_id cannot be empty"):
            downloader.download_model("")

    @patch("src.models.huggingface_downloader.snapshot_download")
    def test_download_model_repository_not_found(self, mock_snapshot):
        """Test download handles repository not found error."""
        mock_snapshot.side_effect = RepositoryNotFoundError("Repository not found")

        downloader = HuggingFaceDownloader()

        with pytest.raises(RepositoryNotFoundError):
            downloader.download_model("nonexistent/model")

    @patch("src.models.huggingface_downloader.snapshot_download")
    def test_download_model_http_error(self, mock_snapshot):
        """Test download handles HTTP error."""
        mock_snapshot.side_effect = HfHubHTTPError("HTTP error")

        downloader = HuggingFaceDownloader()

        with pytest.raises(HfHubHTTPError):
            downloader.download_model("microsoft/DialoGPT-medium")

    @patch("src.models.huggingface_downloader.hf_hub_download")
    def test_download_file_success(self, mock_download):
        """Test successful file download."""
        mock_download.return_value = "/path/to/file.json"

        downloader = HuggingFaceDownloader(token="test_token")
        result = downloader.download_file("microsoft/DialoGPT-medium", "config.json")

        assert result == "/path/to/file.json"
        mock_download.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium",
            filename="config.json",
            cache_dir=None,
            force_download=False,
            local_files_only=False,
            token="test_token",
            revision=None,
        )

    def test_download_file_empty_filename(self):
        """Test file download fails with empty filename."""
        downloader = HuggingFaceDownloader()

        with pytest.raises(ValueError, match="filename cannot be empty"):
            downloader.download_file("microsoft/DialoGPT-medium", "")

    @patch("src.models.huggingface_downloader.yaml.safe_load")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.models.huggingface_downloader.Path.exists")
    def test_download_models_from_config_success(self, mock_exists, mock_file, mock_yaml):
        """Test successful download from config file."""
        # Mock file exists
        mock_exists.return_value = True

        mock_yaml.return_value = {
            "models": [{"repo_id": "microsoft/DialoGPT-medium"}, {"repo_id": "facebook/bart-large-cnn"}]
        }

        downloader = HuggingFaceDownloader()

        with patch.object(downloader, "download_model_batch") as mock_batch:
            mock_batch.return_value = {
                "microsoft/DialoGPT-medium": "/path/1",
                "facebook/bart-large-cnn": "/path/2",
            }

            result = downloader.download_models_from_config("config.yaml")

            assert len(result) == 2
            assert "microsoft/DialoGPT-medium" in result
            assert "facebook/bart-large-cnn" in result

    def test_download_models_from_config_file_not_found(self):
        """Test config download fails when file doesn't exist."""
        downloader = HuggingFaceDownloader()

        with pytest.raises(FileNotFoundError):
            downloader.download_models_from_config("nonexistent.yaml")

    @patch("builtins.open", new_callable=mock_open, read_data="models: [repo_id: 'bad-yaml'")
    @patch("src.models.huggingface_downloader.Path.exists")
    def test_download_models_from_config_malformed_yaml(self, mock_exists, mock_file):
        """Test config download fails with invalid YAML."""
        mock_exists.return_value = True
        downloader = HuggingFaceDownloader()
        with pytest.raises(yaml.YAMLError):
            downloader.download_models_from_config("config.yaml")

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("src.models.huggingface_downloader.Path.exists")
    def test_download_models_from_config_invalid_schema(self, mock_exists, mock_file):
        """Test config download fails with invalid schema."""
        mock_exists.return_value = True
        downloader = HuggingFaceDownloader()
        with pytest.raises(ValueError, match="Invalid config structure"):
            downloader.download_models_from_config("config.yaml")

    def test_download_model_batch_success(self):
        """Test successful batch download."""
        downloader = HuggingFaceDownloader()

        with patch.object(downloader, "download_model") as mock_download:
            mock_download.side_effect = ["/path/1", "/path/2"]

            model_configs = [
                ModelConfig(repo_id="microsoft/DialoGPT-medium"),
                ModelConfig(repo_id="facebook/bart-large-cnn"),
            ]

            result = downloader.download_model_batch(model_configs)

            assert len(result) == 2
            assert result["microsoft/DialoGPT-medium"] == "/path/1"
            assert result["facebook/bart-large-cnn"] == "/path/2"

    def test_download_model_batch_empty_list(self):
        """Test batch download fails with empty list."""
        downloader = HuggingFaceDownloader()

        with pytest.raises(ValueError, match="models_to_download list cannot be empty"):
            downloader.download_model_batch([])

    def test_download_model_batch_with_errors(self):
        """Test batch download handles partial failures."""
        downloader = HuggingFaceDownloader()

        with patch.object(downloader, "download_model") as mock_download:
            mock_download.side_effect = ["/path/1", RepositoryNotFoundError("Not found")]

            model_configs = [
                ModelConfig(repo_id="microsoft/DialoGPT-medium"),
                ModelConfig(repo_id="nonexistent/model"),
            ]

            result = downloader.download_model_batch(model_configs)

            assert len(result) == 1
            assert result["microsoft/DialoGPT-medium"] == "/path/1"
            assert "nonexistent/model" not in result


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch("src.models.huggingface_downloader.HuggingFaceDownloader")
    def test_download_model(self, mock_downloader_class):
        """Test download_model convenience function."""
        mock_downloader = Mock()
        mock_downloader.download_model.return_value = "/path/to/model"
        mock_downloader_class.return_value = mock_downloader

        result = download_model("microsoft/DialoGPT-medium")

        assert result == "/path/to/model"
        mock_downloader_class.assert_called_once_with(token=None, cache_dir=None)
        mock_downloader.download_model.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium",
            force_download=False,
            local_files_only=False,
            revision=None,
            allow_patterns=None,
            ignore_patterns=None,
        )

    @patch("src.models.huggingface_downloader.HuggingFaceDownloader")
    def test_download_models_from_config(self, mock_downloader_class):
        """Test download_models_from_config convenience function."""
        mock_downloader = Mock()
        mock_downloader.download_models_from_config.return_value = {"model": "/path"}
        mock_downloader_class.return_value = mock_downloader

        result = download_models_from_config("config.yaml")

        assert result == {"model": "/path"}
        mock_downloader_class.assert_called_once_with(token=None)
        mock_downloader.download_models_from_config.assert_called_once_with("config.yaml")
