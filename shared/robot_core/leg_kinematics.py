"""Động học thuận/nghịch cho 1 chân 3 khớp (hình học phẳng, theo báo cáo)."""
from dataclasses import dataclass
from typing import List, Tuple

from shared.common.math_utils import Vec3
from shared.common.leg_geometry import forward_kinematics, inverse_kinematics, joint_chain


@dataclass(frozen=True)
class IKResult:
    angles: Tuple[float, float, float]   # theta1 (coxa), theta2 (femur), theta3 (tibia) - radian
    reachable: bool


class LegKinematics:
    """Hệ chân: gốc tại trục coxa, X hướng ra ngoài, Z hướng lên."""

    def __init__(self, coxa: float, femur: float, tibia: float):
        self.l1, self.l2, self.l3 = coxa, femur, tibia

    def forward(self, t1: float, t2: float, t3: float) -> Vec3:
        return Vec3(*forward_kinematics((t1, t2, t3), (self.l1, self.l2, self.l3)))

    def inverse(self, p: Vec3) -> IKResult:
        angles, reachable = inverse_kinematics((p.x,p.y,p.z),(self.l1,self.l2,self.l3))
        return IKResult(angles, reachable)

    def joint_points(self, t1: float, t2: float, t3: float) -> List[Vec3]:
        """Các điểm cuối từng đốt (coxa, femur, bàn chân) trong hệ chân - dùng để vẽ."""
        return [Vec3(*point) for point in joint_chain(
            (t1, t2, t3), (self.l1, self.l2, self.l3))[1:]]
