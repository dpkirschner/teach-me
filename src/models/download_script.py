#!/usr/bin/env python3
"""CLI script for downloading HuggingFace models."""

import argparse
import sys
import traceback
from pathlib import Path

# Assuming these are your project's custom modules
from teach_me.utils.logging import setup_teach_me_logger
from .huggingface_downloader import HuggingFaceDownloader, ModelConfig


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = "DEBUG" if verbose else "INFO"
    setup_teach_me_logger(level=level)


def download_single_model(
    downloader: HuggingFaceDownloader,
    repo_id: str,
    force: bool,
    revision: str | None,
) -> None:
    """Download a single model using the provided downloader instance."""
    path = downloader.download_model(
        repo_id=repo_id,
        force_download=force,
        revision=revision,
    )
    print(f"Model downloaded successfully to: {path}")


def download_from_config(downloader: HuggingFaceDownloader, config_path: str) -> None:
    """Download models from a configuration file."""
    results = downloader.download_models_from_config(config_path)

    print("\nDownload Summary:")
    print(f"Successfully downloaded {len(results)} models:")
    for repo_id, path in results.items():
        print(f"  {repo_id} -> {path}")


def download_batch(downloader: HuggingFaceDownloader, repo_ids: list[str]) -> None:
    """Download multiple models in batch."""
    model_configs = [ModelConfig(repo_id=repo_id) for repo_id in repo_ids]
    results = downloader.download_model_batch(model_configs)

    print("\nBatch Download Summary:")
    print(f"Successfully downloaded {len(results)} models:")
    for repo_id, path in results.items():
        print(f"  {repo_id} -> {path}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download HuggingFace models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a single model
  python -m src.models.download_script --repo-id microsoft/DialoGPT-medium

  # Download with custom cache directory (works for all modes)
  python -m src.models.download_script --repo-id microsoft/DialoGPT-medium --cache-dir ./models

  # Download from configuration file
  python -m src.models.download_script --config models_config.yaml

  # Download multiple models
  python -m src.models.download_script --batch microsoft/DialoGPT-medium facebook/bart-large-cnn

  # Force re-download a single model
  python -m src.models.download_script --repo-id microsoft/DialoGPT-medium --force
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo-id", type=str, help="HuggingFace repository ID to download")
    group.add_argument("--config", type=str, help="Path to YAML configuration file")
    group.add_argument("--batch", nargs="+", help="Download multiple models (space-separated repo IDs)")

    parser.add_argument("--cache-dir", type=str, help="Directory to cache downloaded models")
    parser.add_argument("--token", type=str, help="HuggingFace Hub token (overrides env var)")
    parser.add_argument("--force", action="store_true", help="Force re-download (single model only)")
    parser.add_argument("--revision", type=str, help="Model revision (single model only)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging and error tracebacks")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.revision and not args.repo_id:
        parser.error("--revision can only be used with --repo-id")
    if args.force and not args.repo_id:
        parser.error("--force can only be used with --repo-id")

    try:
        downloader = HuggingFaceDownloader(
            token=args.token,
            cache_dir=args.cache_dir
        )

        if args.repo_id:
            download_single_model(
                downloader=downloader,
                repo_id=args.repo_id,
                force=args.force,
                revision=args.revision,
            )
        elif args.config:
            if not Path(args.config).exists():
                print(f"Error: Configuration file '{args.config}' not found", file=sys.stderr)
                sys.exit(1)
            download_from_config(
                downloader=downloader,
                config_path=args.config,
            )
        elif args.batch:
            download_batch(
                downloader=downloader,
                repo_ids=args.batch,
            )
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()