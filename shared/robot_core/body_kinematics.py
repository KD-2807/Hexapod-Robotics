"""Động học toàn thân: tư thế thân + vị trí bàn chân trên nền -> mục tiêu trong hệ từng chân."""
from typing import List, Sequence

from shared.common.math_utils import Vec3, deg2rad
from shared.common.types import BodyPose
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.transforms import rotate_rpy_inverse


class BodyKinematics:
    def __init__(self, hexapod: Hexapod):
        self._hexapod = hexapod

    def leg_targets(self, pose: BodyPose, feet_ground: Sequence[Vec3]) -> List[Vec3]:
        """feet_ground: vị trí bàn chân trong hệ nền (trùng hệ thân khi thân ở tư thế chuẩn)."""
        translation = Vec3(pose.x, pose.y, pose.z)
        roll, pitch, yaw = deg2rad(pose.roll), deg2rad(pose.pitch), deg2rad(pose.yaw)
        targets = []
        for leg, foot in zip(self._hexapod.legs, feet_ground):
            in_body = rotate_rpy_inverse(foot - translation, roll, pitch, yaw)
            targets.append(leg.body_to_leg(in_body))
        return targets
