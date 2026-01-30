#!/usr/bin/env python

# Minimal Piper CAN bus wrapper using Piper SDK
# Strictly following dual_piper.py implementation

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass


@dataclass
class PIPERMotorsBusConfig:
    can_name: str
    motors: dict[str, tuple[int, str]]


class PIPERMotorsBus:
    """
    Lightweight wrapper around the Piper SDK following dual_piper.py implementation.

    Only uses methods and patterns from dual_piper.py:
    - C_PiperInterface_V2(can_name) - simple constructor
    - ConnectPort() - no parameters
    - EnablePiper() - enable with polling
    - GetArmJointMsgs().joint_state - read joints
    - GetArmGripperMsgs().gripper_state - read gripper
    - MotionCtrl_2() - set motion mode
    - JointCtrl() - control joints
    - GripperCtrl() - control gripper
    - DisConnectPort() - disconnect
    """

    def __init__(self, config: PIPERMotorsBusConfig):
        # Lazy import so environments without the SDK can still import the package.
        from piper_sdk import C_PiperInterface_V2  # type: ignore

        # Following dual_piper.py: simple constructor with only can_name
        self.piper = C_PiperInterface_V2(config.can_name)
        # Following dual_piper.py: ConnectPort() with no parameters
        self.piper.ConnectPort()
        self._is_enable = False
        while not self.piper.EnablePiper():
            time.sleep(0.01)
        print("使能成功")
        self._is_enable = True

        # 注意：根据 piper_sdk 文档，未收到 MasterSlaveConfig 指令的机械臂默认为运动输出臂（从臂）状态
        # 但是，调用 JointCtrl 和 GripperCtrl 可能会触发固件自动切换为主臂模式
        # 需要进一步分析为什么会被设置成主臂模式

        self.motors: dict[str, tuple[int, str]] = config.motors
        self.config = config
        # 1000 * 180 / pi, converts radians to 0.001 degrees units used by Piper
        # Same factor as in dual_piper.py
        self.factor = 57295.7795

    # Compatibility attributes used by LeRobot
    @property
    def is_connected(self) -> bool:
        return self._is_enable

    @property
    def is_calibrated(self) -> bool:
        # Piper does not require LeRobot calibration; treat as calibrated by default
        return True

    def connect(self) -> None:
        # Already connected and enabled in __init__, no-op
        pass

    def disconnect(self, disable_torque: bool | None = None) -> None:
        # Following dual_piper.py: use DisconnectPort()
        try:
            self.piper.DisconnectPort()
        finally:
            self._is_enable = False

    @contextlib.contextmanager
    def torque_disabled(self):
        # Piper SDK handles enable/disable; expose a no-op context for compatibility
        yield

    # Read present joints in radians and gripper in meters
    # Strictly following dual_piper.py: GetArmJointMsgs().joint_state and GetArmGripperMsgs().gripper_state
    def read(self) -> dict[str, float]:
        # Following dual_piper.py line 124-125: GetArmJointMsgs().joint_state
        joint_msg = self.piper.GetArmJointMsgs()
        joint_state = joint_msg.joint_state

        # Following dual_piper.py line 184-185: GetArmGripperMsgs().gripper_state
        gripper_msg = self.piper.GetArmGripperMsgs()
        gripper_state = gripper_msg.gripper_state

        # Following dual_piper.py line 149-156: joint_state.joint_X / 57295.7795
        # Direct division as in dual_piper.py (not using inv_factor for exact match)
        factor = 57295.7795  # Same as dual_piper.py

        return {
            "joint_1": joint_state.joint_1 / factor,
            "joint_2": joint_state.joint_2 / factor,
            "joint_3": joint_state.joint_3 / factor,
            "joint_4": joint_state.joint_4 / factor,
            "joint_5": joint_state.joint_5 / factor,
            "joint_6": joint_state.joint_6 / factor,
            # Following dual_piper.py line 188: grippers_angle / 1e6
            "gripper": gripper_state.grippers_angle / 1e6,
        }

    # Write goal joints: expect order aligned to self.motors keys
    # Following dual_piper.py: MotionCtrl_2() then JointCtrl() then GripperCtrl()
    def write(self, target_joint: list[float]) -> None:
        # Already connected and enabled in __init__, no need to check

        # Convert radians to 0.001 degrees
        # Following dual_piper.py: round(joint * factor)
        j0 = round(target_joint[0] * self.factor)
        j1 = round(target_joint[1] * self.factor)
        j2 = round(target_joint[2] * self.factor)
        j3 = round(target_joint[3] * self.factor)
        j4 = round(target_joint[4] * self.factor)
        j5 = round(target_joint[5] * self.factor)
        # Following dual_piper.py: gripper uses 1000 * 1000
        gr = round(abs(target_joint[6]) * 1000 * 1000)

        # Following dual_piper.py: MotionCtrl_2(0x01, 0x01, 10, 0x00)
        # Using default speed of 10 (can be adjusted if needed)
        # self.piper.MotionCtrl_2(0x01, 0x01, 50, 0x00)
        # self.piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)
        # 30 can massively increase success rate!
        # self.piper.MotionCtrl_2(0x01, 0x01, 20, 0x00)
        self.piper.MotionCtrl_2(0x01, 0x01, 35, 0x00)
        # self.piper.MotionCtrl_2(0x01, 0x01, 15, 0x00)
        # self.piper.MotionCtrl_2(0x01, 0x01, 15, 0x00)
        # self.piper.MotionCtrl_2(0x01, 0x01, 15, 0x00)
        # Following dual_piper.py: JointCtrl(j0, j1, j2, j3, j4, j5)
        self.piper.JointCtrl(j0, j1, j2, j3, j4, j5)
        # Following dual_piper.py: GripperCtrl(abs(gr), 1000, 0x01, 0)
        self.piper.GripperCtrl(abs(gr), 1000, 0x01, 0)

    def go_home(self):
        """Move the robot to its home position."""
        self.piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)
        self.piper.JointCtrl(0, 0, 0, 0, 0, 0)
