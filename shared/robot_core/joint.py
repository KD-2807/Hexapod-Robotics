"""Một khớp quay: góc hiện tại và giới hạn."""
from shared.common.enums import JointType
from shared.common.math_utils import clamp


class Joint:
    def __init__(self, joint_type: JointType, min_deg: float, max_deg: float):
        self.type = joint_type
        self.min_deg = min_deg
        self.max_deg = max_deg
        self.angle_deg = 0.0

    def clamped(self, angle_deg: float) -> float:
        return clamp(angle_deg, self.min_deg, self.max_deg)

    def set_angle(self, angle_deg: float) -> None:
        self.angle_deg = self.clamped(angle_deg)
