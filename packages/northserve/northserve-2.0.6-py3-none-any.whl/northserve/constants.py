"""Constants and default values for NorthServing."""

import os
import sys
from pathlib import Path

# Base paths - handle both development and installed package
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_PATH = Path(sys.executable).parent
elif '__file__' in globals():
    # Try to find the actual project root
    current = Path(__file__).parent.parent
    # Check if we're in site-packages (installed package)
    if 'site-packages' in str(current):
        # Look for data files relative to package installation
        BASE_PATH = current
    else:
        # Development mode - use project root
        BASE_PATH = current
else:
    BASE_PATH = Path.cwd()

USER_NAME = os.getenv("USER", os.getenv("USERNAME", "unknown"))

# Default configuration values
DEFAULT_NAMESPACE = "qiji"
DEFAULT_QUEUE = "qiji"
DEFAULT_INGRESS_NAME = "northserving-ingress-nginx"
DEFAULT_PRIORITY_CLASS = "low-priority-job"
DEFAULT_PROTOCOL = "openai"
DEFAULT_BACKEND = "vllm"
DEFAULT_PROFILE = "generation"
DEFAULT_REPLICAS = 1
DEFAULT_GPUS_PER_POD = 1
DEFAULT_PODS_PER_JOB = 1
DEFAULT_VOLUMES = "gpfs:/gpfs"
DEFAULT_TERMINATION_GRACE_PERIOD = 3
DEFAULT_MINILB_REPLICAS = 4
DEFAULT_PIPELINE_PARALLEL_SIZE = "1"

# Server configuration
INFRAWAVE_SERVER_HOST = os.getenv("K8S_SERVER_HOST", "10.51.6.7:31000")

# User credentials - read from environment variables
INFRAWAVES_USERNAME = os.getenv("INFRAWAVES_USERNAME", "")
INFRAWAVES_PASSWORD = os.getenv("INFRAWAVES_PASSWORD", "")

# Paths - data directories are at project root
YAML_TEMPLATES_DIR = BASE_PATH / "yaml_templates"
CONFIGS_DIR = BASE_PATH / "configs"
TOOLS_DIR = BASE_PATH / "tools"
BENCHMARK_DIR = BASE_PATH / "benchmark"

# Auto-update
UPDATE_MARKER_FILE = Path.home() / ".northserve" / "marker"

# Logging
LOG_BASE_PATH = Path.home() / ".northserve" / "logs"

# Valid choices
VALID_GPU_TYPES = ["h20", "4090d", "gpu"]
VALID_PRIORITY_CLASSES = ["high-priority-job", "low-priority-job", "higher-priority-job"]
VALID_BACKENDS = ["vllm", "sglang", "bp-sglang", "bp-vllm", "bp-vllm-wp", "crossing"]
VALID_PROTOCOLS = ["openai", "anthropic", "weaver"]

# API endpoints
SERVICE_URL = "http://10.51.6.110/v1/"
STANDALONE_SERVICE_IPS = ["10.51.6.6", "10.51.6.7", "10.51.6.8", "10.51.6.31", "10.51.6.32", "10.51.6.33"]


