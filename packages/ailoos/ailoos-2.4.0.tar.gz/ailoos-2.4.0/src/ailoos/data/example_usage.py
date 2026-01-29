"""
Example usage of the DatasetDownloader class.
"""

import asyncio
import logging
from pathlib import Path

from .dataset_downloader import DatasetDownloader, DownloadProgress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def progress_callback(progress: DownloadProgress):
    """Example progress callback function."""
    print(".1f"
          ".2f"
          ".1f"
          ".0f")


async def main():
    """Example usage of DatasetDownloader."""

    # Initialize downloader with config file
    config_path = Path(__file__).parent.parent.parent.parent / "massive_datasets_config.yaml"
    downloader = DatasetDownloader(config_path=str(config_path))

    # List available datasets
    print("Available datasets:")
    for dataset_name in downloader.get_available_datasets():
        config = downloader.get_dataset_info(dataset_name)
        print(f"  - {dataset_name}: {config.description} ({config.size})")

    # Download a dataset (using the first available one)
    if downloader.get_available_datasets():
        dataset_name = downloader.get_available_datasets()[0]
        print(f"\nDownloading dataset: {dataset_name}")

        try:
            success = await downloader.download_dataset(
                dataset_name=dataset_name,
                progress_callback=progress_callback,
                force_redownload=False  # Set to True to force redownload
            )

            if success:
                print(f"✅ Successfully downloaded {dataset_name}")
            else:
                print(f"❌ Failed to download {dataset_name}")

        except KeyboardInterrupt:
            print(f"\n🛑 Cancelling download of {dataset_name}")
            await downloader.cancel_download(dataset_name)
        except Exception as e:
            print(f"❌ Error downloading {dataset_name}: {e}")

    # Show active downloads (should be empty now)
    active = downloader.get_active_downloads()
    if active:
        print(f"Active downloads: {active}")
    else:
        print("No active downloads")


if __name__ == "__main__":
    asyncio.run(main())