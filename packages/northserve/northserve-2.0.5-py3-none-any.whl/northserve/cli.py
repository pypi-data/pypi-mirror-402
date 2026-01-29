"""Main CLI interface for NorthServing."""

import click
import sys

from northserve.utils.logger import setup_logger, get_logger
from northserve.utils.updater import check_update, skip_update_check
from northserve import __version__

# Setup logger
logger = setup_logger()


@click.group()
@click.version_option(version=__version__, prog_name="northserve")
@click.pass_context
def main(ctx):
    """
    NorthServing - A one-click LLM serving deployment tool.

    Deploy and manage LLM serving infrastructure on Kubernetes using Volcano jobs.
    """
    # Check for updates unless skipped
    if not skip_update_check():
        try:
            check_update()
        except Exception as e:
            logger.debug(f"Update check failed: {e}")


def show_examples():
    """Display usage examples."""
    examples = """
The following commands are copy & paste ready to start models:
==== Start models:
new model:
  northserve launch --model-name qwen2.5-0.5b-instruct-inst-1 --served-model-name qwen2.5-0.5b-instruct --model-path /gpfs/models/huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/ --replicas 4 --gpus-per-pod 1 --profile generation --backend nla-vllm
qwen2-72b-instruct:
  northserve launch --model-name qwen2-72b-instruct --model-path /gpfs/models/huggingface.co/Qwen/Qwen2-72B-Instruct/ --replicas 1 --gpus-per-pod 8 --profile generation
mistral-large-instruct:
  northserve launch --model-name mistral-large-instruct --model-path /gpfs/models/huggingface.co/mistral-ai/Mistral-Large-Instruct-2407/ --replicas 1 --gpus-per-pod 8 --profile generation --extra-cmds "--max-num-batched-tokens=16384 --max-model-len=16384 --enforce-eager"
deepseek-v2-chat (BF16):
  northserve launch --model-name deepseek-v2-chat --model-path /gpfs/models/huggingface.co/deepseek-ai/DeepSeek-V2-Chat/ --replicas 1 --gpus-per-pod 8 --profile generation --backend crossing --extra-cmds "--max-seq-len 32768" --extra-envs "CROSSING_SERVER_RETURN_USAGE_IN_STREAM=1 CROSSING_MODEL_WARMUP_SIZES=default CROSSING_FLASH_DECODING_MAX_CHUNKS=64 CROSSING_ENABLE_FAST_LOAD_WEIGHTS=1 CROSSING_DEEPSEEK_V2_SPLIT_FORWARD_SEQ_LEN_THRESHOLD=4096 SILICON_LLM_LICENSE_KEY=$LICENSE"
deepseek-v2-chat-fp8 (FP8):
  northserve launch --model-name deepseek-v2-chat-fp8 --model-path /gpfs/models/huggingface.co/otavia/DeepSeek-V2-X-fp8/ --replicas 1 --gpus-per-pod 8 --profile generation --backend crossing --extra-cmds "--max-seq-len 32768" --extra-envs "CROSSING_SERVER_RETURN_USAGE_IN_STREAM=1 CROSSING_MODEL_WARMUP_SIZES=default CROSSING_FLASH_DECODING_MAX_CHUNKS=64 CROSSING_ENABLE_FAST_LOAD_WEIGHTS=1 CROSSING_DEEPSEEK_V2_SPLIT_FORWARD_SEQ_LEN_THRESHOLD=4096 SILICON_LLM_LICENSE_KEY=$LICENSE"

==== Check service status:
northserve list

==== Stop models:
qwen2-72b-instruct: northserve stop --model-name qwen2-72b-instruct
mistral-large-instruct: northserve stop --model-name mistral-large-instruct
deepseek-v2-chat: northserve stop --model-name deepseek-v2-chat --backend crossing
deepseek-v2-chat-fp8: northserve stop --model-name deepseek-v2-chat-fp8 --backend crossing
"""
    click.echo(examples)


# Import and register command modules
from northserve.commands import launch, stop, list as list_cmd, benchmark, north_llm_api

# Register commands
main.add_command(launch.launch)
main.add_command(stop.stop)
main.add_command(list_cmd.list_models)
main.add_command(benchmark.benchmark)
main.add_command(north_llm_api.launch_north_llm_api)
main.add_command(north_llm_api.stop_north_llm_api)


# Intercept when no command is given to show examples
@main.result_callback()
@click.pass_context
def process_result(ctx, result, **kwargs):
    """Process result and show examples if no command was given."""
    if ctx.invoked_subcommand is None:
        show_examples()


if __name__ == "__main__":
    main()


