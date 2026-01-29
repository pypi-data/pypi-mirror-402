"""Launch command implementation."""

import click
from typing import Optional

from northserve.models.deployment import DeploymentConfig, VolumeConfig
from northserve.models.enums import BackendType, ProtocolType, GPUType, PriorityClass, ProfileType
from northserve.core.job_manager import JobManager
from northserve.constants import (
    DEFAULT_NAMESPACE,
    DEFAULT_PROTOCOL,
    DEFAULT_BACKEND,
    DEFAULT_PROFILE,
    DEFAULT_REPLICAS,
    DEFAULT_GPUS_PER_POD,
    DEFAULT_PODS_PER_JOB,
    DEFAULT_VOLUMES,
    DEFAULT_QUEUE,
    DEFAULT_PRIORITY_CLASS,
    DEFAULT_PIPELINE_PARALLEL_SIZE,
    DEFAULT_TERMINATION_GRACE_PERIOD,
    DEFAULT_MINILB_REPLICAS,
    USER_NAME,
)
from northserve.utils.logger import get_logger
from northserve.utils.validator import (
    ValidationError,
    validate_gpu_type,
    validate_priority_class,
    validate_backend,
    validate_volumes,
    validate_pd_separation_mode,
    validate_mutual_exclusivity,
)

logger = get_logger(__name__)


