"""Visualizer: vẽ robot 3D bằng matplotlib từ JointFrame (dùng chính FK của lõi điều khiển)."""
import math
from typing import List, Tuple

from shared.common.math_utils import Vec3, deg2rad
from shared.common.types import BodyPose
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.joint_frame import JointFrame
from shared.robot_core.transforms import rotate_rpy

_LEG_COLORS = ["#d62728", "#ff7f0e", "#bcbd22", "#2ca02c", "#1f77b4", "#9467bd"]


class Visualizer:
    def __init__(self, hexapod: Hexapod, axes=None, span_mm: float = 230.0):
        import matplotlib.pyplot as plt          # nạp trễ: lõi không phụ thuộc matplotlib
        self._hexapod = hexapod
        self._span = span_mm
        if axes is None:
            self.figure = plt.figure(figsize=(7, 6))
            axes = self.figure.add_subplot(111, projection="3d")
        else:
            self.figure = axes.figure
        self.axes = axes

    def leg_points_world(self, frame: JointFrame, pose: BodyPose) -> List[List[Vec3]]:
        """Với mỗi chân: [điểm gốc coxa, cuối coxa, cuối femur, bàn chân] trong hệ nền (z=0 là mặt đất)."""
        roll, pitch, yaw = deg2rad(pose.roll), deg2rad(pose.pitch), deg2rad(pose.yaw)
        origin = Vec3(pose.x, pose.y, pose.z + self._hexapod.config.stand_height)
        result = []
        for leg in self._hexapod.legs:
            t1, t2, t3 = (deg2rad(frame.get(leg.index, j)) for j in range(3))
            local = [Vec3()] + leg.kinematics.joint_points(t1, t2, t3)
            result.append([rotate_rpy(leg.leg_to_body(p), roll, pitch, yaw) + origin for p in local])
        return result

    def body_outline_world(self, pose: BodyPose) -> List[Vec3]:
        roll, pitch, yaw = deg2rad(pose.roll), deg2rad(pose.pitch), deg2rad(pose.yaw)
        origin = Vec3(pose.x, pose.y, pose.z + self._hexapod.config.stand_height)
        pts = [rotate_rpy(leg.mount, roll, pitch, yaw) + origin for leg in self._hexapod.legs]
        return pts + pts[:1]

    def draw(self, frame: JointFrame, pose: BodyPose, title: str = "") -> None:
        ax = self.axes
        ax.cla()
        s = self._span
        ax.set_xlim(-s, s); ax.set_ylim(-s, s); ax.set_zlim(0, s)
        ax.set_xlabel("X (phải)"); ax.set_ylabel("Y (tiến)"); ax.set_zlabel("Z")
        ax.set_box_aspect((1, 1, 0.5))
        ax.plot([-s, s, s, -s, -s], [-s, -s, s, s, -s], [0] * 5, color="#bbbbbb", linewidth=0.8)   # mặt đất
        body = self.body_outline_world(pose)
        ax.plot([p.x for p in body], [p.y for p in body], [p.z for p in body], color="black", linewidth=3)
        for index, points in enumerate(self.leg_points_world(frame, pose)):
            ax.plot([p.x for p in points], [p.y for p in points], [p.z for p in points],
                    color=_LEG_COLORS[index], linewidth=2.5, marker="o", markersize=3)
            foot = points[-1]
            ax.scatter([foot.x], [foot.y], [max(foot.z, 0.0)], color=_LEG_COLORS[index], s=20)
        ax.set_title(title)
