from shared.motion_core.actions.base_action import ActionOutput, BaseAction


class StandUp(BaseAction):
    """Đứng dậy: nâng thân từ tư thế ngồi lên chiều cao chuẩn."""
    name = "stand_up"

    def start(self) -> None:
        self._ctx.posture.set_target(self._ctx.stand_pose)

    def update(self, dt: float) -> ActionOutput:
        return ActionOutput(self._ctx.zero_offsets(), self._ctx.posture.update(dt))

    @property
    def finished(self) -> bool:
        return self._ctx.posture.reached
