#!/usr/bin/env python

# Copyright 2025 LUNA team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""LUNA Command Line Interface.

This module provides the main entry point for the LUNA CLI, supporting:
- Inference: Run trained policies on robots
- Server: Start model inference server
- Benchmarking: Measure inference latency

Usage:
    luna run <config.yaml> [options]
    luna server <config.yaml> [options]
    luna benchmark <config.yaml> [options]
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main entry point for LUNA CLI.

    Parses the first argument as the command and dispatches to the
    appropriate handler function.
    """
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Dispatch to the appropriate command handler
    if command == "train":
        train_command()
    elif command == "server":
        server_command()
    elif command == "run":
        run_command()
    elif command == "benchmark":
        benchmark_command()
    elif command in ["--help", "-h", "help"]:
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


def get_num_gpus():
    """Detect number of available GPUs.
    
    Uses CUDA_VISIBLE_DEVICES environment variable if set, otherwise
    queries PyTorch for the actual GPU count.
    
    Returns:
        int: Number of available GPUs.
    """
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    
    if cuda_visible is None:
        # CUDA_VISIBLE_DEVICES not set, check actual GPU count via PyTorch
        try:
            import torch
            return torch.cuda.device_count()
        except ImportError:
            return 0
    
    if cuda_visible == "":
        # Empty string means no GPUs are visible
        return 0
    
    # Count comma-separated GPU IDs (e.g., "0,1,2" -> 3 GPUs)
    return len(cuda_visible.split(","))


def train_command():
    """Handle 'luna train' command - REMOVED.

    Training functionality has been removed from this minimal version.
    """
    print("Training functionality has been removed from this minimal version.")
    sys.exit(1)


def run_command():
    """Handle 'luna run' command for robot inference.

    Loads a trained policy and runs inference on a connected robot.
    The config file specifies robot type, policy path, and runtime settings.
    """
    if len(sys.argv) < 3:
        print("Usage: luna run <config.yaml> [options]")
        print("\nExamples:")
        print("  luna run examples/inference/async.yaml")
        print("  luna run examples/inference/async.yaml --policy.path=outputs/train/pi05/checkpoints/050000/pretrained_model")
        print("  luna run examples/inference/async.yaml --control_time_s=120")
        sys.exit(1)

    config_path = sys.argv[2]

    # Validate config file exists
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    print(f"Running inference with config: {config_path}")

    # Build arguments for the run module
    run_args = [f"--config_path={config_path}"]
    run_args.extend(sys.argv[3:])

    # Import and execute the run function
    from luna.run import run

    # Reconstruct sys.argv for draccus config parser
    sys.argv = [sys.argv[0]] + run_args
    run()


def server_command():
    """Handle 'luna server' command for model inference server.

    Starts a model server that loads and keeps the model in memory,
    providing inference services via HTTP API.
    """
    if len(sys.argv) < 3:
        print("Usage: luna server <config.yaml> [--port=8000] [--host=0.0.0.0]")
        print("\nExamples:")
        print("  luna server examples/inference/bi_piper_follower.yaml")
        print("  luna server examples/inference/bi_piper_follower.yaml --port=8000")
        print("  luna server examples/inference/bi_piper_follower.yaml --port=8000 --host=0.0.0.0")
        sys.exit(1)

    config_path = sys.argv[2]

    # Validate config file exists
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    # Extract server arguments
    server_args = ["--config", config_path]

    # Parse optional arguments
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--port="):
            server_args.append(arg)
        elif arg.startswith("--host="):
            server_args.append(arg)
        elif arg == "--port" and i + 1 < len(sys.argv):
            server_args.extend(["--port", sys.argv[i + 1]])
            i += 1
        elif arg == "--host" and i + 1 < len(sys.argv):
            server_args.extend(["--host", sys.argv[i + 1]])
            i += 1
        i += 1

    # Import and run server
    from luna.model_server import main
    import sys as sys_module
    sys_module.argv = ["luna.server"] + server_args
    main()


def benchmark_command():
    """Handle 'luna benchmark' command for performance measurement.

    Runs benchmarks to measure inference latency and throughput.
    The benchmark type is determined by the 'type' field in the config file.
    """
    if len(sys.argv) < 3:
        print("Usage: luna benchmark <config.yaml> [options]")
        print("\nExamples:")
        print("  luna benchmark examples/benchmark/inference_latency.yaml")
        print("  luna benchmark examples/benchmark/inference_latency.yaml --num_samples=200")
        print("  luna benchmark examples/benchmark/inference_latency.yaml --output_file=results/latency.json")
        sys.exit(1)

    config_path = sys.argv[2]

    # Validate config file exists
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    print(f"Running benchmark with config: {config_path}")

    # Parse config to determine which benchmark to run
    import yaml
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    benchmark_type = config_dict.get('type', None)

    # Build arguments for the benchmark module
    benchmark_args = [f"--config_path={config_path}"]
    benchmark_args.extend(sys.argv[3:])

    # Reconstruct sys.argv for draccus config parser
    sys.argv = [sys.argv[0]] + benchmark_args

    # Dispatch to the appropriate benchmark based on type
    if benchmark_type == "inference_latency":
        print(f"Running inference latency benchmark...")
        from luna.benchmarks.benchmark_inference_latency import benchmark_inference_latency
        benchmark_inference_latency()
    else:
        print(f"Error: Unknown benchmark type: {benchmark_type}")
        sys.exit(1)


def print_usage():
    """Print CLI usage information and examples."""
    print("""
LUNA - Real-Time VLAs via Future-state-aware Asynchronous Inference

Usage:
  luna <command> [arguments]

Commands:
  server <config.yaml> [--port=8000] [--host=0.0.0.0]
      Start model inference server (keeps model in memory)

  run <config.yaml> [options]
      Run inference with a trained policy on a robot
      Use --model_server_url to connect to a remote server

  benchmark <config.yaml> [options]
      Benchmark inference latency of a trained policy

  help, --help, -h
      Show this help message

Server Examples:
  # Start model server (keeps model in memory)
  luna server examples/inference/bi_piper_follower.yaml

  # Start server on custom port
  luna server examples/inference/bi_piper_follower.yaml --port=8000

  # Start server accessible from network
  luna server examples/inference/bi_piper_follower.yaml --port=8000 --host=0.0.0.0

Inference Examples:
  # Run inference with default settings (loads model locally)
  luna run examples/inference/async.yaml

  # Run inference using remote model server
  luna run examples/inference/async.yaml --model_server_url=http://localhost:8000

  # Override policy path
  luna run examples/inference/async.yaml --policy.path=outputs/train/pi05/checkpoints/050000/pretrained_model

  # Override control time and overlap settings
  luna run examples/inference/async.yaml --control_time_s=120 --inference_overlap_steps=6

Benchmark Examples:
  # Benchmark inference latency
  luna benchmark examples/benchmark/inference_latency.yaml

  # Override number of samples and output file
  luna benchmark examples/benchmark/inference_latency.yaml --num_samples=200 --output_file=results/latency.json

For more information, see:
  https://github.com/mit-han-lab/luna
    """)


if __name__ == "__main__":
    main()
