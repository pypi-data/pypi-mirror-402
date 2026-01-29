# zeroArm_sdk/arm.py
# Copyright (c) 2026 Han / ForceEase Co. All Rights Reserved.
# Public interface for ZeroArm SDK - only for licensed hardware owners

import gettext
import os
from typing import Dict, List, Optional, Callable, Tuple
from ._core import RobotArm as _RobotArmImpl
from .arm_types import FullArmState, JointState, GripperState, Pose
from .exceptions import ArmNotFoundError, ArmConnectionError, ArmCommandError


class RobotArm(_RobotArmImpl):
    """
    Main class for controlling ZeroArm robotic arm.

    机械臂控制主类。

    Features / 主要功能：
    - Automatically find and connect to the arm / 自动发现并连接机械臂
    - Connect using short serial number (first 6 characters) / 支持使用序列号前6位快速连接
    - Control all joints, gripper, and end-effector pose / 控制所有关节、夹爪、末端位姿
    - Switch control modes (zero gravity, etc.) / 切换控制模式（零重力等）
    - Graceful and emergency shutdown / 优雅关机与紧急停止
    - Real-time state updates / 实时状态更新
    """

    def __init__(self, sn: Optional[str] = None, ip: Optional[str] = None):
        """
        Create a new RobotArm instance.

        创建 RobotArm 实例。

        Args / 参数:
            sn: Full serial number of the arm (optional) / 机械臂完整序列号（可选）
            ip: IP address of the arm (optional) / 机械臂 IP 地址（可选）

        Note / 注意:
        - If both sn and ip are None, use auto_discover_and_connect() to find the arm automatically.
          如果 sn 和 ip 均未提供，可通过 auto_discover_and_connect() 自动发现机械臂。
        """
        super().__init__(sn, ip)

    async def find_all_devices(self, timeout: float = 1.0) -> List[Dict]:
        """
        Find all available ZeroArm devices on the network.

        在局域网内发现所有可用的 ZeroArm 设备。

        Args / 参数:
            timeout: Maximum time to wait for discovery (seconds, default 1.0) / 发现最大等待时间（秒，默认 1.0）

        Returns / 返回:
            List[Dict]: List of device information dictionaries / 设备信息字典列表

        Example / 示例:
            devices = await arm.find_all_devices(timeout=2.0)
            print(devices)
        """
        return await super().find_all_devices(timeout)

    async def auto_discover_and_connect(self, timeout: float = 1.0) -> bool:
        """
        Automatically find the first available arm and connect to it.
        Shows a progress bar during connection.

        自动发现局域网内第一个可用机械臂并连接。
        连接过程中显示进度条。

        Args / 参数:
            timeout: Maximum wait time for discovery (seconds, default 1.0) / 发现最大等待时间（秒，默认 1.0）

        Returns / 返回:
            bool: True if connected successfully, False otherwise / 连接成功返回 True，否则 False

        Example / 示例:
            success = await arm.auto_discover_and_connect(timeout=3.0)
            if success:
                print(_("Arm is ready!"))  # 支持本地化：已连接机械臂！
        """
        return await super().auto_discover_and_connect(timeout)

    async def connect_with_short_sn(self, short_sn: str, timeout: float = 1.0) -> bool:
        """
        Connect to an arm using the first 6 characters of its serial number.

        使用序列号前6位（或更多）连接机械臂。

        Args / 参数:
            short_sn: First 6 characters of the serial number / 序列号前缀（建议至少6位）
            timeout: Maximum wait time for discovery (seconds, default 1.0) / 发现最大等待时间（秒，默认 1.0）

        Returns / 返回:
            bool: True if connected successfully, False otherwise / 连接成功返回 True，否则 False

        Example / 示例:
            await arm.connect_with_short_sn("F82FCD")
        """
        return await super().connect_with_short_sn(short_sn, timeout)

    async def connect(self) -> bool:
        """
        Connect to the arm using current serial number and IP.

        使用当前已设置的序列号和 IP 进行连接。

        Returns / 返回:
            bool: True if successful, False otherwise / 连接成功返回 True，否则 False

        Note / 注意:
        - Must set sn and ip first (via __init__ or manually).
          必须先设置 sn 和 ip。
        """
        return await super().connect()

    def is_connected(self) -> bool:
        """
        Check if the arm is currently connected.

        检查当前是否已连接到机械臂。

        Returns / 返回:
            bool: True if connected, False otherwise / 已连接返回 True，否则 False
        """
        return super().is_connected()

    @property
    def current_state(self) -> Optional[FullArmState]:
        """
        Get the latest received arm state.

        获取机械臂的最新状态（实时更新）。

        Returns / 返回:
            FullArmState or None: Latest arm state / 最新机械臂状态；若无数据则返回 None

        Example / 示例:
            state = arm.current_state
            if state:
                print(f"Joint 1: {state.joints[0].position:.3f} rad")
        """
        return super().current_state

    def on_state_update(self, callback: Callable[[FullArmState], None]):
        """
        Set a callback function to be called on every new state update.

        设置状态更新回调函数，每次接收到新状态时调用。

        Args / 参数:
            callback: Function that receives FullArmState / 接收 FullArmState 的回调函数

        Example / 示例:
            def handler(state):
                print(f"End-effector pose: {state.eef_pose}")
            arm.on_state_update(handler)
        """
        super().on_state_update(callback)

    async def set_joint(
        self,
        can_id: int,
        target_pos: float,
        target_vel: float = 0.0,
        target_tau: float = 0.0,
        mode: int = 0,
        enable: bool = True,
        set_zero: bool = False,
        max_vel: Optional[float] = None,
        max_acc: Optional[float] = None,
        max_jerk: Optional[float] = None,
    ):
        """
        Move a single joint to target position.

        控制单个关节运动到目标位置。

        Args / 参数:
            can_id: Joint CAN ID (usually starts from 1) / 关节 CAN ID（通常从 1 开始）
            target_pos: Target position in radians / 目标位置（弧度）
            target_vel: Target velocity (rad/s), default 0.0 / 目标速度（弧度/秒，默认 0.0）
            target_tau: Target torque (Nm), default 0.0 / 目标力矩（Nm，默认 0.0）
            mode: Control mode (0 = position mode, see arm manual) / 控制模式（0=位置模式，参考臂说明书）
            enable: Enable the joint, default True / 是否使能关节，默认 True
            set_zero: Set current position as zero, default False / 是否将当前位置设为零位，默认 False
            max_vel/max_acc/max_jerk: Optional speed/acceleration/jerk limits / 可选的最大速度/加速度/加加速度限制

        Example / 示例:
            await arm.set_joint(1, 0.785)  # Move joint 1 to 45° / 将关节1移动到45°
        """
        await super().set_joint(
            can_id,
            target_pos,
            target_vel,
            target_tau,
            mode,
            enable,
            set_zero,
            max_vel,
            max_acc,
            max_jerk,
        )

    async def set_gripper(
        self,
        target_pos: float,
        target_vel: float = 0.0,
        target_tau: float = 0.0,
        set_zero: bool = False,
    ):
        """
        Control gripper opening/closing.

        控制夹爪开合。

        Args / 参数:
            target_pos: Target gripper position / 目标开合位置
            target_vel: Gripper velocity, default 0.0 / 夹爪运动速度，默认 0.0
            target_tau: Gripper torque, default 0.0 / 夹爪力矩，默认 0.0
            set_zero: Set current position as zero, default False / 是否设为零位，默认 False

        Example / 示例:
            await arm.set_gripper(0.08)  # Open gripper to 8cm / 将夹爪打开到8cm
        """
        await super().set_gripper(target_pos, target_vel, target_tau, set_zero)

    async def set_tf(
        self, x: float, y: float, z: float, qw: float, qx: float, qy: float, qz: float
    ):
        """
        Set end-effector position and orientation (quaternion).

        设置末端执行器位姿（位置 + 四元数姿态）。

        Args / 参数:
            x, y, z: Position in meters / 位置（米）
            qw, qx, qy, qz: Orientation quaternion / 姿态四元数

        Example / 示例:
            await arm.set_tf(0.5, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0)
        """
        await super().set_tf(x, y, z, qw, qx, qy, qz)

    async def set_joints_batch(
        self,
        joint_targets: List[Tuple[int, float]],
        target_vel: float = 0.0,
        target_tau: float = 0.0,
        mode: int = 0,
        enable: bool = True,
        set_zero: bool = False,
        max_vel: int = 10,
        max_acc: int = 30,
        max_jerk: int = 50,
        wait_for_completion: bool = False,
        timeout: float = 8.0,
        tolerance: float = 0.015,
    ) -> bool:
        """
        Move multiple joints simultaneously (recommended for synchronized motion).

        同时控制多个关节运动（推荐用于同步轨迹规划）。

        Args / 参数:
            joint_targets: List of (can_id, target_pos) tuples / 关节目标列表：[(can_id, 目标位置), ...]
            target_vel/target_tau: Reserved parameters (currently not used) / 保留参数（当前未使用）
            mode/enable/set_zero: Global mode, enable, zero setting / 全局模式、使能、零位设置
            max_vel/max_acc/max_jerk: Global limits (deg/s, deg/s², deg/s³) / 全局最大速度/加速度/加加速度限制
            wait_for_completion: Wait until all joints reach targets, default False / 是否等待到达目标，默认 False
            timeout: Timeout in seconds (when waiting) / 等待超时时间（秒）
            tolerance: Position tolerance in radians, default 0.015 (~0.86°) / 位置容差（弧度，默认 0.015）

        Returns / 返回:
            bool: Command sent successfully (or reached targets if waiting) / 命令发送成功（或等待成功）

        Example / 示例:
            await arm.set_joints_batch([(1, 0.5), (2, -0.3), (5, 1.57)])
        """
        return await super().set_joints_batch(
            joint_targets,
            target_vel,
            target_tau,
            mode,
            enable,
            set_zero,
            max_vel,
            max_acc,
            max_jerk,
            wait_for_completion,
            timeout,
            tolerance,
        )

    async def zero_gravity_mode(self):
        """
        Switch to zero gravity mode (free manual movement).

        切换到零重力模式（可手动自由拖动机械臂）。
        """
        await super().zero_gravity_mode()

    async def back_to_zero(self):
        """
        Move all joints back to zero position.

        将所有关节移动回零位。
        """
        await super().back_to_zero()

    async def back_to_initial(self):
        """
        Move all joints to factory initial positions.

        将所有关节移动到出厂初始位置。
        """
        await super().back_to_initial()

    async def gracefully_shutdown(self, wait_before_shutdown: float = 10.0):
        """
        Gracefully shutdown: move to initial pose → wait → power off.

        优雅关机：先移动到初始位置 → 等待 → 安全断电。

        Args / 参数:
            wait_before_shutdown: Wait time after movement (seconds, default 10.0) / 运动完成后等待时间（秒，默认 10.0）
        """
        await super().gracefully_shutdown(wait_before_shutdown)

    async def emergency_shutdown(self):
        """
        Immediate emergency stop and shutdown.

        紧急停止并关机（立即停止所有运动并断电）。
        Use only in emergency situations / 仅在紧急情况下使用。
        """
        await super().emergency_shutdown()

    async def close(self):
        """
        Close connection and release resources.

        关闭连接并释放所有资源。
        """
        await super().close()
