# zeroArm_sdk/arm_types.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class JointState:
    can_id: int
    position: float      # radians
    velocity: float
    torque: float
    enable: bool
    mode: int


@dataclass
class GripperState:
    position: float
    velocity: float
    torque: float
    enable: bool
    mode: int


@dataclass
class Pose:
    x: float
    y: float
    z: float
    qw: float
    qx: float
    qy: float
    qz: float


@dataclass
class FullArmState:
    joints: List[JointState]
    gripper: Optional[GripperState] = None
    eef_pose: Optional[Pose] = None