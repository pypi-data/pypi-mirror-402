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
"""LUNA Robot Inference Module.

This module implements real-time robot control using trained VLA policies
with LUNA's asynchronous inference strategy. The key innovation is
future-state-aware prediction that overlaps inference with execution.

Key components:
- LUNAAsyncManager: Manages asynchronous action chunk execution
- run_loop: Core control loop for real-time robot operation
- run: Main entry point for inference

Usage:
    luna run examples/inference/async.yaml
"""

import logging
import signal
import time
from dataclasses import asdict
from pprint import pformat
from copy import copy
import numpy as np
import torch

from lerobot.configs import parser
from lerobot.configs.policies import PreTrainedConfig

# Import bi_piper_follower adapter early to ensure registration
# This must happen before config parsing
try:
    from luna.robots.bi_piper_follower_adapter import BiPIPERFollowerConfig  # noqa: F401
except ImportError:
    # Fallback to standard lerobot import if adapter not available
    try:
        from lerobot.robots.bi_piper_follower import BiPIPERFollowerConfig  # noqa: F401
    except ImportError:
        pass  # bi_piper_follower not available
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.robots import Robot, make_robot_from_config
from lerobot.utils.constants import OBS_IMAGES
from lerobot.utils.control_utils import (
    init_keyboard_listener,
    prepare_observation_for_inference,
)
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import get_safe_torch_device, init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

from luna.configs import RunConfig
from luna.policies.factory import get_policy_class


