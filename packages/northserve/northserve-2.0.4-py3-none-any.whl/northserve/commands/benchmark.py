"""Benchmark command implementation."""

import click
from pathlib import Path

from northserve.models.deployment import BenchmarkConfig
from northserve.models.enums import BackendType
from northserve.core.benchmark_engine import BenchmarkEngine
from northserve.constants import DEFAULT_BACKEND
from northserve.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def benchmark():
    """Benchmark commands for performance testing."""
    pass


@benchmark.command(name='launch')
@click.option('--model-name', required=True, help='Model name to benchmark')
@click.option('--model-path', required=True, help='Path to model weights')
@click.option('--backend', default=DEFAULT_BACKEND, help=f'Backend type (default: {DEFAULT_BACKEND})')
@click.option('--cluster-name', default='', help='Cluster name')
@click.option('--namespace', default='llm-serving', help='Kubernetes namespace (default: llm-serving)')
@click.option('-y', '--yes', 'skip_confirmation', is_flag=True, help='Skip confirmation prompt')
def benchmark_launch(
    model_name: str,
    model_path: str,
    backend: str,
    cluster_name: str,
    namespace: str,
    skip_confirmation: bool,
):
    """Launch a benchmark test on a running deployment."""
    try:
        # Create benchmark config
        config = BenchmarkConfig(
            model_name=model_name,
            model_path=model_path,
            backend=BackendType(backend),
            cluster_name=cluster_name,
            namespace=namespace,
        )

        # Create benchmark engine and launch
        benchmark_engine = BenchmarkEngine()
        benchmark_engine.launch_benchmark(config, skip_confirmation)

    except Exception as e:
        logger.error(f"Failed to launch benchmark: {e}")
        raise click.Abort()


@benchmark.command(name='report')
@click.option('--log-path', required=True, type=click.Path(exists=True, path_type=Path), help='Path to benchmark logs')
@click.option('--config-file', required=True, type=click.Path(exists=True, path_type=Path), help='Path to Feishu config file')
def benchmark_report(
    log_path: Path,
    config_file: Path,
):
    """Report benchmark results to Feishu."""
    try:
        # Create benchmark engine and report
        benchmark_engine = BenchmarkEngine()
        benchmark_engine.report_benchmark(log_path, config_file)

    except Exception as e:
        logger.error(f"Failed to report benchmark: {e}")
        raise click.Abort()


