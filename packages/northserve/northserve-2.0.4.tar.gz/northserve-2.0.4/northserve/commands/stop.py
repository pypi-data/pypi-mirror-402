"""Stop command implementation."""

import click
from typing import Optional

from northserve.core.job_manager import JobManager
from northserve.constants import DEFAULT_NAMESPACE, DEFAULT_BACKEND, DEFAULT_PROFILE
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.option('--model-name', required=True, help='Model name to stop')
@click.option('--backend', default=DEFAULT_BACKEND, help=f'Backend type (default: {DEFAULT_BACKEND})')
@click.option('--profile', default=DEFAULT_PROFILE, help=f'Deployment profile (default: {DEFAULT_PROFILE})')
@click.option('--cluster-name', default='', help='Cluster name')
@click.option('--namespace', default=DEFAULT_NAMESPACE, help=f'Kubernetes namespace (default: {DEFAULT_NAMESPACE})')
@click.option('--standalone', is_flag=True, help='Stop standalone service')
@click.option('--app-name', help='Custom application name (auto-generated if not specified)')
@click.option('-y', '--yes', 'skip_confirmation', is_flag=True, help='Skip confirmation prompt')
def stop(
    model_name: str,
    backend: str,
    profile: str,
    cluster_name: str,
    namespace: str,
    standalone: bool,
    app_name: Optional[str],
    skip_confirmation: bool,
):
    """Stop a running LLM serving deployment."""
    try:
        # Build app name if not provided
        if not app_name:
            app_name = f"{model_name}-{backend}"
            if cluster_name:
                app_name = f"{app_name}-{cluster_name}"

        # Create job manager and stop deployment
        job_manager = JobManager()
        job_manager.stop_deployment(
            app_name,
            namespace,
            standalone,
            skip_confirmation
        )

    except Exception as e:
        logger.error(f"Failed to stop deployment: {e}")
        raise click.Abort()


