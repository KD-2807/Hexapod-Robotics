"""MotionContext: trạng thái dùng chung giữa MotionController và các action."""
from dataclasses import dataclass, field
from typing import Dict, List

from shared.common.enums import GaitType
from shared.common.math_utils import Vec3
from shared.common.types import BodyPose, Velocity
from shared.gait_core.base_gait import BaseGait
from shared.gait_core.gait_factory import GaitFactory
from shared.posture_core.posture_generator import PostureGenerator


@dataclass
class MotionContext:
    posture: PostureGenerator
    gait_factory: GaitFactory
    stand_pose: BodyPose
    sit_pose: BodyPose
    speed: float
    gait_type: GaitType
    velocity: Velocity = field(default_factory=Velocity)      # vận tốc đã làm mượt
    _gaits: Dict[GaitType, BaseGait] = field(default_factory=dict)

    def gait(self, gait_type: GaitType) -> BaseGait:
        if gait_type not in self._gaits:
            self._gaits[gait_type] = self.gait_factory.create(gait_type)
        return self._gaits[gait_type]

    @staticmethod
    def zero_offsets() -> List[Vec3]:
        return [Vec3()] * 6
