from shared.common.types import Velocity
from shared.motion_core.actions.walk import Walk


class Strafe(Walk):
    """Đi ngang trái/phải: thân giữ hướng, chỉ dùng vx."""
    name = "strafe"

    def shape(self, velocity: Velocity) -> Velocity:
        return Velocity(velocity.vx, 0.0, 0.0)
