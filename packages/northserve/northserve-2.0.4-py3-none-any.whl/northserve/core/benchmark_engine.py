"""Benchmark execution engine."""

from pathlib import Path
from typing import Optional

from northserve.models.deployment import BenchmarkConfig
from northserve.clients.kubernetes import KubernetesClient
from northserve.constants import BENCHMARK_DIR, LOG_BASE_PATH, USER_NAME
from northserve.utils.logger import get_logger
from northserve.utils.helpers import confirm_action

logger = get_logger(__name__)


class BenchmarkEngineError(Exception):
    """Exception raised for benchmark engine errors."""
    pass


class BenchmarkEngine:
    """Manages benchmark execution and reporting."""

    def __init__(self, k8s_client: Optional[KubernetesClient] = None):
        """
        Initialize benchmark engine.

        Args:
            k8s_client: Kubernetes client (creates default if None)
        """
        self.k8s_client = k8s_client or KubernetesClient()
        self.benchmark_script = BENCHMARK_DIR / "benchmark_serving_throughput.sh"

    def launch_benchmark(
        self,
        config: BenchmarkConfig,
        skip_confirmation: bool = False
    ) -> None:
        """
        Launch a benchmark test.

        Args:
            config: Benchmark configuration
            skip_confirmation: Skip user confirmation

        Raises:
            BenchmarkEngineError: If benchmark launch fails
        """
        # Build app name
        app_name = f"{config.model_name}-{config.backend.value}"
        if config.cluster_name:
            app_name = f"{app_name}-{config.cluster_name}"

        # Get number of GPUs from job
        try:
            num_gpus = self.k8s_client.get_volcano_job_gpus(
                app_name,
                config.namespace
            )
        except Exception as e:
            raise BenchmarkEngineError(f"Failed to get GPU count: {e}")

        pod_name = f"{app_name}-server-0"
        log_path = LOG_BASE_PATH / pod_name

        # Display benchmark info
        logger.info(f"NUM_GPUS: {num_gpus}")
        logger.info(f"CHIP_NAME: {config.chip_name}")
        logger.info(f"BACKEND: {config.backend.value}")
        logger.info(f"Going to run perf test to pod: {pod_name} in namespace {config.namespace}")
        logger.info("Make sure there's no production requests.")

        # Confirm action
        if not confirm_action("Continue", skip_confirmation):
            logger.info("Canceled.")
            return

        # Ensure log directory exists
        log_path.mkdir(parents=True, exist_ok=True)

        # Build benchmark command
        benchmark_cmd = (
            f"nohup bash {self.benchmark_script} "
            f"{config.model_name} {config.model_path} {log_path} "
            f"{config.backend.value} {config.chip_name} {num_gpus} "
            f"&> {log_path}/run.log &"
        )

        # Execute benchmark in pod
        try:
            self.k8s_client.exec_command(
                pod_name,
                ["bash", "-c", benchmark_cmd],
                namespace=config.namespace
            )
            logger.info(f"Benchmark launched. Logs will be saved to: {log_path}")

        except Exception as e:
            raise BenchmarkEngineError(f"Failed to launch benchmark: {e}")

    def report_benchmark(
        self,
        log_path: Path,
        config_file: Path
    ) -> None:
        """
        Report benchmark results to Feishu.

        Args:
            log_path: Path to benchmark logs
            config_file: Path to Feishu config file

        Raises:
            BenchmarkEngineError: If reporting fails
        """
        import subprocess

        logger.info(f"Log path: {log_path}")
        logger.info(f"Config file: {config_file}")

        report_script = BENCHMARK_DIR / "report_to_feishu.py"

        if not report_script.exists():
            raise BenchmarkEngineError(f"Report script not found: {report_script}")

        if not log_path.exists():
            raise BenchmarkEngineError(f"Log path not found: {log_path}")

        if not config_file.exists():
            raise BenchmarkEngineError(f"Config file not found: {config_file}")

        # Run report script
        cmd = [
            "python3",
            str(report_script),
            "--log-path",
            str(log_path),
            "--config-file",
            str(config_file)
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Benchmark report completed successfully")
            logger.info(result.stdout)

        except subprocess.CalledProcessError as e:
            raise BenchmarkEngineError(
                f"Failed to report benchmark results: {e.stderr}"
            )


