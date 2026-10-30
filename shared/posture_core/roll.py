from dataclasses import replace

from shared.common.types import BodyPose
from shared.posture_core.base_posture import BasePosture


class Roll(BasePosture):
    """Nghiêng thân trái/phải (độ)."""
    def apply(self, pose: BodyPose, value: float) -> BodyPose:
        return replace(pose, roll=value)
