from shared.motion_core.actions.base_action import ActionOutput, BaseAction


class BodyPoseAction(BaseAction):
    """Giữ nguyên các chân; thân nội suy mượt về tư thế đích (nâng/hạ/nghiêng/xoay thân)."""
    name = "body_pose"

    def update(self, dt: float) -> ActionOutput:
        return ActionOutput(self._ctx.zero_offsets(), self._ctx.posture.update(dt))
