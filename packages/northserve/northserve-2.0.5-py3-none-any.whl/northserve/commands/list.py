"""List command implementation."""

import click

from northserve.core.job_manager import JobManager
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


@click.command(name='list')
def list_models():
    """List all deployed models and their status."""
    try:
        logger.info("All model status:")

        # Create job manager and list models
        job_manager = JobManager()
        models = job_manager.list_models()

        if models:
            for model in models:
                click.echo(model)
        else:
            logger.info("No models found")

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise click.Abort()


