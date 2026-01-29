"""Auto-update checker for NorthServing."""

import os
from datetime import datetime
from typing import Optional

import requests
from packaging import version as pkg_version
from importlib.metadata import version as get_version

from northserve.constants import UPDATE_MARKER_FILE
from northserve.utils.logger import get_logger

logger = get_logger(__name__)

# Get current version from package metadata
CURRENT_VERSION = get_version("northserve")

# PyPI server configuration
PYPI_PACKAGE_NAME = "northserve"
# Support custom PyPI server via environment variable
PYPI_SERVER = os.getenv("PYPI_SERVER", "http://10.51.6.7:31624")
PYPI_API_URL = f"{PYPI_SERVER}/pypi/{PYPI_PACKAGE_NAME}/json"


def get_latest_version() -> Optional[str]:
    """
    Get the latest version from PyPI.

    Returns:
        Latest version string, or None if unable to fetch
    """
    try:
        # Disable SSL verification for private PyPI server
        response = requests.get(PYPI_API_URL, timeout=5, verify=False)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except Exception as e:
        logger.debug(f"Failed to fetch latest version from PyPI: {e}")
        return None


def compare_versions(current: str, latest: str) -> bool:
    """
    Compare two version strings.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest > current, False otherwise
    """
    return pkg_version.parse(latest) > pkg_version.parse(current)


def check_update() -> None:
    """
    Check for updates from PyPI.

    This function is currently disabled and does nothing.
    Auto-update checking has been turned off.
    """
    # Auto-update checking is disabled
    return


def skip_update_check() -> bool:
    """
    Check if update check should be skipped.

    Returns:
        True if update check should be skipped, False otherwise
    """
    # Skip if NORTHSERVE_SKIP_UPDATE is set
    return os.getenv("NORTHSERVE_SKIP_UPDATE", "").lower() in ("1", "true", "yes")


