"""Direct Kubernetes operations using kubectl."""

import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

from northserve.utils.logger import get_logger
from northserve.utils.helpers import run_kubectl_command

logger = get_logger(__name__)


class KubernetesError(Exception):
    """Exception raised for Kubernetes operation errors."""
    pass


class KubernetesClient:
    """Client for direct kubectl operations."""

    def __init__(self, namespace: str = "qiji"):
        """
        Initialize Kubernetes client.

        Args:
            namespace: Default namespace for operations
        """
        self.namespace = namespace

    def delete_service(self, service_name: str, namespace: Optional[str] = None) -> None:
        """
        Delete a Kubernetes service.

        Args:
            service_name: Name of the service
            namespace: Namespace (defaults to client's namespace)

        Raises:
            KubernetesError: If deletion fails
        """
        ns = namespace or self.namespace

        result = run_kubectl_command(
            ["delete", "service", service_name],
            namespace=ns
        )

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to delete service {service_name}: {result.stderr}"
            )

        logger.info(f"Service {service_name} deleted successfully")

    def get_service(self, service_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get service details in YAML format.

        Args:
            service_name: Name of the service
            namespace: Namespace (defaults to client's namespace)

        Returns:
            Service details as dictionary

        Raises:
            KubernetesError: If operation fails
        """
        ns = namespace or self.namespace

        result = run_kubectl_command(
            ["get", "service", service_name, "-o", "yaml"],
            namespace=ns
        )

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to get service {service_name}: {result.stderr}"
            )

        # Parse YAML output
        import yaml
        return yaml.safe_load(result.stdout)

    def describe_volcano_job(
        self,
        job_name: str,
        namespace: Optional[str] = None
    ) -> str:
        """
        Describe a Volcano job.

        Args:
            job_name: Name of the job
            namespace: Namespace (defaults to client's namespace)

        Returns:
            Description output

        Raises:
            KubernetesError: If operation fails
        """
        ns = namespace or self.namespace

        result = run_kubectl_command(
            ["describe", "vj", job_name],
            namespace=ns
        )

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to describe job {job_name}: {result.stderr}"
            )

        return result.stdout

    def get_volcano_job_gpus(
        self,
        job_name: str,
        namespace: Optional[str] = None
    ) -> int:
        """
        Get number of GPUs allocated to a Volcano job.

        Args:
            job_name: Name of the job
            namespace: Namespace (defaults to client's namespace)

        Returns:
            Number of GPUs

        Raises:
            KubernetesError: If operation fails
        """
        description = self.describe_volcano_job(job_name, namespace)

        # Parse nvidia.com/gpu count from description
        for line in description.split('\n'):
            if 'nvidia.com/gpu:' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return int(parts[-1])
                    except ValueError:
                        pass

        raise KubernetesError(f"Could not find GPU count for job {job_name}")

    def exec_command(
        self,
        pod_name: str,
        command: list,
        namespace: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Execute a command in a pod.

        Args:
            pod_name: Name of the pod
            command: Command to execute
            namespace: Namespace (defaults to client's namespace)

        Returns:
            CompletedProcess instance

        Raises:
            KubernetesError: If execution fails
        """
        ns = namespace or self.namespace

        # Build exec command
        exec_args = ["exec", pod_name, "--"] + command

        result = run_kubectl_command(exec_args, namespace=ns)

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to execute command in pod {pod_name}: {result.stderr}"
            )

        return result

    def get_ingress(
        self,
        ingress_name: str,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ingress details.

        Args:
            ingress_name: Name of the ingress
            namespace: Namespace (defaults to client's namespace)

        Returns:
            Ingress details as dictionary

        Raises:
            KubernetesError: If operation fails
        """
        ns = namespace or self.namespace

        result = run_kubectl_command(
            ["get", "ingress", ingress_name, "-o", "yaml"],
            namespace=ns
        )

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to get ingress {ingress_name}: {result.stderr}"
            )

        # Parse YAML output
        import yaml
        return yaml.safe_load(result.stdout)

    def backup_resource(
        self,
        resource_type: str,
        resource_name: str,
        backup_file: Path,
        namespace: Optional[str] = None
    ) -> None:
        """
        Backup a Kubernetes resource to a file.

        Args:
            resource_type: Type of resource (e.g., 'service', 'ingress')
            resource_name: Name of the resource
            backup_file: Path to backup file
            namespace: Namespace (defaults to client's namespace)

        Raises:
            KubernetesError: If backup fails
        """
        ns = namespace or self.namespace

        result = run_kubectl_command(
            ["get", resource_type, resource_name, "-o", "yaml"],
            namespace=ns
        )

        if result.returncode != 0:
            raise KubernetesError(
                f"Failed to backup {resource_type} {resource_name}: {result.stderr}"
            )

        # Write to backup file
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text(result.stdout)

        logger.info(f"Backed up {resource_type} {resource_name} to {backup_file}")