@click.command()
@click.option('--model-name', required=True, help='Model name for identification')
@click.option('--served-model-name', help='Name used in API requests (defaults to model-name)')
@click.option('--model-path', help='Path to model weights')
@click.option('--protocol', default=DEFAULT_PROTOCOL, help=f'API protocol (default: {DEFAULT_PROTOCOL})')
@click.option('--replicas', default=DEFAULT_REPLICAS, type=int, help=f'Number of replicas (default: {DEFAULT_REPLICAS})')
@click.option('--gpus-per-pod', default=DEFAULT_GPUS_PER_POD, type=int, help=f'GPUs per pod (default: {DEFAULT_GPUS_PER_POD})')
@click.option('--pods-per-job', default=DEFAULT_PODS_PER_JOB, type=int, help=f'Pods per job (default: {DEFAULT_PODS_PER_JOB})')
@click.option('--backend', default=DEFAULT_BACKEND, help=f'Inference backend (default: {DEFAULT_BACKEND})')
@click.option('--profile', default=DEFAULT_PROFILE, help=f'Deployment profile (default: {DEFAULT_PROFILE})')
@click.option('--extra-cmds', default='', help='Extra command line arguments for engine')
@click.option('--extra-envs', default='', help='Extra environment variables (KEY=value KEY2=value2)')
@click.option('--cluster-name', default='', help='Cluster name for multi-cluster deployment')
@click.option('--gpu-type', default='gpu', help='GPU type (gpu, h20, 4090d)')
@click.option('--namespace', default=DEFAULT_NAMESPACE, help=f'Kubernetes namespace (default: {DEFAULT_NAMESPACE})')
@click.option('--volumes', default=DEFAULT_VOLUMES, help=f'Volume mounts (default: {DEFAULT_VOLUMES})')
@click.option('--queue', default=DEFAULT_QUEUE, help=f'Volcano queue (default: {DEFAULT_QUEUE})')
@click.option('--app-name', help='Custom application name (auto-generated if not specified)')
@click.option('--priority-class-name', default=DEFAULT_PRIORITY_CLASS, help=f'Priority class (default: {DEFAULT_PRIORITY_CLASS})')
@click.option('--standalone', is_flag=True, help='Create standalone service with NodePort')
@click.option('--tensor-parallel-size', help='Tensor parallel size (defaults to gpus-per-pod)')
@click.option('--pipeline-parallel-size', default=DEFAULT_PIPELINE_PARALLEL_SIZE, help=f'Pipeline parallel size (default: {DEFAULT_PIPELINE_PARALLEL_SIZE})')
@click.option('--api-key', default='', help='API key for authentication')
@click.option('--termination-grace-period-seconds', default=DEFAULT_TERMINATION_GRACE_PERIOD, type=int, help=f'Termination grace period (default: {DEFAULT_TERMINATION_GRACE_PERIOD})')
@click.option('-y', '--yes', 'skip_confirmation', is_flag=True, help='Skip confirmation prompt')
@click.option('--use-host-network', is_flag=True, help='Use host network')
@click.option('--use-privileged-pod', is_flag=True, help='Use privileged pod')
@click.option('--need-infrawave-rdma', is_flag=True, help='Need Infrawave RDMA')
@click.option('--prefill-nodes', default=0, type=int, help='Number of prefill nodes (PD separation mode)')
@click.option('--decode-nodes', default=0, type=int, help='Number of decode nodes (PD separation mode)')
@click.option('--minilb-replicas', default=DEFAULT_MINILB_REPLICAS, type=int, help=f'MiniLB replicas (default: {DEFAULT_MINILB_REPLICAS})')
@click.option('--use-sglang-router', is_flag=True, help='Use SGLang router')
@click.option('--image-version', help='Override image version')
def launch(
    model_name: str,
    served_model_name: Optional[str],
    model_path: Optional[str],
    protocol: str,
    replicas: int,
    gpus_per_pod: int,
    pods_per_job: int,
    backend: str,
    profile: str,
    extra_cmds: str,
    extra_envs: str,
    cluster_name: str,
    gpu_type: str,
    namespace: str,
    volumes: str,
    queue: str,
    app_name: Optional[str],
    priority_class_name: str,
    standalone: bool,
    tensor_parallel_size: Optional[str],
    pipeline_parallel_size: str,
    api_key: str,
    termination_grace_period_seconds: int,
    skip_confirmation: bool,
    use_host_network: bool,
    use_privileged_pod: bool,
    need_infrawave_rdma: bool,
    prefill_nodes: int,
    decode_nodes: int,
    minilb_replicas: int,
    use_sglang_router: bool,
    image_version: Optional[str],
):
    """Launch a new LLM serving deployment."""
    try:
        # Validate inputs
        validate_backend(backend)
        validate_gpu_type(gpu_type)
        validate_priority_class(priority_class_name)
        validate_mutual_exclusivity(
            use_host_network, '--use-host-network',
            need_infrawave_rdma, '--need-infrawave-rdma'
        )
        validate_pd_separation_mode(backend, prefill_nodes, decode_nodes)

        # Parse volumes
        volume_list = validate_volumes(volumes)
        volume_configs = [VolumeConfig.from_string(v) for v in volume_list]

        # Set defaults
        if not served_model_name:
            served_model_name = model_name
            logger.info(f"Served Model Name not set, using Model Name: {served_model_name}")

        # Build app name
        if not app_name:
            app_name = f"{model_name}-{backend}"
            if cluster_name:
                app_name = f"{app_name}-{cluster_name}"

        # Determine if Ray cluster is needed
        use_ray_cluster = (backend == "vllm" and pods_per_job > 1)

        # Create deployment config
        config = DeploymentConfig(
            model_name=model_name,
            served_model_name=served_model_name,
            model_path=model_path,
            app_name=app_name,
            replicas=replicas,
            gpus_per_pod=gpus_per_pod,
            pods_per_job=pods_per_job,
            user_name=USER_NAME,
            namespace=namespace,
            volumes=volume_configs,
            backend=BackendType(backend),
            protocol=ProtocolType(protocol),
            profile=ProfileType(profile),
            gpu_type=GPUType(gpu_type),
            tensor_parallel_size=tensor_parallel_size,
            pipeline_parallel_size=pipeline_parallel_size,
            queue=queue,
            priority_class_name=PriorityClass(priority_class_name),
            cluster_name=cluster_name,
            extra_cmds=extra_cmds,
            extra_envs=extra_envs,
            api_key=api_key,
            termination_grace_period_seconds=termination_grace_period_seconds,
            use_host_network=use_host_network,
            use_privileged_pod=use_privileged_pod,
            need_infrawave_rdma=need_infrawave_rdma,
            use_ray_cluster=use_ray_cluster,
            prefill_nodes=prefill_nodes,
            decode_nodes=decode_nodes,
            minilb_replicas=minilb_replicas,
            standalone_mode=standalone,
            use_sglang_router=use_sglang_router,
            image_version=image_version,
        )

        # Create job manager and launch
        job_manager = JobManager()
        job_manager.launch_deployment(config, skip_confirmation)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Failed to launch deployment: {e}")
        raise click.Abort()


