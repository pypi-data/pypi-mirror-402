# NorthServing

A one-click LLM serving deployment tool for Kubernetes with Volcano job scheduling.

## Overview

NorthServing (北服) is a Python-based tool that simplifies the deployment and management of Large Language Model (LLM) serving infrastructure on Kubernetes. It provides a unified command-line interface for deploying models using various backends (vLLM, SGLang, etc.) with support for multi-node, multi-GPU configurations.

## Features

- 🚀 **One-Click Deployment**: Launch LLM serving with a single command
- 🔄 **Multiple Backends**: Support for vLLM, SGLang, and other inference engines
- 📊 **Performance Benchmarking**: Built-in benchmarking tools with Feishu reporting
- 🌐 **Multi-Cluster Support**: Deploy across different Kubernetes clusters
- ⚡ **Advanced Configurations**:
  - PD (Prefill-Decode) separation mode
  - Multi-node deployments with Ray
  - Tensor/Pipeline parallelism
  - Custom resource scheduling
- 🧪 **Well-Tested**: Comprehensive test suite with >80% coverage

## Installation

### Prerequisites

- Python >= 3.8
- Kubernetes cluster with Volcano scheduler
- kubectl configured
- Access to Infrawave API (for job management)

### Install from PyPI

```bash
# Install from internal PyPI server
pip install northserve -i http://10.51.6.7:31624/simple/ --trusted-host 10.51.6.7 --extra-index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# Or configure pip once (recommended)
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = http://10.51.6.7:31624/simple/
trusted-host = 10.51.6.7
EOF

# Then install normally
pip install northserve
```

### Install from Source

```bash
git clone https://github.com/china-qijizhifeng/NorthServing.git
cd NorthServing

# Install dependencies from Tsinghua mirror
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# Install in development mode
pip install -e .
```

For detailed installation guide, see [INSTALL.md](INSTALL.md)

### Configuration

Set up your credentials using environment variables:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export INFRAWAVES_USERNAME='your_username'
export INFRAWAVES_PASSWORD='your_password'

# Apply changes
source ~/.bashrc  # or source ~/.zshrc
```

## Quick Start

### Launch a Model

```bash
northserve launch \
  --model-name qwen2-72b-instruct \
  --model-path /gpfs/models/huggingface.co/Qwen/Qwen2-72B-Instruct/ \
  --replicas 1 \
  --gpus-per-pod 8 \
  --profile generation
```

### List Running Models

```bash
northserve list
```

### Stop a Model

```bash
northserve stop --model-name qwen2-72b-instruct
```

## Command Reference

### `northserve launch`

Launch a new LLM serving deployment.

**Required Options:**
- `--model-name`: Model name for identification
- `--model-path`: Path to model weights (optional for some backends)

**Common Options:**
- `--backend`: Inference backend (default: vllm)
  - `vllm`: vLLM inference engine
  - `sglang`: SGLang inference engine
  - `bp-vllm`: BP-optimized vLLM
  - `crossing`: Crossing inference engine
- `--protocol`: API protocol (default: openai)
  - `openai`: OpenAI-compatible API
  - `anthropic`: Anthropic-compatible API
- `--replicas`: Number of replicas (default: 1)
- `--gpus-per-pod`: GPUs per pod (default: 1)
- `--pods-per-job`: Pods per job for multi-node (default: 1)
- `--gpu-type`: GPU type - `gpu`, `h20`, `4090d`
- `--namespace`: Kubernetes namespace (default: qiji)
- `--priority-class-name`: Priority class (default: low-priority-job)

**Advanced Options:**
- `--extra-cmds`: Additional command-line arguments for the engine
- `--extra-envs`: Extra environment variables (KEY=value KEY2=value2)
- `--tensor-parallel-size`: Tensor parallelism (defaults to gpus-per-pod)
- `--pipeline-parallel-size`: Pipeline parallelism (default: 1)
- `--prefill-nodes`: Prefill nodes for PD separation (SGLang only)
- `--decode-nodes`: Decode nodes for PD separation (SGLang only)
- `--use-host-network`: Use host network
- `--standalone`: Create standalone service with NodePort
- `-y, --yes`: Skip confirmation prompts

**Examples:**

Simple deployment:
```bash
northserve launch --model-name llama2-7b --model-path /gpfs/models/llama2-7b --gpus-per-pod 1
```

Multi-GPU deployment:
```bash
northserve launch \
  --model-name qwen2-72b \
  --model-path /gpfs/models/qwen2-72b \
  --gpus-per-pod 8 \
  --replicas 2
```

With custom arguments:
```bash
northserve launch \
  --model-name mistral-large \
  --model-path /gpfs/models/mistral-large \
  --gpus-per-pod 8 \
  --extra-cmds "--max-num-batched-tokens=16384 --max-model-len=16384 --enforce-eager"
```

PD separation mode (SGLang):
```bash
northserve launch \
  --model-name qwen2-72b \
  --model-path /gpfs/models/qwen2-72b \
  --backend sglang \
  --gpus-per-pod 8 \
  --prefill-nodes 2 \
  --decode-nodes 4 \
  --minilb-replicas 4
