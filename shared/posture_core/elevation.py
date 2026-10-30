from dataclasses import replace

from shared.common.types import BodyPose
from shared.posture_core.base_posture import BasePosture


class Elevation(BasePosture):
    """Nâng/hạ thân (mm)."""
    def apply(self, pose: BodyPose, value: float) -> BodyPose:
        return replace(pose, z=value)
