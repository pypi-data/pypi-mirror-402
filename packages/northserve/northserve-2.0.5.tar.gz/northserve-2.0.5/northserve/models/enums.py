"""Enumerations for NorthServing."""

from enum import Enum


class BackendType(str, Enum):
    """Supported inference backends."""

    VLLM = "vllm"
    SGLANG = "sglang"
    BP_VLLM = "bp-vllm"
    BP_VLLM_WP = "bp-vllm-wp"
    BP_VLLM_WP_2 = "bp-vllm-wp-2"
    NLA_SGLANG = "nla-sglang"
    CROSSING = "crossing"


class ProtocolType(str, Enum):
    """Supported API protocols."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    WEAVER = "weaver"
    SERVICE = "service"


class GPUType(str, Enum):
    """Supported GPU types."""

    GPU = "gpu"
    H20 = "h20"
    GPU_4090D = "4090d"


class PriorityClass(str, Enum):
    """Kubernetes priority classes."""

    HIGH = "high-priority-job"
    LOW = "low-priority-job"
    HIGHER = "higher-priority-job"


class ProfileType(str, Enum):
    """Deployment profiles for different scenarios."""

    GENERATION = "generation"
    SLEEP = "sleep"
    DEBUG = "debug"
    MULTINODE = "multinode"
    MULTINODESERVING = "multinodeserving"
    PDPRE = "pdpre"
    PDDEC = "pddec"
    MINILB = "minilb"


class DeploymentMode(str, Enum):
    """Deployment modes."""

    NORMAL = "normal"
    STANDALONE = "standalone"
    PD_SEPARATION = "pd_separation"


