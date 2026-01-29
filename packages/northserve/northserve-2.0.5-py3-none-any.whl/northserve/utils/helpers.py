"""Helper utility functions."""

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from northserve.constants import INFRAWAVES_USERNAME, INFRAWAVES_PASSWORD
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


def load_config_file() -> Dict[str, str]:
    """
    Load user configuration from environment variables.

    Returns:
        Dictionary containing username and password

    Raises:
        ValueError: If required environment variables are not set

    Environment Variables:
        INFRAWAVES_USERNAME: Your username
        INFRAWAVES_PASSWORD: Your password
    """
    username = INFRAWAVES_USERNAME
    password = INFRAWAVES_PASSWORD

    if not username or not password:
        raise ValueError(
            "Missing required environment variables.\n"
            "Please set INFRAWAVES_USERNAME and INFRAWAVES_PASSWORD:\n"
            "  export INFRAWAVES_USERNAME='your_username'\n"
            "  export INFRAWAVES_PASSWORD='your_password'\n"
            "\n"
            "Or add them to your shell profile (~/.bashrc or ~/.zshrc)"
        )

    return {
        "username": username,
        "password": password,
    }


def confirm_action(message: str, skip_check: bool = False) -> bool:
    """
    Ask user for confirmation.

    Args:
        message: Message to display
        skip_check: If True, automatically return True

    Returns:
        True if user confirmed, False otherwise
    """
    if skip_check:
        return True

    response = input(f"{message} (y/n): ").strip().lower()
    return response in ("y", "yes")


def generate_deployment_uuid() -> str:
    """
    Generate a unique UUID for deployment.

    Returns:
        UUID string without hyphens
    """
    return uuid.uuid4().hex


def run_kubectl_command(args: list, namespace: Optional[str] = None) -> subprocess.CompletedProcess:
    """
    Run a kubectl command.

    Args:
        args: kubectl command arguments
        namespace: Kubernetes namespace (optional)

    Returns:
        CompletedProcess instance

    Raises:
        subprocess.CalledProcessError: If command fails
    """
    cmd = ["kubectl"] + args
    if namespace:
        cmd.extend(["-n", namespace])

    logger.debug(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )

    return result


def get_base_path() -> Path:
    """
    Get the base path of the NorthServing installation.

    Returns:
        Path to base directory
    """
    # Try to get from environment variable first
    base_path = os.getenv("NORTHSERVE_BASE_PATH")
    if base_path:
        return Path(base_path)

    # Otherwise use the package location
    return Path(__file__).parent.parent.parent


def create_temp_yaml_folder() -> Path:
    """
    Create a temporary folder for YAML files.

    Returns:
        Path to created folder
    """
    import time

    folder = Path.home() / "northserve_yamls" / f"northserve_yamls_{os.getpid()}_{int(time.time())}"
    folder.mkdir(parents=True, exist_ok=True)

    return folder


def cleanup_temp_folder(folder: Path) -> None:
    """
    Clean up temporary folder.

    Args:
        folder: Path to folder to clean up
    """
    import shutil

    try:
        if folder.exists():
            shutil.rmtree(folder)
            logger.debug(f"Cleaned up temp folder: {folder}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp folder {folder}: {e}")


def copy_yaml_templates(dest_folder: Path) -> None:
    """
    Copy YAML templates to destination folder.

    Args:
        dest_folder: Destination folder path
    """
    import shutil
    from northserve.constants import YAML_TEMPLATES_DIR

    if not YAML_TEMPLATES_DIR.exists():
        raise FileNotFoundError(f"YAML templates directory not found: {YAML_TEMPLATES_DIR}")

    # Copy all files from templates directory
    for template_file in YAML_TEMPLATES_DIR.glob("*"):
        if template_file.is_file():
            shutil.copy(template_file, dest_folder)


def format_service_url(standalone: bool = False, svc_port: Optional[int] = None) -> str:
    """
    Format service URL based on deployment mode.

    Args:
        standalone: Whether this is a standalone service
        svc_port: Service port (for standalone mode)

    Returns:
        Formatted URL string
    """
    from northserve.constants import SERVICE_URL, STANDALONE_SERVICE_IPS

    if standalone and svc_port:
        ips = ",".join([f"{ip}:{svc_port}" for ip in STANDALONE_SERVICE_IPS])
        return f"http://{ips}/v1/"
    else:
        return SERVICE_URL


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON response with error handling.

    Args:
        response_text: JSON response text

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If response is not valid JSON
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")


