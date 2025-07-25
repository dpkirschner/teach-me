"""HuggingFace model downloader functionality."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download, snapshot_download
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
from pydantic import BaseModel, Field

from teach_me.utils.logging import get_teach_me_logger

# Load environment variables
load_dotenv()

logger = get_teach_me_logger("models")


class ModelConfig(BaseModel):
    """Configuration for a single model download."""

    repo_id: str = Field(..., description="HuggingFace repository ID")
    revision: str | None = Field(None, description="Specific revision/branch/tag to download")
    allow_patterns: list[str] | None = Field(None, description="File patterns to include")
    ignore_patterns: list[str] | None = Field(None, description="File patterns to exclude")


class ModelsConfig(BaseModel):
    """Configuration for multiple model downloads."""

    models: list[ModelConfig] = Field(..., description="List of models to download")
    cache_dir: str | None = Field(None, description="Directory to cache downloaded models")


class HuggingFaceDownloader:
    """Downloads models from HuggingFace Hub with authentication and caching."""

    def __init__(self, token: str | None = None, cache_dir: str | None = None):
        """
        Initialize the downloader.

        Args:
            token: HuggingFace Hub token. If None, loads from HUGGINGFACE_HUB_TOKEN env var.
            cache_dir: Directory to cache models. If None, uses HuggingFace default.
        """
        self.token = token or os.getenv("HUGGINGFACE_HUB_TOKEN")
        self.cache_dir = cache_dir

        if not self.token:
            logger.warning(
                "No HuggingFace token provided. Only public models will be accessible. "
                "Set HUGGINGFACE_HUB_TOKEN environment variable for private models."
            )

    def download_model(
        self,
        repo_id: str,
        cache_dir: str | None = None,
        force_download: bool = False,
        local_files_only: bool = False,
        revision: str | None = None,
        allow_patterns: str | list[str] | None = None,
        ignore_patterns: str | list[str] | None = None,
    ) -> str:
        """
        Download a complete model from HuggingFace Hub.

        Args:
            repo_id: HuggingFace repository ID (e.g., 'microsoft/DialoGPT-medium')
            cache_dir: Directory to cache the model. Overrides instance cache_dir.
            force_download: Force re-download even if cached
            local_files_only: Use only local cached files
            revision: Specific revision/branch/tag to download
            allow_patterns: File patterns to include in download
            ignore_patterns: File patterns to exclude from download

        Returns:
            Path to the downloaded model directory

        Raises:
            RepositoryNotFoundError: If repository doesn't exist or is private without token
            HfHubHTTPError: For other HTTP errors
            ValueError: For invalid parameters
        """
        if not repo_id:
            raise ValueError("repo_id cannot be empty")

        effective_cache_dir = cache_dir or self.cache_dir

        logger.info(f"Downloading model: {repo_id}")
        if revision:
            logger.info(f"  Revision: {revision}")
        if effective_cache_dir:
            logger.info(f"  Cache directory: {effective_cache_dir}")

        try:
            model_path = snapshot_download(
                repo_id=repo_id,
                cache_dir=effective_cache_dir,
                force_download=force_download,
                local_files_only=local_files_only,
                token=self.token,
                revision=revision,
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )

            logger.info(f"Model downloaded successfully to: {model_path}")
            return model_path

        except RepositoryNotFoundError:
            error_msg = f"Repository '{repo_id}' not found or not accessible"
            if not self.token:
                error_msg += ". For private repositories, provide a HuggingFace token."
            logger.error(error_msg)
            raise

        except HfHubHTTPError as e:
            logger.error(f"HTTP error downloading model '{repo_id}': {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error downloading model '{repo_id}': {e}")
            raise

    def download_file(
        self,
        repo_id: str,
        filename: str,
        cache_dir: str | None = None,
        force_download: bool = False,
        local_files_only: bool = False,
        revision: str | None = None,
    ) -> str:
        """
        Download a single file from HuggingFace Hub.

        Args:
            repo_id: HuggingFace repository ID
            filename: Name of the file to download
            cache_dir: Directory to cache the file. Overrides instance cache_dir.
            force_download: Force re-download even if cached
            local_files_only: Use only local cached files
            revision: Specific revision/branch/tag to download from

        Returns:
            Path to the downloaded file

        Raises:
            RepositoryNotFoundError: If repository doesn't exist or is private without token
            HfHubHTTPError: For other HTTP errors
            ValueError: For invalid parameters
        """
        if not repo_id:
            raise ValueError("repo_id cannot be empty")
        if not filename:
            raise ValueError("filename cannot be empty")

        effective_cache_dir = cache_dir or self.cache_dir

        logger.info(f"Downloading file: {filename} from {repo_id}")

        try:
            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=effective_cache_dir,
                force_download=force_download,
                local_files_only=local_files_only,
                token=self.token,
                revision=revision,
            )

            logger.info(f"File downloaded successfully to: {file_path}")
            return file_path

        except RepositoryNotFoundError:
            error_msg = f"Repository '{repo_id}' or file '{filename}' not found"
            if not self.token:
                error_msg += ". For private repositories, provide a HuggingFace token."
            logger.error(error_msg)
            raise

        except HfHubHTTPError as e:
            logger.error(f"HTTP error downloading file '{filename}' from '{repo_id}': {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error downloading file '{filename}' from '{repo_id}': {e}")
            raise

    def download_model_batch(
        self,
        models_to_download: list[ModelConfig],
        cache_dir: str | None = None,
    ) -> dict[str, str]:
        if not models_to_download:
            raise ValueError("models_to_download list cannot be empty")

        results = {}
        errors = {}
        effective_cache_dir = cache_dir or self.cache_dir

        logger.info(f"Starting batch download of {len(models_to_download)} models")

        for model_conf in models_to_download:
            try:
                path = self.download_model(
                    repo_id=model_conf.repo_id,
                    cache_dir=effective_cache_dir,
                    revision=model_conf.revision,
                    allow_patterns=model_conf.allow_patterns,
                    ignore_patterns=model_conf.ignore_patterns,
                )
                results[model_conf.repo_id] = path
            except Exception as e:
                logger.error(f"Failed to download model '{model_conf.repo_id}': {e}")
                errors[model_conf.repo_id] = str(e)

        logger.info(f"Batch download completed. Success: {len(results)}, Errors: {len(errors)}")
        if errors:
            logger.warning(f"Some models failed to download: {list(errors.keys())}")

        return results

    def download_models_from_config(self, config_path: str) -> dict[str, str]:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file: {config_path}") from e

        try:
            config = ModelsConfig(**config_data)
        except Exception as e:  # Consider catching pydantic.ValidationError specifically
            raise ValueError("Invalid config structure") from e

        return self.download_model_batch(models_to_download=config.models, cache_dir=config.cache_dir)


# Convenience functions for common use cases
def download_model(
    repo_id: str,
    cache_dir: str | None = None,
    force_download: bool = False,
    local_files_only: bool = False,
    token: str | None = None,
    revision: str | None = None,
    allow_patterns: str | list[str] | None = None,
    ignore_patterns: str | list[str] | None = None,
) -> str:
    downloader = HuggingFaceDownloader(token=token, cache_dir=cache_dir)
    return downloader.download_model(
        repo_id=repo_id,
        force_download=force_download,
        local_files_only=local_files_only,
        revision=revision,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
    )


def download_models_from_config(config_path: str, token: str | None = None) -> dict[str, str]:
    """
    Convenience function to download models from a configuration file.

    Args:
        config_path: Path to YAML configuration file
        token: HuggingFace Hub token

    Returns:
        Dictionary mapping repo_id to downloaded path
    """
    downloader = HuggingFaceDownloader(token=token)
    return downloader.download_models_from_config(config_path)