class LUNAAsyncManager:
    """Manages asynchronous action chunk execution for LUNA inference.

    This class implements the core LUNA async inference strategy:
    1. Execute actions from the current chunk while preparing the next
    2. Use future state awareness by conditioning on predicted end state
    3. Overlap inference with execution to hide latency

    The execution timeline looks like:

        Chunk N:     [action_0, action_1, ..., action_{n-overlap}, ..., action_{n-1}]
                                                    ^
                                                    |-- Start inference for Chunk N+1
                                                        (using predicted state at action_{n-1})
        Chunk N+1:   [action_0, action_1, ...]
                     ^
                     |-- Switch to new chunk when Chunk N completes

    Attributes:
        policy: The trained policy for action prediction.
        robot: The robot being controlled.
        single_task: task description for policies.
        n_action_steps: Number of actions per chunk.
        overlap_steps: Steps before chunk end to start next inference.
        current_chunk: Currently executing action chunk (numpy array).
        next_chunk: Pre-computed next chunk (torch tensor, pending transfer).
        chunk_index: Current position within the executing chunk.
        device: Torch device for inference.
    """
    
    def __init__(
        self,
        policy: PreTrainedPolicy,
        robot: Robot,
        single_task: str | None,
        overlap_steps: int,
    ):
        """Initialize the async manager.

        Args:
            policy: Trained policy for action prediction.
            robot: Robot instance to control.
            single_task: Task description string.
            overlap_steps: Number of steps before chunk end to start next inference.
                          Higher values give more time for inference but reduce
                          the accuracy of the prediction.
        """
        self.policy = policy
        self.robot = robot
        self.single_task = single_task
        self.n_action_steps = policy.config.n_action_steps
        self.overlap_steps = overlap_steps

        # Chunk state management
        self.current_chunk: np.ndarray | None = None  # Currently executing (on CPU)
        self.next_chunk: torch.Tensor | None = None   # Pre-computed (on GPU)
        self.chunk_index = 0  # Position within current chunk

        self.device = get_safe_torch_device(policy.config.device)

        # Validate configuration
        assert (
            self.n_action_steps >= self.overlap_steps
        ), "n_action_steps must be greater than or equal to overlap_steps"
        assert self.overlap_steps >= 0, "overlap_steps must be non-negative"

    def is_running(self) -> bool:
        """Check if the manager has any chunks to execute.
        
        Returns:
            True if there's a current or pending chunk, False otherwise.
        """
        return (self.current_chunk is not None) or (self.next_chunk is not None)

    def should_switch_chunk(self) -> bool:
        """Check if it's time to switch to the next chunk.
        
        Returns:
            True if at the beginning of a new chunk cycle (index == 0).
        """
        return self.chunk_index == 0

    def should_launch_next_inference(self) -> bool:
        """Check if it's time to start computing the next chunk.
        
        The next inference is launched `overlap_steps` before the current
        chunk ends, allowing inference to happen in parallel with execution.
        
        Returns:
            True if at the trigger point for next inference.
        """
        return self.chunk_index == self.n_action_steps - self.overlap_steps

    def should_fetch_observation(self) -> bool:
        """Check if a fresh observation is needed.
        
        Observations are fetched:
        1. At startup (not running yet)
        2. When launching next inference (need current state)
        
        Returns:
            True if observation should be captured this step.
        """
        return (not self.is_running()) or self.should_launch_next_inference()

    def get_current_action(self) -> dict[str, float]:
        """Extract the current action from the executing chunk.
        
        Returns:
            Dictionary mapping action feature names to values.
            
        Raises:
            RuntimeError: If no chunk is currently executing.
        """
        if self.current_chunk is None:
            raise RuntimeError("No chunk is currently executing")

        # Get action values at current index and map to feature names
        action_values = self.current_chunk[self.chunk_index]
        action = {key: action_values[i].item() for i, key in enumerate(self.robot.action_features)}
        return action

    def launch_next_inference(self, observation: dict[str, np.ndarray]) -> torch.Tensor:
        """Compute the next action chunk using the policy.
        
        Implements future state awareness: if we have a current chunk,
        use its final action as the observation state (predicting where
        the robot will be when this chunk finishes).
        
        Args:
            observation: Current observation dictionary.
            
        Returns:
            Predicted action chunk as a torch tensor [n_action_steps, action_dim].
        """
        observation = copy(observation)
        
        # Future state awareness: use future state instead of current state
        last_action = self.current_chunk[self.n_action_steps - 1] if self.current_chunk is not None else None
        if last_action is not None:
            observation["observation.state"] = last_action

        with torch.inference_mode():
            # Prepare observation: convert images to CHW format, normalize, add batch dim
            observation = prepare_observation_for_inference(
                observation,
                self.device,
                self.single_task,
                self.robot.robot_type,
            )

            # Run policy inference to get action chunk
            action_chunk = self.policy.predict_action_chunk(observation)

        # Remove batch dimension
        return action_chunk.squeeze(0)

    def get_action(self, observation_frame: dict) -> dict[str, float]:
        """Get the next action to execute.
        
        This is the main interface called each control loop iteration.
        It manages chunk transitions and triggers async inference.
        
        Args:
            observation_frame: Current observation in dataset format.
            
        Returns:
            Action dictionary for the robot to execute.
        """
        # Bootstrap: compute first chunk synchronously
        if not self.is_running():
            chunk_tensor = self.launch_next_inference(observation_frame)
            self.current_chunk = chunk_tensor.cpu().numpy()
            # Debug: pause before executing first chunk
            # print(self.current_chunk)
            # input("Press Enter to start executing this chunk...")
        # Chunk transition: move pre-computed next chunk to current
        elif self.should_switch_chunk():
            if self.next_chunk is None:
                # Next chunk not ready - this causes blocking!
                # This happens when inference takes longer than overlap_steps execution time
                logging.warning(
                    f"Next chunk not ready at chunk transition! "
                    f"This will cause blocking. Consider increasing inference_overlap_steps "
                    f"(current: {self.overlap_steps}, n_action_steps: {self.n_action_steps})"
                )
                # Fallback: compute synchronously (blocks execution)
                if observation_frame is not None:
                    chunk_tensor = self.launch_next_inference(observation_frame)
                    self.current_chunk = chunk_tensor.cpu().numpy()
                else:
                    # No observation available, use zero actions as fallback
                    logging.error("No observation available for fallback inference!")
                    self.current_chunk = np.zeros((self.n_action_steps, len(self.robot.action_features)))
            else:
                # Next chunk is ready - smooth transition
                self.current_chunk = self.next_chunk.cpu().numpy()
            self.next_chunk = None
            # Debug: pause before executing new chunk
            # if self.current_chunk is not None:
            #     print(self.current_chunk)
            #     input("Press Enter to start executing this chunk...")

        # Async inference: start computing next chunk in advance
        if self.should_launch_next_inference():
            # This is the async inference point - should complete before chunk transition
            inference_start = time.perf_counter()
            self.next_chunk = self.launch_next_inference(observation_frame)
            inference_time = time.perf_counter() - inference_start
            # Log if inference is taking too long
            steps_remaining = self.overlap_steps
            time_available = steps_remaining / self.robot.observation_features.get('fps', 30) if hasattr(self.robot, 'observation_features') else steps_remaining / 30
            if inference_time > time_available:
                logging.warning(
                    f"Inference took {inference_time:.3f}s, but only {time_available:.3f}s available "
                    f"({steps_remaining} steps remaining). This may cause blocking at chunk transition."
                )

        # Get action at current index
        action = self.get_current_action()

        # Advance index and handle chunk completion
        self.chunk_index = (self.chunk_index + 1) % self.n_action_steps
        self.current_chunk = None if self.chunk_index == 0 else self.current_chunk

        return action


