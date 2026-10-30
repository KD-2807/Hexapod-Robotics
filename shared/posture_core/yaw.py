from dataclasses import replace

from shared.common.types import BodyPose
from shared.posture_core.base_posture import BasePosture


class Yaw(BasePosture):
    """Xoay thân quanh trục đứng (độ) - chân không bước."""
    def apply(self, pose: BodyPose, value: float) -> BodyPose:
        return replace(pose, yaw=value)
