"""Một chân: vị trí gắn lên thân, 3 khớp, động học."""
import math
from typing import List

from shared.common.math_utils import Vec3, deg2rad
from shared.robot_core.joint import Joint
from shared.robot_core.leg_kinematics import LegKinematics
from shared.robot_core.robot_config import LegSpec


class Leg:
    def __init__(self, index: int, spec: LegSpec, kinematics: LegKinematics, joints: List[Joint],
                 stance_radius: float, stand_height: float):
        self.index = index
        self.id = spec.id
        self.name = spec.name
        self.group = spec.group
        self.mount = Vec3(spec.x, spec.y, 0.0)
        self.yaw = deg2rad(spec.yaw_deg)
        self.kinematics = kinematics
        self.joints = joints
        self._neutral = self.leg_to_body(Vec3(stance_radius, 0.0, -stand_height))

    @property
    def neutral_foot(self) -> Vec3:
        """Vị trí bàn chân khi đứng chuẩn, trong hệ thân."""
        return self._neutral

    def body_to_leg(self, p: Vec3) -> Vec3:
        return (p - self.mount).rotated_z(-self.yaw)

    def leg_to_body(self, p: Vec3) -> Vec3:
        return p.rotated_z(self.yaw) + self.mount
