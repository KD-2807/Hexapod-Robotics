from shared.common.enums import GaitType
from shared.common.types import Velocity
from shared.gait_core.base_gait import BaseGait


class RotationGait(BaseGait):
    """Các chân bước theo cung tròn quanh tâm thân: chỉ dùng thành phần xoay wz."""
    gait_type = GaitType.ROTATION

    def shape_velocity(self, velocity: Velocity) -> Velocity:
        return Velocity(0.0, 0.0, velocity.wz)