def validate_robot_cameras(robot: Robot, policy_config: PreTrainedConfig):
    """Validate that robot cameras match policy expectations.
    
    Ensures the robot's camera configuration exactly matches what the
    policy was trained with. Mismatches will cause inference failures.
    
    Args:
        robot: Connected robot instance.
        policy_config: Configuration of the pretrained policy.
        
    Raises:
        ValueError: If camera names don't match between robot and policy.
    """
    # Build set of robot camera feature names (with observation.images prefix)
    robot_camera_names = set(robot.cameras.keys())
    robot_image_features = {f"{OBS_IMAGES}.{name}" for name in robot_camera_names}

    # Get policy's expected image features
    policy_image_features = policy_config.image_features
    if not isinstance(policy_image_features, dict):
        raise ValueError(
            f"Policy image_features must be a dict, got {type(policy_image_features)}: {policy_image_features}"
        )

    policy_camera_features = set(policy_image_features.keys())

    # Strict match required
    if robot_image_features != policy_camera_features:
        raise ValueError(
            "Robot camera names must exactly match policy image feature names!\n"
            f"Robot cameras (with prefix): {sorted(robot_image_features)}\n"
            f"Policy image features: {sorted(policy_camera_features)}\n"
            "Please ensure camera configuration matches the trained model."
        )


