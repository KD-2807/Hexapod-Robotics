"""Quỹ đạo bàn chân: pha vung (Bézier bậc 2) và pha đứng (đường thẳng)."""
from shared.common.math_utils import Vec3, lerp


def bezier2(p0: float, p1: float, p2: float, t: float) -> float:
    inv = 1.0 - t
    return inv * inv * p0 + 2.0 * inv * t * p1 + t * t * p2


class Trajectory:
    """Độ dịch bàn chân so với vị trí chuẩn. stride = quãng đường thân đi được trong 1 pha đứng."""

    @staticmethod
    def swing(u: float, stride: Vec3, height: float) -> Vec3:
        """u in [0,1]: từ -stride/2 (sau) tới +stride/2 (trước), nhấc cao `height` ở giữa."""
        return Vec3(lerp(-stride.x / 2, stride.x / 2, u),
                    lerp(-stride.y / 2, stride.y / 2, u),
                    bezier2(0.0, 2.0 * height, 0.0, u))

    @staticmethod
    def stance(u: float, stride: Vec3) -> Vec3:
        """u in [0,1]: bàn chân bám đất, trượt ngược từ +stride/2 về -stride/2."""
        return Vec3(lerp(stride.x / 2, -stride.x / 2, u),
                    lerp(stride.y / 2, -stride.y / 2, u), 0.0)
