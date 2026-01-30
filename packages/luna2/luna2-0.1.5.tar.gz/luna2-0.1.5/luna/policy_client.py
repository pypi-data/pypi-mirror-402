#!/usr/bin/env python
"""Policy Client for LUNA Model Server.

This module provides a client interface that mimics PreTrainedPolicy,
but forwards inference requests to a remote model server.

Usage:
    from luna.policy_client import PolicyClient

    client = PolicyClient(server_url="http://localhost:8000")
    action_chunk = client.predict_action_chunk(observation)
"""

import logging
import pickle
from typing import Any

import numpy as np
import requests
import torch
from torch import Tensor

from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.pretrained import PreTrainedPolicy

logger = logging.getLogger(__name__)


class PolicyClient(PreTrainedPolicy):
    """Client proxy for remote policy server.
    
    This class implements the same interface as PreTrainedPolicy,
    but forwards inference requests to a remote server.
    
    Attributes:
        server_url: Base URL of the model server (e.g., "http://localhost:8000")
        config: Policy configuration (loaded from server)
        timeout: Request timeout in seconds
    """
    
    # Required class attributes for PreTrainedPolicy subclass
    config_class = PreTrainedConfig
    name = "policy_client"
    
    def __init__(
        self,
        server_url: str,
        config: PreTrainedConfig | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the policy client.
        
        Args:
            server_url: Base URL of the model server.
            config: Optional policy configuration. If None, will be loaded from server.
            timeout: Request timeout in seconds.
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        
        # Load config from server if not provided
        if config is None:
            config = self._load_config_from_server()
        
        # Initialize base class with minimal config
        super().__init__(config)
        self.config = config
        
        # Verify server is available
        self._check_server_health()
    
    def _check_server_health(self) -> None:
        """Check if the server is available and model is loaded."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("model_loaded", False):
                raise RuntimeError("Server is running but model is not loaded")
            
            logger.info("Server health check passed")
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to connect to model server at {self.server_url}: {e}")
    
    def _load_config_from_server(self) -> PreTrainedConfig:
        """Load policy configuration from server."""
        try:
            response = requests.get(f"{self.server_url}/config", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Create a minimal config from server response
            # This is a simplified version - in practice, you might want to
            # store the full config on the server
            from luna.policies.pi05.configuration_pi05 import PI05Config
            
            config = PI05Config()
            config.n_action_steps = data.get("n_action_steps", 50)
            config.chunk_size = data.get("chunk_size", 50)
            config.max_action_dim = data.get("max_action_dim", 32)
            config.max_state_dim = data.get("max_state_dim", 32)
            
            # Reconstruct image features
            image_features = data.get("image_features", {})
            from lerobot.configs.types import FeatureType, PolicyFeature
            config.input_features = {}
            for key, feat_data in image_features.items():
                config.input_features[key] = PolicyFeature(
                    type=FeatureType.VISUAL,
                    shape=tuple(feat_data["shape"]),
                )
            
            return config
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to load config from server: {e}")
    
    @torch.no_grad()
    def predict_action_chunk(self, batch: dict[str, Tensor], noise: Tensor | None = None) -> Tensor:
        """Predict action chunk by forwarding request to server.
        
        Args:
            batch: Input batch with images, state, task.
            noise: Optional noise (ignored in client mode).
            
        Returns:
            Action chunk [B, n_action_steps, action_dim] as torch tensor.
        """
        import time
        
        total_start = time.perf_counter()
        
        # Convert torch tensors to numpy arrays for binary serialization
        serialize_start = time.perf_counter()
        observation_dict = {}
        single_task = None
        
        for key, value in batch.items():
            if key == "task":
                # Handle task string
                if isinstance(value, list) and len(value) > 0:
                    single_task = value[0] if isinstance(value[0], str) else str(value[0])
                elif isinstance(value, str):
                    single_task = value
                observation_dict[key] = single_task if single_task else ""
            elif isinstance(value, torch.Tensor):
                # Convert tensor to numpy array (keep as numpy, don't convert to list)
                arr = value.cpu().numpy()
                # Remove batch dimension if present (batch size = 1)
                if arr.ndim >= 1 and arr.shape[0] == 1:
                    arr = arr[0]
                observation_dict[key] = arr
            elif isinstance(value, np.ndarray):
                # Already numpy array, remove batch dim if needed
                if value.ndim >= 1 and value.shape[0] == 1:
                    observation_dict[key] = value[0]
                else:
                    observation_dict[key] = value
            else:
                observation_dict[key] = value
        
        # Serialize to binary format using pickle (much faster than JSON for numpy arrays)
        # Include single_task in the observation dict for transmission
        if single_task:
            observation_dict["_single_task"] = single_task
        
        observation_bytes = pickle.dumps(observation_dict, protocol=pickle.HIGHEST_PROTOCOL)
        
        serialize_time = time.perf_counter() - serialize_start
        
        # Send binary request directly (no JSON, no base64 encoding)
        try:
            network_start = time.perf_counter()
            response = requests.post(
                f"{self.server_url}/predict_binary",
                data=observation_bytes,
                headers={"Content-Type": "application/octet-stream"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            network_time = time.perf_counter() - network_start
            
            deserialize_start = time.perf_counter()
            
            # Check if response is binary or JSON (for error handling)
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                # Error response in JSON format
                data = response.json()
                raise RuntimeError(f"Server returned error: {data.get('error', 'Unknown error')}")
            
            # Binary response: directly unpickle
            action_chunk_bytes = response.content
            action_chunk_np = pickle.loads(action_chunk_bytes)
            
            # Convert to torch tensor
            action_chunk = torch.from_numpy(action_chunk_np)
            
            # Add batch dimension if needed
            if action_chunk.ndim == 2:
                action_chunk = action_chunk.unsqueeze(0)
            
            deserialize_time = time.perf_counter() - deserialize_start
            total_time = time.perf_counter() - total_start
            
            # Log performance breakdown if total time is significant
            if total_time > 0.1:  # Log if total time > 100ms
                logger.warning(
                    f"Client inference breakdown: total={total_time:.3f}s, "
                    f"serialize={serialize_time:.3f}s, network={network_time:.3f}s, "
                    f"deserialize={deserialize_time:.3f}s"
                )
            
            return action_chunk
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get prediction from server: {e}")
    
    def reset(self) -> None:
        """Reset policy state (no-op for client)."""
        pass
    
    def get_optim_params(self):
        """Get optimizer parameters (not applicable for client)."""
        raise NotImplementedError("PolicyClient does not support training")
    
    def to(self, device):
        """Move to device (no-op for client, model is on server)."""
        return self
    
    def eval(self):
        """Set to eval mode (no-op for client)."""
        return self
    
    def train(self, mode: bool = True):
        """Set to train mode (not applicable for client)."""
        raise NotImplementedError("PolicyClient does not support training")
    
    @torch.no_grad()
    def select_action(self, batch: dict[str, Tensor], noise: Tensor | None = None) -> Tensor:
        """Select single action using action chunking.
        
        For client mode, we get the first action from the predicted chunk.
        
        Args:
            batch: Input batch with images, state, task.
            noise: Optional noise (ignored in client mode).
            
        Returns:
            Single action [action_dim] as torch tensor.
        """
        # Get action chunk from server
        action_chunk = self.predict_action_chunk(batch, noise=noise)
        
        # Return first action from chunk
        # action_chunk shape: [B, n_action_steps, action_dim]
        # Return shape: [action_dim] (remove batch and step dimensions)
        return action_chunk[0, 0, :]
    
    def forward(self, batch: dict[str, Tensor], noise=None, time=None) -> tuple[Tensor, dict[str, Tensor]]:
        """Training forward pass (not supported in client mode).
        
        Args:
            batch: Training batch.
            noise: Optional noise.
            time: Optional time.
            
        Returns:
            Tuple of (loss, metrics dict).
            
        Raises:
            NotImplementedError: Client mode does not support training.
        """
        raise NotImplementedError(
            "PolicyClient does not support training. "
            "Training must be done with a local policy instance."
        )