@torch.inference_mode()
def run_loop(
    robot: Robot,
    events: dict,
    fps: int,
    dataset_features: dict[str, dict],
    policy: PreTrainedPolicy,
    single_task: str | None,
    action_quant_ratio: int = 1,
    inference_overlap_steps: int = 0,
    display_data: bool = False,
    control_time_s: int | float = 60,
):
    """Core control loop for real-time robot operation.
    
    Runs the policy on the robot at the specified frequency, managing
    observation capture, action inference, and command execution.
    
    Args:
        robot: Connected robot instance.
        events: Event dictionary for keyboard control (exit_early flag).
        fps: Target control frequency in Hz.
        dataset_features: Feature definitions for observation/action conversion.
        policy: Loaded policy for action prediction.
        single_task: Task description for policies.
        action_quant_ratio: Action quantization ratio.
        inference_overlap_steps: Steps of overlap between chunks.
        display_data: Whether to log data to Rerun for visualization.
        control_time_s: Total runtime in seconds.
    """
    # Reset policy state (clears any cached observations)
    if policy is not None:
        policy.reset()

    # Initialize async manager for LUNA inference
    # Scale overlap_steps by action_quant_ratio to match effective step count
    effective_overlap_steps = inference_overlap_steps * action_quant_ratio
    logging.info(f"Effective overlap_steps: {effective_overlap_steps} (inference_overlap_steps={inference_overlap_steps} * action_quant_ratio={action_quant_ratio})")
    async_manager = LUNAAsyncManager(
        policy=policy,
        robot=robot,
        single_task=single_task,
        overlap_steps=effective_overlap_steps,
    )

    step_count = 0
    observation_frame = None
    start_time = time.perf_counter()
    
    logging.info(f"Starting control loop (fps={fps}, control_time_s={control_time_s})")

    # Main control loop
    while time.perf_counter() - start_time < control_time_s:
        loop_start = time.perf_counter()

        # Check for keyboard interrupt (Escape key)
        if events["exit_early"]:
            events["exit_early"] = False
            break

        # Fetch observation only when needed (reduces camera latency)
        if async_manager.should_fetch_observation():
            obs_start = time.perf_counter()
            observation = robot.get_observation()
            obs_time = time.perf_counter() - obs_start
            if obs_time > 0.05:  # Log if observation takes > 50ms
                logging.debug(f"Observation fetch took {obs_time*1000:.1f}ms")
            # Debug: uncomment to print observation
            # print(observation)
            observation_frame = build_dataset_frame(dataset_features, observation, prefix="observation")
        else:
            observation = None

        # Ensure observation_frame is available when needed
        if observation_frame is None:
            # This should not happen, but handle it gracefully
            logging.warning("observation_frame is None, fetching new observation")
            observation = robot.get_observation()
            observation_frame = build_dataset_frame(dataset_features, observation, prefix="observation")

        # Get action from async manager (handles chunk management internally)
        action = async_manager.get_action(observation_frame)

        # Send action based on quantization ratio
        if (step_count + 1) % action_quant_ratio == 0:
            try:
                robot.send_action(action)
                if step_count % (fps * 5) == 0:  # Log every 5 seconds
                    logging.debug(f"Sent action at step {step_count}")
            except Exception as e:
                logging.error(f"Error sending action at step {step_count}: {e}", exc_info=True)
                raise

            # Optional: log to Rerun for debugging/visualization
            if display_data and observation is not None:
                log_rerun_data(observation, action)

        # Maintain target frequency (always, not just when sending action)
        # This ensures consistent loop timing regardless of action_quant_ratio
        elapsed = time.perf_counter() - loop_start
        busy_wait(1 / fps - elapsed)

        step_count += 1


def load_and_compile_policy(cfg: RunConfig) -> PreTrainedPolicy:
    """Load pretrained policy from checkpoint.
    
    Args:
        cfg: Run configuration with policy path and settings.
        
    Returns:
        Loaded policy ready for inference.
    """
    logging.info(f"Loading policy from: {cfg.policy.pretrained_path}")
    policy_cls = get_policy_class(cfg.policy.type)
    policy: PreTrainedPolicy = policy_cls.from_pretrained(
        pretrained_name_or_path=cfg.policy.pretrained_path,
        config=cfg.policy,
    )
    logging.info("Policy weights loaded.")

    if cfg.policy.compile_model:
        logging.info(f"Compiling model with mode: {cfg.policy.compile_mode} (this may take 10-30 minutes)...")
        warmup_compiled_policy(policy, cfg.single_task)
        logging.info("Model compilation and warmup complete.")

    return policy


