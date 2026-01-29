"""Infrawave API client for job and service management."""

import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path

from northserve.constants import INFRAWAVE_SERVER_HOST
from northserve.utils.logger import get_logger
from northserve.utils.helpers import load_config_file, parse_json_response

logger = get_logger(__name__)


class InfrawaveAPIError(Exception):
    """Exception raised for Infrawave API errors."""
    pass


class InfrawaveClient:
    """Client for interacting with Infrawave API."""

    def __init__(self, server_host: Optional[str] = None):
        """
        Initialize Infrawave client.

        Args:
            server_host: Server host (defaults to environment or constant)
        """
        self.server_host = server_host or INFRAWAVE_SERVER_HOST
        self.base_url = f"http://{self.server_host}"
        self._token: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

    def _load_credentials(self) -> None:
        """Load credentials from config file."""
        if not self._username or not self._password:
            config = load_config_file()
            self._username = config["username"]
            self._password = config["password"]

    def _get_auth_token(self, expire_time: int = 3600) -> str:
        """
        Get authentication token.

        Args:
            expire_time: Token expiration time in seconds

        Returns:
            Authentication token

        Raises:
            InfrawaveAPIError: If authentication fails
        """
        self._load_credentials()

        url = f"{self.base_url}/api/auth/get_token"
        payload = {
            "username": self._username,
            "password": self._password,
            "expireTime": expire_time
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if "data" not in data:
                raise InfrawaveAPIError(f"Invalid response: {data}")

            return data["data"]

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Failed to get auth token: {e}")

    @property
    def token(self) -> str:
        """Get or refresh authentication token."""
        if not self._token:
            self._token = self._get_auth_token()
        return self._token

    def create_job_by_yaml(self, yaml_path: Path) -> Dict[str, Any]:
        """
        Create a job using YAML configuration.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            API response data

        Raises:
            InfrawaveAPIError: If job creation fails
        """
        if not yaml_path.exists():
            raise InfrawaveAPIError(f"YAML file not found: {yaml_path}")

        # Read YAML content
        yaml_content = yaml_path.read_text()

        # Prepare request
        url = f"{self.base_url}/api/task/create_job_by_yaml"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        # Escape YAML content for JSON
        payload = {"code": yaml_content}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            data = response.json()

            if data.get("code") == 200:
                logger.info("Job registered successfully")
                logger.debug(json.dumps(data, indent=2))
                return data
            else:
                logger.error("Failed to register job")
                logger.error(json.dumps(data, indent=2))
                raise InfrawaveAPIError(f"Failed to create job: {data}")

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Request failed: {e}")

    def create_service_by_yaml(self, yaml_path: Path) -> Dict[str, Any]:
        """
        Create a service using YAML configuration.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            API response data

        Raises:
            InfrawaveAPIError: If service creation fails
        """
        if not yaml_path.exists():
            raise InfrawaveAPIError(f"YAML file not found: {yaml_path}")

        url = f"{self.base_url}/api/service/create_service"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        payload = {"yamlPath": str(yaml_path)}

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            data = response.json()

            if data.get("code") == 200:
                logger.debug(json.dumps(data, indent=2))
                return data
            else:
                logger.error(json.dumps(data, indent=2))
                raise InfrawaveAPIError(f"Failed to create service: {data}")

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Request failed: {e}")

    def get_job_uuid(
        self,
        job_name: str,
        namespace: str = "qiji"
    ) -> str:
        """
        Get job UUID by job name.

        Args:
            job_name: Name of the job
            namespace: Kubernetes namespace

        Returns:
            Job UUID

        Raises:
            InfrawaveAPIError: If failed to get UUID
        """
        url = f"{self.base_url}/api/get_jobs"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self.token}"
        }

        params = {"keyWord": job_name}

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # Parse the response format: {"data": [...], "total": 1}
            if not data.get("data") or len(data["data"]) == 0:
                raise InfrawaveAPIError(f"No job found with name: {job_name}")

            # The 'name' field in the first job is the UUID
            job_uuid = data["data"][0]["name"]

            if not job_uuid:
                raise InfrawaveAPIError(f"Failed to get UUID for job: {job_name}")

            return job_uuid

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Request failed: {e}")
        except (KeyError, IndexError) as e:
            raise InfrawaveAPIError(f"Failed to parse response: {e}")

    def delete_job_by_name(
        self,
        job_name: str,
        namespace: str = "qiji"
    ) -> Dict[str, Any]:
        """
        Delete a job by name.

        Args:
            job_name: Name of the job to delete
            namespace: Kubernetes namespace

        Returns:
            API response data

        Raises:
            InfrawaveAPIError: If deletion fails
        """
        # First get the job UUID
        try:
            job_uuid = self.get_job_uuid(job_name, namespace)
            print(job_uuid)
        except InfrawaveAPIError as e:
            print(f"Failed to get job UUID: {e}")
            raise InfrawaveAPIError(f"Failed to get job UUID: {e}")

        # Delete the job
        url = f"{self.base_url}/api/delete_jobs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        payload = {
            "name": job_uuid,
            "namespace": namespace
        }

        try:
            response = requests.delete(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            response_text = response.text

            # Check for success indicator
            if '"success": true' in response_text or '"success":true' in response_text:
                logger.info(f"Successfully deleted job {job_name} (UUID: {job_uuid})")
                return {"success": True, "job_name": job_name, "job_uuid": job_uuid}
            else:
                logger.error(f"Failed to delete job {job_name} (UUID: {job_uuid})")
                logger.error(f"Response: {response_text}")
                raise InfrawaveAPIError(
                    f"Failed to delete job {job_name} in namespace {namespace}. "
                    f"Response: {response_text}"
                )

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Request failed: {e}")

    def list_jobs(self, namespace: str = "qiji") -> Dict[str, Any]:
        """
        List jobs in a namespace.

        Args:
            namespace: Kubernetes namespace

        Returns:
            API response data with job list

        Raises:
            InfrawaveAPIError: If request fails
        """
        url = f"{self.base_url}/api/jobs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        params = {"namespace": namespace}

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            raise InfrawaveAPIError(f"Request failed: {e}")


