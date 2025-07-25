"""Models package for HuggingFace integration."""

# Initialize logging for the models package
from teach_me.utils.logging import setup_teach_me_logger

from .huggingface_downloader import (
    HuggingFaceDownloader,
    ModelConfig,
    ModelsConfig,
    download_model,
    download_models_from_config,
)

setup_teach_me_logger()

__all__ = [
    "HuggingFaceDownloader",
    "ModelConfig",
    "ModelsConfig",
    "download_model",
    "download_models_from_config",
]