def warmup_compiled_policy(
    policy: PreTrainedPolicy,
    single_task: str | None,
    warmup_steps: int = 3,
):
    """Warm up compiled policy to trigger torch.compile.
    
    Running a few inference passes before actual control ensures that
    torch.compile has finished optimizing the model, avoiding latency
    spikes during real operation.
    
    Args:
        policy: Compiled policy to warm up.
        robot: Robot instance (unused, kept for API compatibility).
        single_task: Optional task string.
        warmup_steps: Number of warmup iterations.
    """
    logging.info("Warming up compiled policy...")
    
    device = get_safe_torch_device(policy.config.device)
    
    # Create dummy observation matching policy's expected input shape
    # Format: [B, C, H, W] for images, [B, state_dim] for state
    dummy_obs = {}
    
    # Add dummy image observations with correct shape [B, C, H, W]
    for img_key, img_feature in policy.config.image_features.items():
        channels, height, width = img_feature.shape
        dummy_obs[img_key] = torch.zeros(
            (1, channels, height, width),
            dtype=torch.float32,
            device=device,
        )
    
    # Add dummy state observation with correct shape [B, state_dim]
    # Get state dimension from policy config's input_features
    if "observation.state" in policy.config.input_features:
        state_dim = policy.config.input_features["observation.state"].shape[0]
        dummy_obs["observation.state"] = torch.zeros(
            (1, state_dim),
            dtype=torch.float32,
            device=device,
        )
    
    # Add task string
    dummy_obs["task"] = single_task if single_task is not None else ""
    
    # Run warmup iterations to complete compilation
    # Use predict_action_chunk which includes all necessary preprocessing
    warmup_start = time.perf_counter()
    for i in range(warmup_steps):
        with torch.inference_mode():
            _ = policy.predict_action_chunk(dummy_obs)
    
    warmup_time = time.perf_counter() - warmup_start
    logging.info(f"Warmup complete ({warmup_steps} steps in {warmup_time:.2f}s)")


def build_dataset_features(robot: Robot) -> dict[str, dict]:
    """Build dataset-style feature definitions from robot config.
    
    Converts robot's hardware feature definitions to the format expected
    by LeRobot's dataset utilities for observation/action frame building.
    
    Args:
        robot: Robot instance with observation and action features.
        
    Returns:
        Combined dictionary of action and observation feature definitions.
    """
    action_features = hw_to_dataset_features(robot.action_features, "action", use_video=True)
    obs_features = hw_to_dataset_features(robot.observation_features, "observation", use_video=True)
    
    # Ensure observation.state is included in dataset_features
    # This allows build_dataset_frame() to properly process the state vector
    # State dimension should match action dimension
    state_dim = len(robot.action_features)
    if "observation.state" not in obs_features:
        obs_features["observation.state"] = {
            "shape": (state_dim,),
            "dtype": "float32",
        }
    
    return {**action_features, **obs_features}


def move_to_zero_position(robot: Robot) -> None:
    """Move robot to zero/home position.
    
    For joint-controlled robots: moves all joints to 0.
    For end-effector pose controlled robots: moves to home position.
    
    Args:
        robot: Robot instance to move to zero/home position.
    """
    try:
        logging.info("Moving robot to zero/home position...")
        
        # Check if robot has go_home method (preferred for end-effector pose control)
        if hasattr(robot, 'go_home') and callable(robot.go_home):
            robot.go_home()
            logging.info("Robot moved to home position using go_home().")
        # Check if robot has get_home_action method (for end-effector pose control)
        elif hasattr(robot, 'get_home_action') and callable(robot.get_home_action):
            home_action = robot.get_home_action()
            # Send home action multiple times to ensure smooth movement
            for _ in range(10):
                robot.send_action(home_action)
                time.sleep(0.1)
            logging.info("Robot moved to home position using home action.")
        else:
            # Fallback: use zero action (works for joint-controlled robots)
            logging.info("Using zero action (fallback for joint-controlled robots)...")
        zero_action = {key: 0.0 for key in robot.action_features}
        
        # Send zero action multiple times to ensure smooth movement
        for _ in range(10):
            robot.send_action(zero_action)
            time.sleep(0.1)
        
        logging.info("Robot moved to zero position.")
    except Exception as e:
        logging.error(f"Error moving robot to zero/home position: {e}")


