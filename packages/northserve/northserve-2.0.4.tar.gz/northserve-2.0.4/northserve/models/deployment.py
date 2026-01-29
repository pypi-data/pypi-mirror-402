"""Data models for deployment configuration."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

from northserve.models.enums import (
    BackendType,
    ProtocolType,
    GPUType,
    PriorityClass,
    ProfileType,
    DeploymentMode,
)


@dataclass
class VolumeConfig:
    """Volume configuration."""

    name: str
    path: str

    @classmethod
    def from_string(cls, volume_str: str) -> "VolumeConfig":
        """Parse volume from string format 'name:path'."""
        parts = volume_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid volume format: {volume_str}. Expected 'name:path'")
        return cls(name=parts[0], path=parts[1])


@dataclass
class EngineConfig:
    """Engine-specific configuration from YAML files."""

    image: str
    cmd: List[str]
    liveness_path: Optional[str] = None
    readiness_path: Optional[str] = None


@dataclass
class DeploymentConfig:
    """Complete deployment configuration."""

    # Required fields
    model_name: str
    served_model_name: str
    app_name: str
    replicas: int
    gpus_per_pod: int
    pods_per_job: int
    user_name: str
    namespace: str
    volumes: List[VolumeConfig]

    # Backend and protocol
    backend: BackendType
    protocol: ProtocolType
    profile: ProfileType

    # Optional model configuration
    model_path: Optional[str] = None

    # Resource configuration
    gpu_type: GPUType = GPUType.GPU
    tensor_parallel_size: Optional[str] = None
    pipeline_parallel_size: str = "1"

    # Scheduling configuration
    queue: str = "qiji"
    priority_class_name: PriorityClass = PriorityClass.LOW
    reclaimable_by_volcano: bool = False
    termination_grace_period_seconds: int = 3

    # Cluster configuration
    cluster_name: str = ""

    # Network configuration
    use_host_network: bool = False
    use_privileged_pod: bool = False
    need_infrawave_rdma: bool = False

    # Multi-node configuration
    use_ray_cluster: bool = False

    # PD separation configuration
    pd_separation: bool = False
    prefill_nodes: int = 0
    decode_nodes: int = 0
    minilb_replicas: int = 4

    # Additional configuration
    extra_cmds: str = ""
    extra_envs: str = ""
    api_key: str = ""

    # Deployment mode
    standalone_mode: bool = False
    deployment_mode: DeploymentMode = DeploymentMode.NORMAL

    # Router configuration
    use_sglang_router: bool = False
    is_router: bool = False

    # Deployment UUID for PD separation
    deployment_uuid: str = ""

    # Image version override
    image_version: Optional[str] = None

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Set tensor parallel size if not specified
        if self.tensor_parallel_size is None:
            self.tensor_parallel_size = str(self.gpus_per_pod)

        # Validate mutual exclusivity
        if self.use_host_network and self.need_infrawave_rdma:
            raise ValueError("USE_HOST_NETWORK and NEED_INFRAWAVE_RDMA are mutually exclusive")

        # Validate PD separation mode
        if self.prefill_nodes > 0 and self.decode_nodes > 0:
            self.pd_separation = True
            self.deployment_mode = DeploymentMode.PD_SEPARATION
            if self.backend != BackendType.SGLANG:
                raise ValueError("PD separation mode only supports sglang backend")

        # Set standalone mode if specified
        if self.standalone_mode:
            self.deployment_mode = DeploymentMode.STANDALONE

        # Validate GPU type
        if self.gpu_type not in GPUType:
            raise ValueError(f"Invalid GPU type: {self.gpu_type}")

        # Validate priority class
        if self.priority_class_name not in PriorityClass:
            raise ValueError(f"Invalid priority class: {self.priority_class_name}")

    @property
    def total_replicas(self) -> int:
        """Calculate total number of replicas."""
        return self.replicas * self.pods_per_job

    @property
    def worker_replicas(self) -> int:
        """Calculate number of worker replicas (excluding head)."""
        return self.replicas * (self.pods_per_job - 1)

    @property
    def is_multi_pod(self) -> bool:
        """Check if this is a multi-pod deployment."""
        return self.pods_per_job > 1

    @property
    def serve_base_path(self) -> str:
        """Get the base path for serving logs."""
        return f"/gpfs/users/{self.user_name}/northserve_logs/{self.app_name}-$JOB_LAST_TRANSITION_TIME"


@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""

    model_name: str
    model_path: str
    backend: BackendType
    cluster_name: str = ""
    namespace: str = "llm-serving"
    chip_name: str = "H100"

    def __post_init__(self):
        """Set chip name based on cluster."""
        if self.cluster_name and self.chip_name == "H100":
            # Assume other clusters have 4090
            self.chip_name = "4090"


@dataclass
class NorthLLMAPIConfig:
    """Configuration for North LLM API deployment."""

    version: str = "v0.2.3"
    replicas: int = 1
    namespace: str = "qiji"
    queue: str = "qiji"
    user_name: str = ""
    cluster_name: str = "bp"
    extra_envs: str = ""

    @property
    def app_name(self) -> str:
        """Generate app name from version."""
        return f"north-llm-api-{self.version}".replace(".", "-")


