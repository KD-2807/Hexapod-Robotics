"""BaseGait: khung chung của mọi dáng đi. Lớp con chỉ khai báo loại dáng đi (và hiệu chỉnh vận tốc)."""
import math
from abc import ABC
from typing import List, Sequence

from shared.common.enums import GaitType
from shared.common.math_utils import Vec3, clamp, deg2rad
from shared.common.types import Velocity
from shared.gait_core.gait_config import GaitConfig, GaitProfile
from shared.gait_core.gait_phase import GaitPhase
from shared.gait_core.trajectory import Trajectory
from shared.robot_core.leg import Leg


class BaseGait(ABC):
    gait_type: GaitType

    def __init__(self, config: GaitConfig, profile: GaitProfile, legs: Sequence[Leg]):
        self._config = config
        self._profile = profile
        self._legs = legs
        self._phase = GaitPhase.from_profile(profile, [leg.id for leg in legs])
        self.t = 0.0

    def reset(self) -> None:
        self.t = 0.0

    def advance(self, dt: float, speed: float) -> None:
        self.t = (self.t + dt * speed / self._profile.cycle_time_s) % 1.0

    def shape_velocity(self, velocity: Velocity) -> Velocity:
        """Cho phép dáng đi lọc bớt thành phần vận tốc (mặc định giữ nguyên)."""
        return velocity

    def stride_for(self, leg: Leg, velocity: Velocity) -> Vec3:
        """Quãng đường thân đi được trong 1 pha đứng, theo hướng của chân này (tịnh tiến + xoay)."""
        cfg = self._config
        turn = deg2rad(cfg.turn_angle_deg) * velocity.wz
        foot = leg.neutral_foot
        stride = Vec3(cfg.step_length * velocity.vx - turn * foot.y,
                      cfg.step_length * velocity.vy + turn * foot.x, 0.0)
        length = stride.norm_xy()
        if length > cfg.max_stride:
            stride = stride.scaled(cfg.max_stride / length)
        return stride

    def foot_offsets(self, velocity: Velocity) -> List[Vec3]:
        velocity = self.shape_velocity(velocity)
        offsets = []
        for leg in self._legs:
            stride = self.stride_for(leg, velocity)
            height = self._config.step_height * clamp(stride.norm_xy() / self._config.lift_ramp, 0.0, 1.0)
            swinging, u = self._phase.locate(self.t, leg.index)
            offsets.append(Trajectory.swing(u, stride, height) if swinging else Trajectory.stance(u, stride))
        return offsets

    def stance_phase_mask(self, velocity: Velocity) -> List[bool]:
        """Lịch chống của gait hiện tại; không thay thế cảm biến tiếp xúc."""
        velocity = self.shape_velocity(velocity)
        return [self.stride_for(leg, velocity).norm_xy() < 1e-9
                or not self._phase.locate(self.t, leg.index)[0]
                for leg in self._legs]