def setup_signal_handlers(robot: Robot) -> None:
    """Setup signal handlers for graceful shutdown.
    
    Args:
        robot: Robot instance to move to zero position on interrupt.
    """
    def signal_handler(signum, frame):
        """Handle SIGINT (Ctrl+C) and SIGTERM signals."""
        logging.info(f"Received signal {signum}, moving robot to zero position...")
        try:
            move_to_zero_position(robot)
        except Exception as e:
            logging.error(f"Error in signal handler: {e}")
        finally:
            logging.info("Exiting...")
            import sys
            sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


@parser.wrap()
def run(cfg: RunConfig):
    """Main entry point for LUNA robot inference.

    Loads a pretrained policy and runs it on a connected robot using
    LUNA's async inference strategy for real-time control.

    Args:
        cfg: Run configuration parsed from YAML and CLI arguments.
    """
    init_logging()
    logging.info(pformat(asdict(cfg)))

    # Validate task description is provided (not placeholder)
    if cfg.single_task is None or cfg.single_task == "<task description>":
        raise ValueError(
            "Please provide a language prompt (task description) in the config file.\n"
            "The 'single_task' field cannot be empty or use the placeholder '<task description>'.\n"
            "Example: single_task: 'pick up the cube and place it in the box'"
        )

    # Initialize Rerun visualization if requested
    if cfg.display_data:
        init_rerun(session_name="luna_run")

    # Setup robot and validate camera configuration
    logging.info("Creating robot instance...")
    robot = make_robot_from_config(cfg.robot)
    logging.info("Robot instance created.")
    
    # Load policy: either from server or locally
    if cfg.model_server_url:
        # Server mode: use remote policy client
        logging.info(f"Using model server at: {cfg.model_server_url}")
        from luna.policy_client import PolicyClient
        policy = PolicyClient(server_url=cfg.model_server_url)
        # Load config from server for validation
        original_policy_config = policy.config
    else:
        # Local mode: load policy directly
        logging.info("Loading policy configuration...")
        original_policy_config = PreTrainedConfig.from_pretrained(cfg.policy.pretrained_path)
        logging.info("Loading and compiling policy (this may take several minutes)...")
        policy = load_and_compile_policy(cfg)
        logging.info("Policy loaded and compiled.")
    
    validate_robot_cameras(robot, original_policy_config)
    dataset_features = build_dataset_features(robot)

    # Connect to robot and setup keyboard listener for manual control
    robot.connect()
    listener, events = init_keyboard_listener()
    
    # Setup signal handlers for graceful shutdown (Ctrl+C)
    setup_signal_handlers(robot)

    log_say("Starting LUNA run", cfg.play_sounds, blocking=True)

    try:
        # Run the main control loop
        run_loop(
            robot=robot,
            events=events,
            fps=cfg.fps,
            dataset_features=dataset_features,
            policy=policy,
            single_task=cfg.single_task,
            action_quant_ratio=cfg.action_quant_ratio,
            inference_overlap_steps=cfg.inference_overlap_steps,
            display_data=cfg.display_data,
            control_time_s=cfg.control_time_s,
        )
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt explicitly (though signal handler should catch it)
        logging.info("KeyboardInterrupt received, moving robot to zero position...")
        move_to_zero_position(robot)
    finally:
        # Cleanup: disconnect robot and stop keyboard listener
        log_say("Stopping LUNA run", cfg.play_sounds, blocking=True)
        try:
            move_to_zero_position(robot)
        except Exception as e:
            logging.error(f"Error moving to zero position in finally block: {e}")
        robot.disconnect()
        if listener is not None:
            listener.stop()


def main():
    """CLI entry point."""
    run()


if __name__ == "__main__":
    main()
