"""
Script to acquire and cache the official NOAA/WMO IBTrACS (International Best Track
Archive for Climate Stewardship) dataset for the North Indian Ocean (NI) basin.

Source: NOAA National Centers for Environmental Information (NCEI)
Basin: NI (North Indian Ocean, includes Bay of Bengal & Arabian Sea)
"""

import os
import sys
import logging
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IBTrACS_Downloader")

IBTRACS_NI_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.NI.list.v04r01.csv"
)

DEFAULT_RAW_DIR = Path(__file__).resolve().parent / "raw"
DEFAULT_TARGET_FILE = DEFAULT_RAW_DIR / "ibtracs.NI.list.v04r01.csv"


def download_ibtracs_ni(target_path: Path = DEFAULT_TARGET_FILE, timeout: int = 60) -> Path:
    """
    Downloads the North Indian Ocean IBTrACS CSV archive if not already cached.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and target_path.stat().st_size > 10000:
        logger.info(f"Using cached IBTrACS dataset at: {target_path} ({target_path.stat().st_size / 1024:.1f} KB)")
        return target_path

    logger.info(f"Downloading official IBTrACS NI dataset from: {IBTRACS_NI_URL}")
    try:
        response = requests.get(IBTRACS_NI_URL, stream=True, timeout=timeout)
        response.raise_for_status()

        bytes_written = 0
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)

        logger.info(f"Successfully downloaded IBTrACS NI archive ({bytes_written / 1024:.1f} KB) to {target_path}")
        return target_path

    except Exception as e:
        logger.warning(f"Failed to download IBTrACS dataset from remote: {e}")
        if target_path.exists() and target_path.stat().st_size > 0:
            logger.info("Using existing partial/cached file.")
            return target_path
        raise RuntimeError(
            f"Unable to download IBTrACS NI dataset. Ensure network access or provide file at {target_path}"
        ) from e


if __name__ == "__main__":
    download_ibtracs_ni()
