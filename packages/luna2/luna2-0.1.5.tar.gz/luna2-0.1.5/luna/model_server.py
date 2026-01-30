#!/usr/bin/env python
"""LUNA Model Inference Server.

This server loads and keeps the model in memory, providing inference services
via HTTP API. This allows clients to use the model without reloading it.

Usage:
    python -m luna.model_server --config examples/inference/bi_piper_follower.yaml --port 8000
"""

import argparse
import base64
import logging
import os
import pickle
import signal
import sys
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import robot adapters FIRST to ensure config classes are registered
# This MUST happen before importing RunConfig, which uses RobotConfig
try:
    from luna.robots.bi_piper_follower_adapter import (  # noqa: F401
        BiPIPERFollowerConfig,
        BiPIPERFollowerEeposeConfig,
    )
except ImportError:
    # Adapter not available, robot configs may not be registered
    pass

from luna.configs.run_config import RunConfig
from luna.run import load_and_compile_policy, prepare_observation_for_inference
from lerobot.utils.utils import get_safe_torch_device
from lerobot.configs import parser

# Disable CUDA graph for multi-threaded Flask server
# CUDA graph optimization doesn't work well in multi-threaded environments
# This must be set before torch.compile is called
os.environ["TORCH_COMPILE_DISABLE_CUDAGRAPHS"] = "1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Global policy instance
_policy: Any = None
_policy_config: Any = None
_device: torch.device = None
_robot_type: str = "piper_follower"  # Default robot type


@parser.wrap()
def _load_config_wrapper(cfg: RunConfig) -> RunConfig:
    """Wrapper function to use parser.wrap() for loading config."""
    return cfg


def load_model(config_path: str):
    """Load and compile the policy model."""
    global _policy, _policy_config, _device, _robot_type
    
    logger.info(f"Loading model from config: {config_path}")
    
    # Ensure robot adapter configs are registered before parsing
    # This must happen here to ensure registration happens before parser.wrap() tries to decode
    try:
        from luna.robots.bi_piper_follower_adapter import (  # noqa: F401
            BiPIPERFollowerConfig,
            BiPIPERFollowerEeposeConfig,
        )
        # Verify registration
        from lerobot.robots.config import RobotConfig
        if "bi_piper_follower_eepose" in RobotConfig._choice_registry:
            logger.debug("bi_piper_follower_eepose config class is registered")
        else:
            logger.warning("bi_piper_follower_eepose config class is NOT registered!")
            # Try to register manually
            RobotConfig._choice_registry["bi_piper_follower_eepose"] = BiPIPERFollowerEeposeConfig
            logger.info("Manually registered bi_piper_follower_eepose config class")
    except ImportError as e:
        logger.warning(f"Could not import bi_piper_follower adapter: {e}")
    except Exception as e:
        logger.error(f"Error during config registration: {e}", exc_info=True)

    # Parse config using the same method as run.py
    # Save original argv
    original_argv = sys.argv.copy()

    try:
        # Set up argv for parser (same as run_command does)
        sys.argv = ["luna.server", f"--config_path={config_path}"]

        # Use parser.wrap() wrapper to load config
        cfg = _load_config_wrapper()

    finally:
        # Restore original argv
        sys.argv = original_argv
    
    # Get robot type from config
    _robot_type = cfg.robot.type if hasattr(cfg.robot, 'type') else "piper_follower"
    
    # Load policy
    _policy = load_and_compile_policy(cfg)
    _policy_config = cfg.policy
    _device = get_safe_torch_device(cfg.policy.device)
    
    logger.info("Model loaded and ready for inference")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "model_loaded": _policy is not None})


