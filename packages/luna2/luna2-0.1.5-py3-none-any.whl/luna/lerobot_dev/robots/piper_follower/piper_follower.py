#!/usr/bin/env python

import logging
import time
from functools import cached_property
from typing import Any

import numpy as np
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_piper_follower import PIPERFollowerConfig
from .piper_bus import PIPERMotorsBus, PIPERMotorsBusConfig

logger = logging.getLogger(__name__)


class PIPERFollower(Robot):
    """
    Piper follower arm using Piper SDK over CAN.
    Implements the same external interface as other LeRobot followers.
    """

    config_class = PIPERFollowerConfig
    name = "piper_follower"

    def __init__(self, config: PIPERFollowerConfig):
        super().__init__(config)
        self.config = config

        # Following dual_piper.py: minimal config with only can_name and motors
        bus_cfg = PIPERMotorsBusConfig(
            can_name=config.can_name,
            motors={
                "joint_1": (1, "agilex_piper"),
                "joint_2": (2, "agilex_piper"),
                "joint_3": (3, "agilex_piper"),
                "joint_4": (4, "agilex_piper"),
                "joint_5": (5, "agilex_piper"),
                "joint_6": (6, "agilex_piper"),
                "gripper": (7, "agilex_piper"),
            },
        )
        self.bus = PIPERMotorsBus(config=bus_cfg)
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.bus.motors}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected and all(
            cam.is_connected for cam in self.cameras.values()
        )

    def connect(self, calibrate: bool = True) -> None:
        # Bus is already connected and enabled in __init__, check only cameras
        # If cameras dict is empty, all() returns True, so we need to check if cameras exist
        if self.cameras:
            cameras_connected = all(cam.is_connected for cam in self.cameras.values())
            if cameras_connected and self.bus.is_connected:
                raise DeviceAlreadyConnectedError(f"{self} already connected")

            # Bus is already connected and enabled in __init__, only connect cameras
            for cam in self.cameras.values():
                if not cam.is_connected:
                    cam.connect()
        else:
            # No cameras configured, bus is already connected in __init__
            # This is expected behavior, so we don't raise an error
            pass

        # Piper does not require LeRobot calibration/config steps
        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return self.bus.is_calibrated

    def calibrate(self) -> None:
        return

    def configure(self) -> None:
        return

    def setup_motors(self) -> None:
        return

    def get_observation(self) -> dict[str, Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError("Piper is not connected.")

        start = time.perf_counter()
        obs_dict = self.bus.read()
        obs_dict = {f"{motor}.pos": val for motor, val in obs_dict.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Build state vector from motor positions in the order defined by self.bus.motors
        # This ensures consistent ordering matching the action features
        state_values = np.array(
            [obs_dict[f"{motor}.pos"] for motor in self.bus.motors], dtype=np.float32
        )
        obs_dict["observation.state"] = state_values

        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError("Piper is not connected.")

        goal_pos = {
            key.removesuffix(".pos"): val
            for key, val in action.items()
            if key.endswith(".pos")
        }

        if self.config.max_relative_target is not None:
            present = self.bus.read()
            present = {k: v for k, v in present.items()}
            goal_present_pos = {key: (goal_pos[key], present[key]) for key in goal_pos}
            goal_pos = ensure_safe_goal_position(
                goal_present_pos, self.config.max_relative_target
            )

        # Preserve motor order when converting to list
        target_joints = [goal_pos[motor] for motor in self.bus.motors]
        self.bus.write(target_joints)
        return {
            f"{motor}.pos": val
            for motor, val in zip(self.bus.motors.keys(), target_joints)
        }

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError("Piper is not connected.")

        # Disconnect bus (DisConnectPort)
        self.bus.disconnect(disable_torque=None)
        # Disconnect cameras
        for cam in self.cameras.values():
            cam.disconnect()
        logger.info(f"{self} disconnected.")

    def go_home(self):
        self.bus.go_home()
