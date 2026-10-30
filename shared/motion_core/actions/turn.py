from shared.common.enums import GaitType
from shared.common.types import Velocity
from shared.gait_core.base_gait import BaseGait
from shared.motion_core.actions.walk import Walk


class Turn(Walk):
    """Xoay tại chỗ bằng RotationGait, chỉ dùng wz."""
    name = "turn"

    def shape(self, velocity: Velocity) -> Velocity:
        return Velocity(0.0, 0.0, velocity.wz)

    def _gait(self) -> BaseGait:
        return self._ctx.gait(GaitType.ROTATION)