@app.route("/predict_binary", methods=["POST"])
def predict_binary():
    """Predict action chunk from observation using binary (pickle) format.
    
    Request: Binary pickle data containing observation dictionary
    Response: Binary pickle data containing action_chunk numpy array
    
    This is the fastest format as it avoids JSON serialization entirely.
    """
    if _policy is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    try:
        # Performance monitoring
        deserialize_start = time.perf_counter()
        
        # Deserialize binary observation data
        observation_bytes = request.data
        observation_dict = pickle.loads(observation_bytes)
        
        # Extract single_task if provided
        single_task = observation_dict.pop("_single_task", observation_dict.get("task", ""))
        
        # Convert numpy arrays to torch tensors
        obs_dict = {}
        for key, value in observation_dict.items():
            if key == "task":
                obs_dict[key] = value
            elif isinstance(value, np.ndarray):
                # Convert numpy array to torch tensor and move to device
                tensor = torch.from_numpy(value).to(_device)
                # Add batch dimension if missing (for images: [C, H, W] -> [1, C, H, W])
                if key.startswith("observation.images.") and tensor.ndim == 3:
                    tensor = tensor.unsqueeze(0)
                elif key == "observation.state" and tensor.ndim == 1:
                    tensor = tensor.unsqueeze(0)
                obs_dict[key] = tensor
            else:
                obs_dict[key] = value
        
        deserialize_time = time.perf_counter() - deserialize_start
        
        # Run inference
        inference_start = time.perf_counter()
        with torch.inference_mode():
            action_chunk = _policy.predict_action_chunk(obs_dict)
        inference_time = time.perf_counter() - inference_start
        
        serialize_start = time.perf_counter()
        # Convert to numpy and remove batch dimension
        action_chunk_np = action_chunk.squeeze(0).cpu().numpy()
        
        # Serialize to binary format
        action_chunk_bytes = pickle.dumps(action_chunk_np, protocol=pickle.HIGHEST_PROTOCOL)
        serialize_time = time.perf_counter() - serialize_start
        
        total_time = time.perf_counter() - deserialize_start
        
        # Log detailed timing
        logger.info(
            f"Server binary inference breakdown: total={total_time:.3f}s, "
            f"deserialize={deserialize_time:.3f}s, inference={inference_time:.3f}s, "
            f"serialize={serialize_time:.3f}s"
        )
        
        # Return binary response
        from flask import Response
        return Response(
            action_chunk_bytes,
            mimetype="application/octet-stream",
            status=200
        )
    
    except Exception as e:
        logger.error(f"Error during binary prediction: {e}", exc_info=True)
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """Predict action chunk from observation.
    
    Supports both binary (pickle) and JSON formats for backward compatibility.
    
    Request body (binary format, recommended):
        {
            "observation_b64": "base64_encoded_pickle_data",
            "format": "pickle",
            "single_task": "task description"  # Optional
        }
    
    Request body (JSON format, legacy):
        {
            "observation": {
                "observation.images.*": [[C, H, W]],  # List of images as numpy arrays
                "observation.state": [state_dim],      # State vector
                "task": "task description"            # Task string
            },
            "single_task": "task description"         # Optional, overrides observation.task
        }
    
    Response (binary format):
        {
            "action_chunk_b64": "base64_encoded_pickle_data",
            "format": "pickle",
            "success": true
        }
    
    Response (JSON format, legacy):
        {
            "action_chunk": [[n_action_steps, action_dim]],  # Action chunk as numpy array
            "success": true
        }
    """
    if _policy is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    try:
        data = request.json
        use_binary = data.get("format") == "pickle" and "observation_b64" in data
        
        # Performance monitoring
        deserialize_start = time.perf_counter()
        
        if use_binary:
            # Binary format: decode base64 and unpickle
            observation_b64 = data.get("observation_b64")
            observation_bytes = base64.b64decode(observation_b64)
            observation_dict = pickle.loads(observation_bytes)
            single_task = data.get("single_task", observation_dict.get("task", ""))
            
            # Convert numpy arrays to torch tensors
            obs_dict = {}
            for key, value in observation_dict.items():
                if key == "task":
                    obs_dict[key] = value
                elif isinstance(value, np.ndarray):
                    # Convert numpy array to torch tensor and move to device
                    tensor = torch.from_numpy(value).to(_device)
                    # Add batch dimension if missing (for images: [C, H, W] -> [1, C, H, W])
                    if key.startswith("observation.images.") and tensor.ndim == 3:
                        tensor = tensor.unsqueeze(0)
                    elif key == "observation.state" and tensor.ndim == 1:
                        tensor = tensor.unsqueeze(0)
                    obs_dict[key] = tensor
                else:
                    obs_dict[key] = value
        else:
            # JSON format (legacy, for backward compatibility)
            observation = data.get("observation", {})
            single_task = data.get("single_task", observation.get("task", ""))
            
            # Convert lists to torch tensors
            obs_dict = {}
            for key, value in observation.items():
                if key == "task":
                    obs_dict[key] = value
                elif isinstance(value, list):
                    # Convert list to numpy array, then to torch tensor
                    arr = np.array(value, dtype=np.float32)
                    tensor = torch.from_numpy(arr).to(_device)
                    # Add batch dimension if missing
                    if key.startswith("observation.images.") and tensor.ndim == 3:
                        tensor = tensor.unsqueeze(0)
                    elif key == "observation.state" and tensor.ndim == 1:
                        tensor = tensor.unsqueeze(0)
                    obs_dict[key] = tensor
                else:
                    obs_dict[key] = value
        
        deserialize_time = time.perf_counter() - deserialize_start
        
        # The observation is already preprocessed by the client
        # (normalized, CHW format, batch dimension added)
        # So we can directly use it for inference
        
        inference_start = time.perf_counter()
        with torch.inference_mode():
            # Run inference directly with preprocessed observation
            action_chunk = _policy.predict_action_chunk(obs_dict)
        inference_time = time.perf_counter() - inference_start
        
        serialize_start = time.perf_counter()
        # Convert to numpy and remove batch dimension
        action_chunk_np = action_chunk.squeeze(0).cpu().numpy()
        
        if use_binary:
            # Binary format: pickle and base64 encode
            action_chunk_bytes = pickle.dumps(action_chunk_np, protocol=pickle.HIGHEST_PROTOCOL)
            action_chunk_b64 = base64.b64encode(action_chunk_bytes).decode('utf-8')
            serialize_time = time.perf_counter() - serialize_start
            
            total_time = time.perf_counter() - deserialize_start
            
            # Log detailed timing
            logger.info(
                f"Server inference breakdown: total={total_time:.3f}s, "
                f"deserialize={deserialize_time:.3f}s, inference={inference_time:.3f}s, "
                f"serialize={serialize_time:.3f}s"
            )
            return jsonify({
                "action_chunk_b64": action_chunk_b64,
                "format": "pickle",
                "success": True
            })
        else:
            # JSON format (legacy)
            action_chunk_list = action_chunk_np.tolist()
            serialize_time = time.perf_counter() - serialize_start
            
            total_time = time.perf_counter() - deserialize_start
            
            # Log detailed timing
            logger.info(
                f"Server inference breakdown: total={total_time:.3f}s, "
                f"deserialize={deserialize_time:.3f}s, inference={inference_time:.3f}s, "
                f"serialize={serialize_time:.3f}s"
            )
            return jsonify({
                "action_chunk": action_chunk_list,
                "success": True
            })
    
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/config", methods=["GET"])
def get_config():
    """Get model configuration."""
    if _policy is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    return jsonify({
        "n_action_steps": _policy_config.n_action_steps,
        "chunk_size": _policy_config.chunk_size,
        "max_action_dim": _policy_config.max_action_dim,
        "max_state_dim": _policy_config.max_state_dim,
        "image_features": {k: {"shape": list(v.shape)} for k, v in _policy_config.image_features.items()},
        "robot_type": _robot_type,
        "success": True
    })


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, exiting...")
    sys.exit(0)


def main():
    """Main entry point for the model server."""
    parser = argparse.ArgumentParser(description="LUNA Model Inference Server")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to inference config YAML file",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load model
    load_model(args.config)

    # Start server
    # Note: For multi-threaded Flask with torch.compile, we disable CUDA graphs
    # via environment variable to avoid thread-local storage issues
    logger.info(f"Starting model server on {args.host}:{args.port}")
    logger.info("Note: CUDA graphs are disabled for multi-threaded compatibility")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()

