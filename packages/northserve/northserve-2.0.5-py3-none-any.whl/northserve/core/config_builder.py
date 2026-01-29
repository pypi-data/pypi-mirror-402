"""Configuration builder for deployment YAML generation."""

import os
from typing import Dict, Any, List
from pathlib import Path

from northserve.models.deployment import DeploymentConfig, VolumeConfig
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigBuilderError(Exception):
    """Exception raised for config building errors."""
    pass


class ConfigBuilder:
    """Builds rendering context from deployment configuration."""

    def __init__(self):
        """Initialize config builder."""
        pass

    def _build_volumes(self, volumes: List[VolumeConfig]) -> tuple:
        """
        Build volume and volume mount specifications.

        Args:
            volumes: List of volume configurations

        Returns:
            Tuple of (volumes_yaml, volume_mounts_yaml)
        """
        volumes_list = []
        volume_mounts_list = []

        for volume in volumes:
            if volume.name == "gpfs":
                # HostPath volume
                volumes_list.append(
                    f"      - name: {volume.name}\n"
                    f"        hostPath:\n"
                    f"          path: {volume.path}\n"
                    f"          type: Directory"
                )
                volume_mounts_list.append(
                    f"        - mountPath: {volume.path}\n"
                    f"          name: {volume.name}"
                )
            else:
                # PVC volume
                volumes_list.append(
                    f"      - name: {volume.name}\n"
                    f"        persistentVolumeClaim:\n"
                    f"          claimName: {volume.name}"
                )
                volume_mounts_list.append(
                    f"        - mountPath: {volume.path}\n"
                    f"          name: {volume.name}"
                )

        return "\n".join(volumes_list), "\n".join(volume_mounts_list)

    def _parse_extra_envs(self, extra_envs: str) -> Dict[str, str]:
        """
        Parse extra environment variables string.

        Args:
            extra_envs: Space-separated environment variables

        Returns:
            Dictionary of environment variables
        """
        if not extra_envs.strip():
            return {}

        env_dict = {}
        for item in extra_envs.split():
            if '=' in item:
                key, value = item.split('=', 1)
                env_dict[key] = value

        return env_dict

    def _build_multi_node_init_cmds(
        self,
        use_ray_cluster: bool,
        serve_base_path: str,
        gpus_per_pod: int
    ) -> tuple:
        """
        Build multi-node initialization commands.

        Args:
            use_ray_cluster: Whether to use Ray cluster
            serve_base_path: Base path for logs
            gpus_per_pod: Number of GPUs per pod

        Returns:
            Tuple of (head_init_cmds, worker_init_cmds)
        """
        if not use_ray_cluster:
            return "", ""

        # Verify 8 GPUs per pod for multi-node
        if gpus_per_pod != 8:
            raise ConfigBuilderError(
                "Multi-node with Ray cluster only supports 8 GPUs per pod"
            )

        # Head node initialization
        head_cmds = [
            f"mkdir -p {serve_base_path} && echo `hostname -i` > {serve_base_path}/replica_master_ip",
            "ray start --head --port=6379 --num-cpus 8 --num-gpus 8",
            "sleep 180"
        ]
        head_init_cmds = " && ".join(head_cmds) + " && "

        # Worker node initialization
        wait_for_master = (
            f"master_ip_file={serve_base_path}/replica_master_ip; "
            f"timeout=300; "
            f"start_time=$(date +%s); "
            f"while [ ! -f $master_ip_file ]; do "
            f"current_time=$(date +%s); "
            f"if [ $((current_time - start_time)) -gt $timeout ]; then "
            f"echo 'Timeout waiting for master_ip file after $timeout seconds'; "
            f"exit 1; "
            f"fi; "
            f"echo 'Waiting for master_ip file to be created...'; "
            f"sleep 5; "
            f"done"
        )

        worker_cmds = [
            wait_for_master,
            f"ray start --num-cpus 8 --num-gpus 8 --address `cat {serve_base_path}/replica_master_ip`:6379 --block"
        ]
        worker_init_cmds = " && ".join(worker_cmds)

        return head_init_cmds, worker_init_cmds

    def build_render_context(self, config: DeploymentConfig) -> Dict[str, Any]:
        """
        Build rendering context from deployment configuration.

        Args:
            config: Deployment configuration

        Returns:
            Dictionary with uppercased keys for template rendering
        """
        # Convert all config attributes to uppercase for template compatibility
        context = {
            'MODEL_NAME': config.model_name,
            'SERVED_MODEL_NAME': config.served_model_name,
            'MODEL_PATH': config.model_path or '',
            'APP_NAME': config.app_name,
            'REPLICAS': config.replicas,
            'GPUS_PER_POD': config.gpus_per_pod,
            'PODS_PER_JOB': config.pods_per_job,
            'USER_NAME': config.user_name,
            'NAMESPACE': config.namespace,
            'BACKEND': config.backend.value,
            'PROTOCOL': config.protocol.value,
            'PROFILE': config.profile.value,
            'EXTRA_CMDS': config.extra_cmds,
            'EXTRA_ENVS': config.extra_envs,
            'API_KEY': config.api_key,
            'CLUSTER_NAME': config.cluster_name,
            'GPU_TYPE': config.gpu_type.value,
            'QUEUE': config.queue,
            'PRIORITYCLASSNAME': config.priority_class_name.value,
            'RECLAIMABLEBYVOLCANO': 'true' if config.reclaimable_by_volcano else 'false',
            'TENSOR_PARALLEL_SIZE': config.tensor_parallel_size,
            'PIPELINE_PARALLEL_SIZE': config.pipeline_parallel_size,
            'TERMINATIONGRACEPERIODSECONDS': config.termination_grace_period_seconds,
            'USE_HOST_NETWORK': 'true' if config.use_host_network else 'false',
            'USE_PRIVILEGED_POD': 'true' if config.use_privileged_pod else 'false',
            'NEED_INFRAWAVE_RDMA': 'true' if config.need_infrawave_rdma else 'false',
            'IMAGE_VERSION': config.image_version,
            'DEPLOYMENT_UUID': config.deployment_uuid,
            'IS_ROUTER': 'true' if config.is_router else 'false',
        }

        # Parse extra environment variables
        extra_envs_dict = self._parse_extra_envs(config.extra_envs)
        context['EXTRA_ENVS'] = extra_envs_dict
        context['HAS_EXTRA_ENVS'] = len(extra_envs_dict) > 0

        # Cluster configuration
        context['USE_OTHER_CLUSTER'] = config.cluster_name != ""

        # Multi-pod configuration
        context['MULTI_PODS'] = config.is_multi_pod
        context['TOTAL_REPLICAS'] = config.total_replicas
        context['WORKER_REPLICAS'] = config.worker_replicas

        # PD separation configuration
        context['PD_SEPARATION'] = config.pd_separation
        context['PREFILL_NODES'] = config.prefill_nodes
        context['DECODE_NODES'] = config.decode_nodes
        context['MINILB_REPLICAS'] = config.minilb_replicas

        # Serve base path
        context['SERVE_BASE_PATH'] = config.serve_base_path

        # UID and GID
        context['UID'] = os.getuid()
        context['GID'] = 2888  # Default group id for qiji

        # Build volumes
        volumes_yaml, volume_mounts_yaml = self._build_volumes(config.volumes)
        context['VOLUMES'] = volumes_yaml
        context['VOLUMEMOUNTS'] = volume_mounts_yaml

        # Multi-node initialization commands
        head_init, worker_init = self._build_multi_node_init_cmds(
            config.use_ray_cluster,
            config.serve_base_path,
            config.gpus_per_pod
        )
        context['MULTI_NODE_HEAD_INIT_CMDS'] = head_init
        context['MULTI_NODE_WORKER_INIT_CMDS'] = worker_init

        # Ray cluster configuration
        context['USE_RAY_CLUSTER'] = config.use_ray_cluster

        return context

    def determine_template_file(self, config: DeploymentConfig) -> str:
        """
        Determine which template file to use.

        Args:
            config: Deployment configuration

        Returns:
            Template filename
        """
        if config.is_multi_pod:
            return 'deployment_multi_node.jinja'
        else:
            return 'deployment.yaml.jinja'

    def determine_pd_template_files(self) -> Dict[str, str]:
        """
        Determine template files for PD separation mode.

        Returns:
            Dictionary mapping component to template filename
        """
        return {
            'prefill': 'deployment_pd_prefill.jinja',
            'decode': 'deployment_pd_decode.jinja',
            'minilb': 'deployment_pd_minilb.jinja'
        }


