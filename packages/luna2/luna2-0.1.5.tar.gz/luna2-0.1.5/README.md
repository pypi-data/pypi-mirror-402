# LUNA: Real-Time VLAs via Future-state-aware Asynchronous Inference

LUNA is an efficient and easy-to-use framework for VLAs inference.

## Features

LUNA is efficient through:
- **Asynchronous Inference**: Overlaps action prediction with execution to achieve real-time performance
- **Future-state Awareness**: Uses predicted future states for more accurate action planning

LUNA is easy to use with:
- **Simple CLI**: Clean command-line interface for inference and serving
- **Flexible Configuration**: YAML-based configuration for easy customization

## Installation

```bash
# Create conda environment
conda create -n "luna" python=3.10
conda activate luna

# Install dependencies
pip install -e .
```

## Usage

```bash
# Run inference with a trained policy
luna run examples/inference/async.yaml

# Start model server for remote inference
luna server examples/inference/async.yaml

# Run inference with custom parameters
luna run examples/inference/async.yaml --action_quant_ratio=2
```

LUNA is designed to be flexible and extensible, allowing users to easily integrate new policies and customize existing ones.

