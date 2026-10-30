from shared.common.enums import GaitType
from shared.common.types import Velocity
from shared.gait_core.base_gait import BaseGait
from shared.motion_core.actions.base_action import ActionOutput, BaseAction


class Walk(BaseAction):
    """Đi tiến/lùi (kèm đi chéo, đi vòng cung) bằng dáng đi đang chọn."""
    name = "walk"

    def shape(self, velocity: Velocity) -> Velocity:
        return velocity

    def _gait(self) -> BaseGait:
        return self._ctx.gait(self._ctx.gait_type)

    def update(self, dt: float) -> ActionOutput:
        gait = self._gait()
        gait.advance(dt, self._ctx.speed)
        offsets = gait.foot_offsets(self.shape(self._ctx.velocity))
        return ActionOutput(offsets, self._ctx.posture.update(dt))
