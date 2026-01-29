"""Job manager for orchestrating deployments."""

from pathlib import Path
from typing import Optional, List
import uuid

from northserve.models.deployment import DeploymentConfig
from northserve.models.enums import BackendType
from northserve.core.config_builder import ConfigBuilder
from northserve.core.template_renderer import TemplateRenderer
from northserve.clients.infrawave import InfrawaveClient
from northserve.clients.kubernetes import KubernetesClient
from northserve.constants import YAML_TEMPLATES_DIR, CONFIGS_DIR
from northserve.utils.logger import get_logger
from northserve.utils.helpers import (
    create_temp_yaml_folder,
    cleanup_temp_folder,
    copy_yaml_templates,
    format_service_url,
    confirm_action
)

logger = get_logger(__name__)


class JobManagerError(Exception):
    """Exception raised for job manager errors."""
    pass


class JobManager:
    """Manages deployment lifecycle for LLM serving jobs."""

    def __init__(
        self,
        infrawave_client: Optional[InfrawaveClient] = None,
        k8s_client: Optional[KubernetesClient] = None
    ):
        """
        Initialize job manager.

        Args:
            infrawave_client: Infrawave API client (creates default if None)
            k8s_client: Kubernetes client (creates default if None)
        """
        self.infrawave_client = infrawave_client or InfrawaveClient()
        self.k8s_client = k8s_client or KubernetesClient()
        self.config_builder = ConfigBuilder()
        self.template_renderer = TemplateRenderer()

    def _create_single_job(
        self,
        config: DeploymentConfig,
        template_file: str,
        engine_config_path: Path,
        output_file: Path,
        context_prefix: str = ''
    ) -> None:
        """
        Create a single deployment job.

        Args:
            config: Deployment configuration
            template_file: Template filename
            engine_config_path: Path to engine config
            output_file: Output YAML file path
            context_prefix: Prefix for context keys (for PD separation)
        """
        # Build rendering context
        context = self.config_builder.build_render_context(config)

        # Add engine configuration to context
        context = self.template_renderer.add_engine_config_to_context(
            engine_config_path,
            context,
            prefix=context_prefix
        )

        # Render template
        template_path = YAML_TEMPLATES_DIR / template_file
        rendered_yaml = self.template_renderer.render_template(template_path, context)

        # Save rendered template
        self.template_renderer.save_rendered_template(rendered_yaml, output_file)

        # Create job via Infrawave API
        logger.info(f"Creating job from {output_file}")
        self.infrawave_client.create_job_by_yaml(output_file)

    def _create_pd_separation_jobs(
        self,
        config: DeploymentConfig,
        yaml_folder: Path
    ) -> None:
        """
        Create jobs for PD separation mode (3 separate jobs).

        Args:
            config: Deployment configuration
            yaml_folder: Temporary YAML folder
        """
        logger.info("Creating PD separation deployment (3 separate jobs)...")

        # Generate deployment UUID
        deployment_uuid = uuid.uuid4().hex
        config.deployment_uuid = deployment_uuid
        logger.info(f"Generated deployment UUID: {deployment_uuid}")

        # Create prefill job
        logger.info("Creating prefill job...")
        prefill_config = DeploymentConfig(
            **{**config.__dict__, 'pods_per_job': config.prefill_nodes, 'replicas': 1}
        )
        prefill_engine_config = CONFIGS_DIR / f"{config.backend.value}_{config.protocol.value}_pdpre.yaml"
        self._create_single_job(
            prefill_config,
            'deployment_pd_prefill.jinja',
            prefill_engine_config,
            yaml_folder / 'deployment_prefill.yaml',
            context_prefix='PREFILL_'
        )

        # Create decode job
        logger.info("Creating decode job...")
        decode_config = DeploymentConfig(
            **{**config.__dict__, 'pods_per_job': config.decode_nodes, 'replicas': 1}
        )
        decode_engine_config = CONFIGS_DIR / f"{config.backend.value}_{config.protocol.value}_pddec.yaml"
        self._create_single_job(
            decode_config,
            'deployment_pd_decode.jinja',
            decode_engine_config,
            yaml_folder / 'deployment_decode.yaml',
            context_prefix='DECODE_'
        )

        # Create minilb job
        logger.info("Creating minilb job...")
        minilb_config = DeploymentConfig(
            **{
                **config.__dict__,
                'pods_per_job': 1,
                'replicas': config.minilb_replicas,
                'gpus_per_pod': 0
            }
        )
        minilb_engine_config = CONFIGS_DIR / f"{config.backend.value}_{config.protocol.value}_minilb.yaml"
        self._create_single_job(
            minilb_config,
            'deployment_pd_minilb.jinja',
            minilb_engine_config,
            yaml_folder / 'deployment_minilb.yaml',
            context_prefix='MINILB_'
        )

        logger.info("All 3 jobs created successfully!")
        logger.info(f"Prefill job: {config.app_name}-prefill")
        logger.info(f"Decode job: {config.app_name}-decode")
        logger.info(f"Minilb job: {config.app_name}-minilb")

    def _create_router_job(
        self,
        config: DeploymentConfig,
        yaml_folder: Path
    ) -> None:
        """
        Create SGLang router job.

        Args:
            config: Deployment configuration
            yaml_folder: Temporary YAML folder
        """
        logger.info("Creating SGLang router job...")

        # Create router config
        router_config = DeploymentConfig(
            model_name=config.model_name,
            served_model_name=config.served_model_name,
            app_name=f"{config.app_name}-router",
            replicas=1,
            gpus_per_pod=0,
            pods_per_job=1,
            user_name=config.user_name,
            namespace=config.namespace,
            volumes=config.volumes,
            backend=config.backend,
            protocol=config.protocol,
            profile=config.profile,
            model_path=config.model_path,
            cluster_name=config.cluster_name,
            priority_class_name=config.priority_class_name,
            queue=config.queue,
            reclaimable_by_volcano=config.reclaimable_by_volcano,
            api_key=config.api_key,
            termination_grace_period_seconds=config.termination_grace_period_seconds,
            is_router=True
        )

        router_engine_config = CONFIGS_DIR / "sglang_router.yaml"
        self._create_single_job(
            router_config,
            'deployment.yaml.jinja',
            router_engine_config,
            yaml_folder / 'router_deployment.yaml'
        )

    def launch_deployment(
        self,
        config: DeploymentConfig,
        skip_confirmation: bool = False
    ) -> None:
        """
        Launch a new deployment.

        Args:
            config: Deployment configuration
            skip_confirmation: Skip user confirmation

        Raises:
            JobManagerError: If deployment fails
        """
        # Display configuration
        self._display_launch_config(config)

        # Confirm action
        if not confirm_action("Continue", skip_confirmation):
            logger.info("Canceled.")
            return

        # Create temporary YAML folder
        yaml_folder = create_temp_yaml_folder()

        try:
            # Copy template files
            copy_yaml_templates(yaml_folder)

            # Handle PD separation mode
            if config.pd_separation:
                self._create_pd_separation_jobs(config, yaml_folder)
            else:
                # Create router job if requested
                if config.use_sglang_router:
                    self._create_router_job(config, yaml_folder)

                # Determine template file
                template_file = self.config_builder.determine_template_file(config)

                # Get engine config path
                engine_config_path = self.template_renderer.get_engine_config_path(
                    config.backend.value,
                    config.protocol.value,
                    config.profile.value
                )

                # Create main deployment
                output_file = yaml_folder / 'deployment.yaml'
                self._create_single_job(
                    config,
                    template_file,
                    engine_config_path,
                    output_file
                )

            # Handle standalone mode service
            if config.standalone_mode:
                self._create_standalone_service(config, yaml_folder)

            # Display success message
            self._display_launch_success(config)

        finally:
            # Cleanup temporary folder
            cleanup_temp_folder(yaml_folder)

    def _display_launch_config(self, config: DeploymentConfig) -> None:
        """Display launch configuration."""
        logger.info("Going to create service with the following config:")
        logger.info(f"Model Name: {config.model_name}")
        logger.info(f"Served Model Name: {config.served_model_name}")
        logger.info(f"Model Path: {config.model_path}")
        logger.info(f"Protocol: {config.protocol.value}")
        logger.info(f"Replicas: {config.replicas}")
        logger.info(f"GPUs per Pod: {config.gpus_per_pod}")
        logger.info(f"Pods per Job: {config.pods_per_job}")
        logger.info(f"Backend: {config.backend.value}")
        logger.info(f"Profile: {config.profile.value}")
        logger.info(f"Extra cmds: {config.extra_cmds}")
        logger.info(f"Extra envs: {config.extra_envs}")
        logger.info(f"API Key: {config.api_key}")
        if config.cluster_name:
            logger.info(f"Cluster Name: {config.cluster_name}")
        logger.info(f"Use Host Network: {config.use_host_network}")
        logger.info(f"Need Infrawave RDMA: {config.need_infrawave_rdma}")
        logger.info(f"GPU Type: {config.gpu_type.value}")
        logger.info("=" * 25)
        logger.info("With this config, will create the following resource:")
        logger.info(f"- A VolcanoJob called {config.app_name}")
        if config.standalone_mode:
            logger.info(f"- A service called {config.app_name}-svc")

    def _display_launch_success(self, config: DeploymentConfig) -> None:
        """Display launch success message."""
        logger.info("Done.")
        service_url = format_service_url(config.standalone_mode)
        logger.info(f"Service started, request with url: {service_url}")

    def _create_standalone_service(
        self,
        config: DeploymentConfig,
        yaml_folder: Path
    ) -> None:
        """
        Create standalone service.

        Args:
            config: Deployment configuration
            yaml_folder: YAML folder containing service template
        """
        logger.info("Creating standalone service...")

        # Update service.yaml with sed-like replacements
        service_file = yaml_folder / 'service.yaml'
        content = service_file.read_text()

        content = content.replace('APP_NAME', config.app_name)
        content = content.replace('NAMESPACE', config.namespace)
        content = content.replace('SERVED_MODEL_NAME', config.served_model_name)
        content = content.replace('PORT', '8000')

        service_file.write_text(content)

        # Create service via Infrawave API
        response = self.infrawave_client.create_service_by_yaml(service_file)

        # Extract service port
        if 'data' in response and 'spec' in response['data']:
            ports = response['data']['spec'].get('ports', [])
            if ports:
                svc_port = ports[0].get('nodePort')
                logger.info(f"Service created with port: {svc_port}")

    def stop_deployment(
        self,
        app_name: str,
        namespace: str = "qiji",
        standalone_mode: bool = False,
        skip_confirmation: bool = False
    ) -> None:
        """
        Stop a deployment.

        Args:
            app_name: Application name
            namespace: Kubernetes namespace
            standalone_mode: Whether this is a standalone deployment
            skip_confirmation: Skip user confirmation

        Raises:
            JobManagerError: If stop operation fails
        """
        # Display stop configuration
        logger.info("Going to stop service with the following config:")
        logger.info(f"App Name: {app_name}")
        logger.info(f"Namespace: {namespace}")
        if standalone_mode:
            logger.info("Standalone Mode: on")
        logger.info("=" * 25)
        logger.info("With this config, will delete the following resources:")
        logger.info(f"- A VolcanoJob called {app_name}")
        if standalone_mode:
            logger.info(f"- A service called {app_name}-svc")

        # Confirm action
        if not confirm_action("Continue", skip_confirmation):
            logger.info("Canceled.")
            return

        try:
            # Delete job
            logger.info("Deleting job...")
            self.infrawave_client.delete_job_by_name(app_name, namespace)

            # Delete service if standalone
            if standalone_mode:
                logger.info("Deleting service...")
                svc_name = f"{app_name}-svc"
                self.k8s_client.delete_service(svc_name, namespace)

            logger.info("Done.")

        except Exception as e:
            raise JobManagerError(f"Failed to stop deployment: {e}")

    def list_models(self) -> List[str]:
        """
        List all deployed models.

        Returns:
            List of model names

        Raises:
            JobManagerError: If listing fails
        """
        try:
            import requests
            from northserve.constants import SERVICE_URL

            response = requests.get(
                f"{SERVICE_URL.rstrip('/')}/models",
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if 'data' in data:
                return [item['id'] for item in data['data']]

            return []

        except Exception as e:
            raise JobManagerError(f"Failed to list models: {e}")


