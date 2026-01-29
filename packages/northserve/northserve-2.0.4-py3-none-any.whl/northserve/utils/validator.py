"""Input validation utilities."""

from typing import List, Optional
from pathlib import Path

from northserve.models.enums import BackendType, GPUType, PriorityClass
from northserve.constants import (
    VALID_GPU_TYPES,
    VALID_PRIORITY_CLASSES,
    VALID_BACKENDS,
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_gpu_type(gpu_type: str) -> None:
    """
    Validate GPU type.

    Args:
        gpu_type: GPU type to validate

    Raises:
        ValidationError: If GPU type is invalid
    """
    if gpu_type not in VALID_GPU_TYPES:
        raise ValidationError(
            f"Invalid GPU type: {gpu_type}. Must be one of: {', '.join(VALID_GPU_TYPES)}"
        )


def validate_priority_class(priority_class: str) -> None:
    """
    Validate priority class name.

    Args:
        priority_class: Priority class to validate

    Raises:
        ValidationError: If priority class is invalid
    """
    if priority_class not in VALID_PRIORITY_CLASSES:
        raise ValidationError(
            f"Invalid priority class: {priority_class}. "
            f"Must be one of: {', '.join(VALID_PRIORITY_CLASSES)}"
        )


def validate_backend(backend: str) -> None:
    """
    Validate backend type.

    Args:
        backend: Backend to validate

    Raises:
        ValidationError: If backend is invalid or deprecated
    """
    # Check for deprecated backends
    if backend == "nla-vllm":
        raise ValidationError(
            "Backend 'nla-vllm' is deprecated. Please use 'bp-vllm' instead."
        )

    if backend not in VALID_BACKENDS:
        raise ValidationError(
            f"Invalid backend: {backend}. Must be one of: {', '.join(VALID_BACKENDS)}"
        )


def validate_model_path(model_path: Optional[str]) -> None:
    """
    Validate model path exists.

    Args:
        model_path: Path to model

    Raises:
        ValidationError: If path doesn't exist
    """
    if model_path and not Path(model_path).exists():
        raise ValidationError(f"Model path does not exist: {model_path}")


def validate_volumes(volumes_str: str) -> List[str]:
    """
    Validate and parse volume configuration.

    Args:
        volumes_str: Comma-separated volume specs (name:path,name:path,...)

    Returns:
        List of validated volume specs

    Raises:
        ValidationError: If volume format is invalid
    """
    if not volumes_str.strip():
        raise ValidationError("At least one volume must be specified")

    volumes = []
    for volume in volumes_str.split(","):
        volume = volume.strip()
        if ":" not in volume:
            raise ValidationError(
                f"Invalid volume format: {volume}. Expected 'name:path'"
            )
        volumes.append(volume)

    return volumes


def validate_extra_envs(extra_envs: str) -> dict:
    """
    Validate and parse extra environment variables.

    Args:
        extra_envs: Space-separated env vars (KEY=value KEY2=value2)

    Returns:
        Dictionary of environment variables

    Raises:
        ValidationError: If format is invalid
    """
    if not extra_envs.strip():
        return {}

    env_dict = {}
    for item in extra_envs.split():
        if "=" not in item:
            raise ValidationError(
                f"Invalid environment variable format: {item}. Expected 'KEY=value'"
            )
        key, value = item.split("=", 1)
        env_dict[key] = value

    return env_dict


def validate_positive_int(value: int, name: str) -> None:
    """
    Validate that a value is a positive integer.

    Args:
        value: Value to check
        name: Parameter name for error message

    Raises:
        ValidationError: If value is not positive
    """
    if value <= 0:
        raise ValidationError(f"{name} must be a positive integer, got: {value}")


def validate_non_negative_int(value: int, name: str) -> None:
    """
    Validate that a value is a non-negative integer.

    Args:
        value: Value to check
        name: Parameter name for error message

    Raises:
        ValidationError: If value is negative
    """
    if value < 0:
        raise ValidationError(f"{name} must be a non-negative integer, got: {value}")


def validate_mutual_exclusivity(
    flag1: bool,
    flag1_name: str,
    flag2: bool,
    flag2_name: str
) -> None:
    """
    Validate that two flags are mutually exclusive.

    Args:
        flag1: First flag value
        flag1_name: First flag name
        flag2: Second flag value
        flag2_name: Second flag name

    Raises:
        ValidationError: If both flags are True
    """
    if flag1 and flag2:
        raise ValidationError(
            f"{flag1_name} and {flag2_name} are mutually exclusive. "
            f"Only one can be true at a time."
        )


def validate_pd_separation_mode(
    backend: str,
    prefill_nodes: int,
    decode_nodes: int
) -> None:
    """
    Validate PD separation mode configuration.

    Args:
        backend: Backend type
        prefill_nodes: Number of prefill nodes
        decode_nodes: Number of decode nodes

    Raises:
        ValidationError: If configuration is invalid
    """
    if prefill_nodes > 0 and decode_nodes > 0:
        # PD separation mode is enabled
        if backend != "sglang":
            raise ValidationError(
                "PD separation mode only supports sglang backend"
            )
        validate_positive_int(prefill_nodes, "prefill_nodes")
        validate_positive_int(decode_nodes, "decode_nodes")


