#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
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

import time
from functools import cached_property
from typing import Any

import numpy as np
from lerobot.robots.piper_follower import PIPERFollower
from lerobot.robots.piper_follower.config_piper_follower import PIPERFollowerConfig

from ..robot import Robot
from .config_bi_piper_follower import BiPIPERFollowerConfig
# from luna.cam_rs import CameraWrapper
from superbot.sensors.cams.cam_rs import CameraWrapper
from loguru import logger


class BiPIPERFollower(Robot):
    """
    Bimanual Piper follower arms using Piper SDK over CAN.
    This bimanual robot combines two PIPERFollower instances for dual-arm control.
    """

    config_class = BiPIPERFollowerConfig
    name = "bi_piper_follower"

    def __init__(self, config: BiPIPERFollowerConfig):
        super().__init__(config)
        self.config = config
        # Camera names are taken from the config and used to build the observation dict.
        # We keep using the config only for metadata (name, width, height, fps),
        # while image acquisition is delegated to LUNA's CameraWrapper which can
        # use pyrealsense2 (RealSense) or OpenCV under the hood.
        self._camera_names = list(self.config.cameras.keys())

        # Following dual_piper.py: minimal config with only can_name
        left_arm_config = PIPERFollowerConfig(
            id=f"{config.id}_left" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=None,  # Piper uses CAN, not serial port
            can_name=config.left_arm_can_name,
            max_relative_target=config.left_arm_max_relative_target,
            cameras={},
        )

        right_arm_config = PIPERFollowerConfig(
            id=f"{config.id}_right" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=None,  # Piper uses CAN, not serial port
            can_name=config.right_arm_can_name,
            max_relative_target=config.right_arm_max_relative_target,
            cameras={},
        )

        self.left_arm = PIPERFollower(left_arm_config)
        self.right_arm = PIPERFollower(right_arm_config)

        # start position
        self.go_home()

        # ------------------------------------------------------------------
        # Camera setup using CameraWrapper (supports pyrealsense2 + OpenCV)
        # ------------------------------------------------------------------
        # We interpret each camera's `index_or_path` field as a device id for
        # CameraWrapper. Width/height/fps are taken from the first camera and
        # are assumed to be identical across cameras (as in the default config).
        if not self._camera_names:
            logger.warning("No cameras configured for BiPIPERFollower")
            self.camera_wrapper = CameraWrapper(
                devices=[], width=640, height=480, fps=30
            )
        else:
            devices = []
            for name in self._camera_names:
                cam_cfg = self.config.cameras[name]
                # `index_or_path` comes from OpenCVCameraConfig; we reuse it as device id.
                if not hasattr(cam_cfg, "index_or_path"):
                    raise AttributeError(
                        f"Camera config for '{name}' must define 'index_or_path' to be used with CameraWrapper"
                    )
                devices.append(getattr(cam_cfg, "index_or_path"))

            first_cam_cfg = self.config.cameras[self._camera_names[0]]
            width = getattr(first_cam_cfg, "width", 640)
            height = getattr(first_cam_cfg, "height", 480)
            fps = getattr(first_cam_cfg, "fps", 30)

            # Assume all configured cameras are RealSense by default; if you want
            # a mix of RealSense and OpenCV, you can reduce `num_realsense` and
            # keep the remaining as OpenCV indices.
            num_realsense = len(devices)

            self.camera_wrapper = CameraWrapper(
                devices=devices,
                width=width,
                height=height,
                fps=fps,
                num_realsense=num_realsense,
            )

        # Keep a placeholder dict for compatibility with existing utilities.
        # Only the keys are used elsewhere (e.g. for validation); the actual
        # image acquisition happens through `camera_wrapper`.
        self.cameras: dict[str, Any] = {name: None for name in self._camera_names}

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"left_{motor}.pos": float for motor in self.left_arm.bus.motors} | {
            f"right_{motor}.pos": float for motor in self.right_arm.bus.motors
        }

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self._camera_names
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        # Arms must be connected
        arms_ok = self.left_arm.bus.is_connected and self.right_arm.bus.is_connected
        # CameraWrapper opens cameras in its constructor; we simply check that
        # we managed to open the expected number of devices.
        cameras_ok = len(self.camera_wrapper.cameras) == len(self._camera_names)
        return arms_ok and cameras_ok

    def connect(self, calibrate: bool = True) -> None:
        self.left_arm.connect(calibrate)
        self.right_arm.connect(calibrate)
        # CameraWrapper opens cameras on construction; nothing to do here.

    @property
    def is_calibrated(self) -> bool:
        return self.left_arm.is_calibrated and self.right_arm.is_calibrated

    def calibrate(self) -> None:
        self.left_arm.calibrate()
        self.right_arm.calibrate()

    def configure(self) -> None:
        self.left_arm.configure()
        self.right_arm.configure()

    def setup_motors(self) -> None:
        self.left_arm.setup_motors()
        self.right_arm.setup_motors()

    def get_observation(self) -> dict[str, Any]:
        obs_dict = {}

        # Add "left_" prefix
        left_obs = self.left_arm.get_observation()
        obs_dict.update({f"left_{key}": value for key, value in left_obs.items()})

        # Add "right_" prefix
        right_obs = self.right_arm.get_observation()
        obs_dict.update({f"right_{key}": value for key, value in right_obs.items()})

        # Build state vector matching training data format: [14] = [left_joint_1...left_joint_6, left_gripper, right_joint_1...right_joint_6, right_gripper]
        # Order must match training data: left arm first (joint_1...joint_6, gripper), then right arm (joint_1...joint_6, gripper)
        state_values = []

        # Left arm: joint_1 to joint_6, then gripper (order matches self.left_arm.bus.motors)
        for motor in self.left_arm.bus.motors:
            key = f"left_{motor}.pos"
            state_values.append(obs_dict[key])

        # Right arm: joint_1 to joint_6, then gripper (order matches self.right_arm.bus.motors)
        for motor in self.right_arm.bus.motors:
            key = f"right_{motor}.pos"
            state_values.append(obs_dict[key])

        # Convert to numpy array matching training data format: shape [14], dtype float32
        obs_dict["observation.state"] = np.array(state_values, dtype=np.float32)

        # Read all camera images in a single call to CameraWrapper, then
        # distribute them to the observation dict using the configured names.
        start = time.perf_counter()
        images = self.camera_wrapper.get_images()
        dt_ms = (time.perf_counter() - start) * 1e3

        if not images:
            logger.error(
                "CameraWrapper returned no images, using dummy frames for all cameras"
            )
            # CameraWrapper already returns dummy images when no hardware is available,
            # but keep a safeguard in case of unexpected failures.
            for cam_key in self._camera_names:
                h = getattr(self.config.cameras[cam_key], "height", 480)
                w = getattr(self.config.cameras[cam_key], "width", 640)
                dummy_img = np.zeros((h, w, 3), dtype=np.uint8)
                dummy_img[:, :, :] = 128
                obs_dict[cam_key] = dummy_img
        else:
            if len(images) != len(self._camera_names):
                logger.warning(
                    "CameraWrapper returned %d images for %d configured cameras; "
                    "reusing images to fill all camera slots",
                    len(images),
                    len(self._camera_names),
                )

            # Map images to camera names; if there are fewer images than names,
            # reuse the last available image to ensure every expected camera key
            # is present in the observation dict (required by the policy).
            last_img = images[-1]
            for idx, cam_key in enumerate(self._camera_names):
                img = images[idx] if idx < len(images) else last_img
                obs_dict[cam_key] = img

        logger.debug(f"read {len(images)} cameras in {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        # Remove "left_" prefix
        left_action = {
            key.removeprefix("left_"): value
            for key, value in action.items()
            if key.startswith("left_")
        }
        # Remove "right_" prefix
        right_action = {
            key.removeprefix("right_"): value
            for key, value in action.items()
            if key.startswith("right_")
        }

        send_action_left = self.left_arm.send_action(left_action)
        send_action_right = self.right_arm.send_action(right_action)

        # Add prefixes back
        prefixed_send_action_left = {
            f"left_{key}": value for key, value in send_action_left.items()
        }
        prefixed_send_action_right = {
            f"right_{key}": value for key, value in send_action_right.items()
        }

        return {**prefixed_send_action_left, **prefixed_send_action_right}

    def disconnect(self):
        self.left_arm.disconnect()
        self.right_arm.disconnect()

        # Release all camera resources held by CameraWrapper
        self.camera_wrapper.release()

    def go_home(self):
        """Move the robot to its home position."""
        self.left_arm.go_home()
        self.right_arm.go_home()
