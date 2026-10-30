from shared.motion_core.actions.base_action import ActionOutput, BaseAction


class SitDown(BaseAction):
    """Ngồi xuống: hạ thân xuống tư thế ngồi."""
    name = "sit_down"

    def start(self) -> None:
        self._ctx.posture.set_target(self._ctx.sit_pose)

    def update(self, dt: float) -> ActionOutput:
        return ActionOutput(self._ctx.zero_offsets(), self._ctx.posture.update(dt))

    @property
    def finished(self) -> bool:
        return self._ctx.posture.reached