```

### `northserve stop`

Stop a running deployment.

**Options:**
- `--model-name`: Model name to stop (required)
- `--backend`: Backend type (default: vllm)
- `--namespace`: Kubernetes namespace (default: qiji)
- `--standalone`: Stop standalone service
- `-y, --yes`: Skip confirmation

**Example:**
```bash
northserve stop --model-name qwen2-72b-instruct
```

### `northserve list`

List all deployed models and their status.

**Example:**
```bash
northserve list
```

### `northserve benchmark`

Performance benchmarking commands.

#### `northserve benchmark launch`

Launch a benchmark test on a running deployment.

**Options:**
- `--model-name`: Model name to benchmark (required)
- `--model-path`: Path to model weights (required)
- `--backend`: Backend type
- `--namespace`: Kubernetes namespace

**Example:**
```bash
northserve benchmark launch \
  --model-name qwen2-72b \
  --model-path /gpfs/models/qwen2-72b \
  --backend vllm
```

#### `northserve benchmark report`

Report benchmark results to Feishu.

**Options:**
- `--log-path`: Path to benchmark logs (required)
- `--config-file`: Path to Feishu config file (required)

**Example:**
```bash
northserve benchmark report \
  --log-path ~/.northserve/logs/qwen2-72b-vllm-server-0 \
  --config-file ~/.northserve/feishu.json
```

### `northserve launch_north_llm_api`

Launch the North LLM API service.

**Options:**
- `--version`: Version to deploy (default: v0.2.3)
- `--replicas`: Number of replicas (default: 1)
- `--namespace`: Kubernetes namespace (default: qiji)

**Example:**
```bash
northserve launch_north_llm_api --version v0.2.3 --replicas 2
```

### `northserve stop_north_llm_api`

Stop the North LLM API service.

**Example:**
```bash
northserve stop_north_llm_api --version v0.2.3
```

## Architecture

NorthServing follows a modular architecture:

```
┌─────────────────────────────────────┐
│         CLI Interface (Click)        │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐         ┌─────▼──────┐
│Commands│         │Core Logic  │
└───┬────┘         └─────┬──────┘
    │                    │
    │    ┌───────────────┴────────────────┐
    │    │                                 │
    │ ┌──▼──────────┐          ┌─────────▼────────┐
    │ │Job Manager  │          │Config Builder    │
    │ └──┬──────────┘          └─────────┬────────┘
    │    │                                │
    │ ┌──▼────────────┐        ┌─────────▼────────┐
    └─┤API Clients    │        │Template Renderer │
      └───────────────┘        └──────────────────┘
```

### Key Components

- **CLI Layer**: Click-based command-line interface
- **Commands**: Individual command implementations (launch, stop, list, etc.)
- **Core Logic**:
  - `JobManager`: Orchestrates deployment lifecycle
  - `ConfigBuilder`: Builds deployment configurations
  - `TemplateRenderer`: Jinja2 template rendering
  - `BenchmarkEngine`: Performance testing
- **API Clients**:
  - `InfrawaveClient`: Infrawave API integration
  - `KubernetesClient`: Direct kubectl operations
- **Models**: Type-safe data models with validation
- **Utils**: Validators, logger, helpers

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=northserve --cov-report=html

# Run specific test file
pytest tests/test_core/test_config_builder.py
```

### Code Quality

```bash
# Format code
black northserve tests

# Sort imports
isort northserve tests

# Lint
flake8 northserve tests

# Type checking
mypy northserve
```

## Migration from Shell Version

The Python version maintains backward compatibility with the shell-based version:

- **Same Command Interface**: All commands work the same way
- **Same Configuration Files**: YAML configs and templates unchanged
- **Same Output**: Identical deployment behavior

To use the new version, simply install it and use `northserve` instead of the old shell script.

## Troubleshooting

### Common Issues

**"Config file not found"**
- Ensure `~/.config/northjob/userinfo.conf` exists with valid credentials

**"Failed to create job"**
- Check Infrawave API connectivity
- Verify your credentials are correct
- Ensure you have permissions for the namespace

**"Template not found"**
- Make sure you installed from the repository root
- YAML templates should be in `yaml_templates/` directory

**"Invalid backend"**
- Use one of: vllm, sglang, bp-vllm, crossing
- Note: `nla-vllm` is deprecated, use `bp-vllm`

### Debug Mode

Enable debug logging:

```bash
export NORTHSERVE_LOG_LEVEL=DEBUG
northserve launch ...
```

Skip auto-update checks:

```bash
export NORTHSERVE_SKIP_UPDATE=1
northserve launch ...
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/china-qijizhifeng/NorthServing/issues
- Documentation: See this README and inline help (`northserve --help`)

## Why NorthServing?

- ✅ **Training-Inference Unified Scheduling**: Uses Volcano jobs compatible with training workloads
- ✅ **Multi-Backend Support**: Unified interface for different inference engines
- ✅ **Cross-Cluster Deployment**: Deploy to multiple clusters with unified ingress
- ✅ **Production Ready**: Mature codebase with comprehensive testing
- ✅ **Easy Automation**: Command-line interface perfect for CI/CD pipelines
