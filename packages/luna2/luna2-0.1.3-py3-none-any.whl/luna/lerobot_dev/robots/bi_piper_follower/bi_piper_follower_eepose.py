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
from scipy.spatial.transform import Rotation as R
from loguru import logger

from ..robot import Robot
from .config_bi_piper_follower_eepose import BiPIPERFollowerEeposeConfig
from superbot.sensors.cams.cam_rs import CameraWrapper
from luna.dual_piper import DualPiperRobot
from superbot.utils.rotation import rotation_6d_to_matrix, eef_6d_new_reg


# 6D相关函数已从 luna.rotation 导入


def abs_6d_2_abs_euler_with_validation(action: np.ndarray) -> np.ndarray:
    """
    将20维6D位姿动作转换为14维Euler角度动作（带错误处理）
    
    这是 abs_6d_2_abs_euler 的包装函数，添加了旋转矩阵有效性验证。
    
    输入格式: [left_xyz(3), left_6d(6), left_gripper(1), right_xyz(3), right_6d(6), right_gripper(1)]
    输出格式: [left_xyz(3), left_euler(3), left_gripper(1), right_xyz(3), right_euler(3), right_gripper(1)]
    """
    # Left arm
    left_xyz = action[0:3]
    left_6d = action[3:9]
    left_grip = action[9]

    # Right arm
    right_xyz = action[10:13]
    right_6d = action[13:19]
    right_grip = action[19]

    # 6D to Euler with validation
    try:
        left_matrix = rotation_6d_to_matrix(left_6d)
        right_matrix = rotation_6d_to_matrix(right_6d)
        
        # 验证旋转矩阵的有效性
        left_det = np.linalg.det(left_matrix)
        right_det = np.linalg.det(right_matrix)
        
        # 如果行列式接近0或为负，使用单位矩阵
        if abs(left_det) < 0.5 or left_det < 0:
            logger.debug(f"Left rotation matrix invalid (det={left_det}), using identity")
            left_matrix = np.eye(3)
        
        if abs(right_det) < 0.5 or right_det < 0:
            logger.debug(f"Right rotation matrix invalid (det={right_det}), using identity")
            right_matrix = np.eye(3)
        
        left_euler = R.from_matrix(left_matrix).as_euler('xyz', degrees=False)
        right_euler = R.from_matrix(right_matrix).as_euler('xyz', degrees=False)
    except Exception as e:
        # 如果转换失败，使用零Euler角度（保持当前姿态）
        logger.warning(f"Error converting 6D to Euler: {e}, using zero Euler angles")
        left_euler = np.zeros(3)
        right_euler = np.zeros(3)

    return np.concatenate([
        left_xyz,
        left_euler,
        [left_grip],
        right_xyz,
        right_euler,
        [right_grip]
    ])


