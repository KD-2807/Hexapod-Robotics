"""Hành động đặc biệt theo thời gian: chào, nhún, múa."""
import math
from abc import abstractmethod
from dataclasses import replace
from typing import Dict, List, Type

from shared.common.enums import LegId
from shared.common.math_utils import Vec3, clamp
from shared.common.types import BodyPose
from shared.motion_core.actions.base_action import ActionOutput, BaseAction
from shared.motion_core.context import MotionContext

_TAU = 2.0 * math.pi


class SpecialAction(BaseAction):
    """Khung chung: cộng thêm độ lệch (theo hàm thời gian có bao đóng vào/ra) lên tư thế đang giữ."""
    duration = 3.0
    ramp = 0.5

    def __init__(self, ctx: MotionContext):
        super().__init__(ctx)
        self._t = 0.0

    def start(self) -> None:
        self._t = 0.0

    @property
    def finished(self) -> bool:
        return self._t >= self.duration

    def _envelope(self) -> float:
        return clamp(min(self._t / self.ramp, (self.duration - self._t) / self.ramp), 0.0, 1.0)

    @abstractmethod
    def _delta_pose(self, t: float, env: float) -> BodyPose:
        ...

    def _foot_offsets(self, t: float, env: float) -> List[Vec3]:
        return self._ctx.zero_offsets()

    def update(self, dt: float) -> ActionOutput:
        self._t = min(self._t + dt, self.duration)
        env = self._envelope()
        base = self._ctx.posture.update(dt)
        d = self._delta_pose(self._t, env)
        pose = replace(base, z=base.z + d.z, roll=base.roll + d.roll,
                       pitch=base.pitch + d.pitch, yaw=base.yaw + d.yaw)
        return ActionOutput(self._foot_offsets(self._t, env), pose)


class Wave(SpecialAction):
    """Chào: cúi người về phía trước, nhấc chân trước bên phải và vẫy."""
    name = "wave"
    duration = 4.0

    def _delta_pose(self, t: float, env: float) -> BodyPose:
        return BodyPose(pitch=-5.0 * env)

    def _foot_offsets(self, t: float, env: float) -> List[Vec3]:
        offsets = self._ctx.zero_offsets()
        offsets[LegId.RIGHT_FRONT] = Vec3(12.0 * math.sin(_TAU * 1.5 * t) * env, 8.0 * env, 32.0 * env)
        return offsets


class Bob(SpecialAction):
    """Nhún: thân nhún lên xuống."""
    name = "bob"
    duration = 3.0

    def _delta_pose(self, t: float, env: float) -> BodyPose:
        return BodyPose(z=-10.0 * env * (1.0 - math.cos(_TAU * 1.5 * t)) / 2.0)


class Dance(SpecialAction):
    """Múa: thân lắc và xoay nhịp nhàng."""
    name = "dance"
    duration = 6.0

    def _delta_pose(self, t: float, env: float) -> BodyPose:
        return BodyPose(z=-4.0 * env * math.sin(_TAU * 1.6 * t),
                        roll=10.0 * env * math.sin(_TAU * 0.8 * t),
                        yaw=12.0 * env * math.sin(_TAU * 0.4 * t))


SPECIAL_ACTIONS: Dict[str, Type[SpecialAction]] = {cls.name: cls for cls in (Wave, Bob, Dance)}


def create_special(name: str, ctx: MotionContext) -> SpecialAction:
    return SPECIAL_ACTIONS[name](ctx)
