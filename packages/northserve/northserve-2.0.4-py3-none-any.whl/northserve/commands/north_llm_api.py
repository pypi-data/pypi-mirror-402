"""North LLM API deployment commands."""

import click
from pathlib import Path
from typing import Optional

from northserve.models.deployment import NorthLLMAPIConfig
from northserve.clients.infrawave import InfrawaveClient
from northserve.clients.kubernetes import KubernetesClient
from northserve.core.template_renderer import TemplateRenderer
from northserve.core.config_builder import ConfigBuilder
from northserve.constants import (
    YAML_TEMPLATES_DIR,
    CONFIGS_DIR,
    USER_NAME,
)
from northserve.utils.logger import get_logger
from northserve.utils.helpers import (
    create_temp_yaml_folder,
    cleanup_temp_folder,
    copy_yaml_templates,
    confirm_action,
)

logger = get_logger(__name__)


@click.command()
@click.option('--version', default='v0.2.3', help='Version to deploy (default: v0.2.3)')
@click.option('--replicas', default=1, type=int, help='Number of replicas (default: 1)')
@click.option('--namespace', default='qiji', help='Kubernetes namespace (default: qiji)')
@click.option('--queue', default='qiji', help='Volcano queue (default: qiji)')
@click.option('--extra-envs', default='', help='Extra environment variables')
@click.option('-y', '--yes', 'skip_confirmation', is_flag=True, help='Skip confirmation prompt')
def launch_north_llm_api(
    version: str,
    replicas: int,
    namespace: str,
    queue: str,
    extra_envs: str,
    skip_confirmation: bool,
):
    """Launch North LLM API service."""
    try:
        # Warning for non-qiji namespace
        if namespace != "qiji" and not skip_confirmation:
            logger.warning(
                f"Namespace is not qiji. Please verify your Infrawave account "
                f"belongs to namespace: {namespace}"
            )
            if not confirm_action("Are you sure to continue?", False):
                logger.info("Operation cancelled")
                return

        # Create config
        config = NorthLLMAPIConfig(
            version=version,
            replicas=replicas,
            namespace=namespace,
            queue=queue,
            user_name=USER_NAME,
            extra_envs=extra_envs,
        )

        app_name = config.app_name

        # Display info
        logger.info(f"Going to create deployment \"{app_name}\" in namespace \"{namespace}\"")

        if not confirm_action("Continue?", skip_confirmation):
            logger.info("Operation cancelled")
            return

        # Create temporary YAML folder
        yaml_folder = create_temp_yaml_folder()

        try:
            # Copy templates
            copy_yaml_templates(yaml_folder)

            # Build rendering context
            context = {
                'APP_NAME': app_name,
                'REPLICAS': config.replicas,
                'USER_NAME': config.user_name,
                'GPUS_PER_POD': 0,
                'PODS_PER_JOB': 1,
                'CLUSTER_NAME': config.cluster_name,
                'SERVED_MODEL_NAME': app_name,
                'PRIORITYCLASSNAME': 'higher-priority-job',
                'RECLAIMABLEBYVOLCANO': 'false',
                'QUEUE': config.queue,
                'NAMESPACE': config.namespace,
                'EXTRA_ENVS': config.extra_envs,
                'IMAGE_VERSION': config.version,
            }

            # Load and add engine config
            renderer = TemplateRenderer()
            engine_config_path = CONFIGS_DIR / 'north-llm-api_service.yaml'
            context = renderer.add_engine_config_to_context(
                engine_config_path,
                context
            )

            # Render deployment
            template_path = yaml_folder / 'deployment.yaml.jinja'
            rendered_yaml = renderer.render_template(template_path, context)

            deployment_file = yaml_folder / 'deployment_northllm_api.yaml'
            renderer.save_rendered_template(rendered_yaml, deployment_file)

            logger.info(f"Deployment file created at {deployment_file}")

            # Update service.yaml
            service_file = yaml_folder / 'service.yaml'
            content = service_file.read_text()
            content = content.replace('APP_NAME', app_name)
            content = content.replace('NAMESPACE', namespace)
            content = content.replace('SERVED_MODEL_NAME', app_name)
            content = content.replace('PORT', '8000')
            service_file.write_text(content)

            logger.info(f"Service file created at {service_file}")

            # Create deployment
            infrawave_client = InfrawaveClient()

            logger.info("Creating deployment...")
            infrawave_client.create_job_by_yaml(deployment_file)

            logger.info("Creating service...")
            infrawave_client.create_service_by_yaml(service_file)

            logger.info(f"Successfully created deployment \"{app_name}\" in namespace \"{namespace}\"")
            logger.info("All done.")

        finally:
            # Cleanup
            cleanup_temp_folder(yaml_folder)

    except Exception as e:
        logger.error(f"Failed to launch North LLM API: {e}")
        raise click.Abort()


@click.command()
@click.option('--version', default='v0.2.3', help='Version to stop (default: v0.2.3)')
@click.option('--namespace', default='qiji', help='Kubernetes namespace (default: qiji)')
@click.option('-y', '--yes', 'skip_confirmation', is_flag=True, help='Skip confirmation prompt')
def stop_north_llm_api(
    version: str,
    namespace: str,
    skip_confirmation: bool,
):
    """Stop North LLM API service."""
    try:
        # Warning for non-qiji namespace
        if namespace != "qiji" and not skip_confirmation:
            logger.warning(
                f"Namespace is not qiji. Please verify your Infrawave account "
                f"belongs to namespace: {namespace}"
            )
            if not confirm_action("Are you sure to continue?", False):
                logger.info("Operation cancelled")
                return

        # Create config
        config = NorthLLMAPIConfig(
            version=version,
            namespace=namespace,
        )

        app_name = config.app_name

        # Display info
        logger.info(f"Going to delete deployment \"{app_name}\" in namespace \"{namespace}\"")

        if not confirm_action("Continue?", skip_confirmation):
            logger.info("Operation cancelled")
            return

        # Create backup directory
        import time
        backup_dir = Path(f"/tmp/north_llm_api_backup_{int(time.time())}")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup resources
        k8s_client = KubernetesClient(namespace)

        logger.info(f"Backing up service to {backup_dir}/svc.yaml.back")
        try:
            k8s_client.backup_resource(
                'service',
                f'{app_name}-svc',
                backup_dir / 'svc.yaml.back',
                namespace
            )
        except Exception as e:
            logger.warning(f"Failed to backup service: {e}")

        # Get deployment UUID
        infrawave_client = InfrawaveClient()
        try:
            deployment_uuid = infrawave_client.get_job_uuid(app_name, namespace)
            logger.info(f"Deployment UUID: {deployment_uuid}")

            logger.info(f"Backing up deployment to {backup_dir}/deployment.yaml.back")
            try:
                k8s_client.backup_resource(
                    'deployment',
                    deployment_uuid,
                    backup_dir / 'deployment.yaml.back',
                    namespace
                )
            except Exception as e:
                logger.warning(f"Failed to backup deployment: {e}")
        except Exception as e:
            logger.warning(f"Failed to get deployment UUID: {e}")

        # Delete deployment
        logger.info("Deleting deployment...")
        infrawave_client.delete_job_by_name(app_name, namespace)

        # Delete service
        logger.info("Deleting service...")
        k8s_client.delete_service(f'{app_name}-svc', namespace)

        logger.info("Successfully stopped North LLM API")

    except Exception as e:
        logger.error(f"Failed to stop North LLM API: {e}")
        raise click.Abort()