class BiPIPERFollowerEepose(Robot):
    """
    Bimanual Piper follower arms with end-effector pose control.
    Uses DualPiperRobot for direct end-effector pose control via Piper SDK.
    """

    config_class = BiPIPERFollowerEeposeConfig
    name = "bi_piper_follower_eepose"

    def __init__(self, config: BiPIPERFollowerEeposeConfig):
        super().__init__(config)
        self.config = config
        self._camera_names = list(self.config.cameras.keys())

        # Initialize DualPiperRobot for end-effector pose control
        self.dual_piper = DualPiperRobot(
            can_interfaces=(config.left_arm_can_name, config.right_arm_can_name)
        )

        # Start position
        self.go_home()

        # Camera setup using CameraWrapper
        if not self._camera_names:
            logger.warning("No cameras configured for BiPIPERFollowerEepose")
            self.camera_wrapper = CameraWrapper(
                devices=[], width=640, height=480, fps=30
            )
        else:
            devices = []
            for name in self._camera_names:
                cam_cfg = self.config.cameras[name]
                if not hasattr(cam_cfg, "index_or_path"):
                    raise AttributeError(
                        f"Camera config for '{name}' must define 'index_or_path' to be used with CameraWrapper"
                    )
                devices.append(getattr(cam_cfg, "index_or_path"))

            first_cam_cfg = self.config.cameras[self._camera_names[0]]
            width = getattr(first_cam_cfg, "width", 640)
            height = getattr(first_cam_cfg, "height", 480)
            fps = getattr(first_cam_cfg, "fps", 30)

            num_realsense = len(devices)

            self.camera_wrapper = CameraWrapper(
                devices=devices,
                width=width,
                height=height,
                fps=fps,
                num_realsense=num_realsense,
            )

        # Keep a placeholder dict for compatibility with existing utilities
        self.cameras: dict[str, Any] = {name: None for name in self._camera_names}

    @property
    def _eepose_ft(self) -> dict[str, type]:
        """End-effector pose features: 20D (left_xyz+6d+gripper + right_xyz+6d+gripper)"""
        return {f"eepose_{i}": float for i in range(20)}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self._camera_names
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._eepose_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._eepose_ft

    @property
    def is_connected(self) -> bool:
        arms_ok = self.dual_piper.connected
        cameras_ok = len(self.camera_wrapper.cameras) == len(self._camera_names)
        return arms_ok and cameras_ok

    def connect(self, calibrate: bool = True) -> None:
        """Connect to the robot hardware."""
        if not self.dual_piper.connected:
            self.dual_piper.connect()
        # CameraWrapper opens cameras on construction; nothing to do here.

    @property
    def is_calibrated(self) -> bool:
        """DualPiperRobot doesn't have calibration, always return True."""
        return True

    def calibrate(self) -> None:
        """DualPiperRobot doesn't require calibration."""
        pass

    def configure(self) -> None:
        """DualPiperRobot doesn't require configuration."""
        pass

    def setup_motors(self) -> None:
        """DualPiperRobot doesn't have motors setup."""
        pass

    def get_observation(self) -> dict[str, Any]:
        """Get current observation including end-effector poses and camera images."""
        obs_dict = {}

        # Get end-effector poses from DualPiperRobot (7D: xyz + euler + gripper)
        left_pose, right_pose = self.dual_piper.get_state_endpos()
        
        # Convert 7D poses to 20D 6D representation
        eepose_6d = eef_6d_new_reg(left_pose, right_pose)
        
        # Add to observation dict
        for i in range(20):
            obs_dict[f"eepose_{i}"] = float(eepose_6d[i])
        
        # Build state vector for policy (20D 6D representation)
        obs_dict["observation.state"] = eepose_6d.astype(np.float32)

        # Read all camera images
        start = time.perf_counter()
        images = self.camera_wrapper.get_images()
        dt_ms = (time.perf_counter() - start) * 1e3

        if not images:
            logger.error(
                "CameraWrapper returned no images, using dummy frames for all cameras"
            )
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

            last_img = images[-1]
            for idx, cam_key in enumerate(self._camera_names):
                img = images[idx] if idx < len(images) else last_img
                obs_dict[cam_key] = img

        logger.debug(f"read {len(images)} cameras in {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Send end-effector pose action to the robot.
        
        Converts 20D 6D pose action to 14D Euler angles, then sends to DualPiperRobot.
        """
        # Extract action array from dictionary
        action_array = np.array([
            action.get(f"eepose_{i}", 0.0) for i in range(20)
        ], dtype=np.float32)
        
        # Check for invalid values (NaN or Inf)
        if not np.isfinite(action_array).all():
            logger.warning("Action contains invalid values (NaN or Inf), skipping this action")
            return action
        
        # Convert 6D representation to Euler angles (20D -> 14D)
        # Use wrapper function with validation for better error handling
        try:
            action_euler = abs_6d_2_abs_euler_with_validation(action_array)
        except Exception as e:
            logger.error(f"Error converting 6D to Euler: {e}, skipping this action")
            return action
        
        # Check for invalid values in converted action
        if not np.isfinite(action_euler).all():
            logger.warning("Converted action contains invalid values (NaN or Inf), skipping this action")
            return action
        
        # Split into left and right arm poses (7D each: xyz + euler + gripper)
        left_pose = action_euler[0:7]   # [x, y, z, euler_x, euler_y, euler_z, gripper]
        right_pose = action_euler[7:14]  # [x, y, z, euler_x, euler_y, euler_z, gripper]
        
        # Send pose command to robot (duration=0.12 matches reference implementation)
        try:
            logger.debug(f"Sending pose command: left={left_pose[:6]}, right={right_pose[:6]}")
            self.dual_piper.move_to_pose(
                left_target=left_pose,
                right_target=right_pose,
                duration=0.18
            )
            logger.debug("Pose command sent successfully")
        except Exception as e:
            logger.error(f"Error sending pose command: {e}", exc_info=True)
            return action
        
        # Small delay before gripper control (matches reference: time.sleep(0.033))
        time.sleep(0.033)
        
        # Control grippers separately
        # Note: gripper value is inverted (1 - value) to match reference implementation
        try:
            self.dual_piper.set_gripper(
                left_value=(1 - left_pose[6]/0.059),
                right_value=(1 - right_pose[6]/0.059)
            )
        except Exception as e:
            logger.error(f"Error sending gripper command: {e}")
        
        # Return action dict for compatibility
        return action

    def disconnect(self):
        """Disconnect from the robot hardware."""
        self.dual_piper.disconnect()
        # Release all camera resources held by CameraWrapper
        self.camera_wrapper.release()

    def go_home(self):
        """Move the robot to its home position."""
        self.dual_piper.go_home()
    
    def get_home_action(self) -> dict[str, float]:
        """
        Get home position as action dictionary (20D 6D representation).
        
        Home position from dual_piper.go_home():
        - Left: [0.057, 0, 0.215, 0, 1.4835, 0, 0.05] (xyz + euler + gripper)
        - Right: [0.057, 0, 0.215, 0, 1.4835, 0, 0.05]
        
        Returns:
            Action dictionary with home position in 6D representation.
        """
        # Home position in 7D format (xyz + euler + gripper)
        left_home_7d = np.array([0.057, 0, 0.215, 0, 1.4835, 0, 0.05], dtype=np.float32)
        right_home_7d = np.array([0.057, 0, 0.215, 0, 1.4835, 0, 0.05], dtype=np.float32)
        
        # Convert to 20D 6D representation
        home_6d = eef_6d_new_reg(left_home_7d, right_home_7d)
        
        # Convert to action dictionary
        home_action = {f"eepose_{i}": float(home_6d[i]) for i in range(20)}
        
        return home_action
