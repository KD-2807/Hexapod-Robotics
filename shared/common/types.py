"""Kiểu dữ liệu giá trị dùng giữa các module."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Velocity:
    """Vận tốc chuẩn hóa trong [-1, 1]. vx: sang phải, vy: tiến, wz: xoay ngược chiều kim đồng hồ."""
    vx: float = 0.0
    vy: float = 0.0
    wz: float = 0.0

    def magnitude(self) -> float:
        return max(abs(self.vx), abs(self.vy), abs(self.wz))

    def is_zero(self, eps: float = 1e-3) -> bool:
        return self.magnitude() < eps


@dataclass(frozen=True)
class BodyPose:
    """Tư thế thân so với tư thế đứng chuẩn. z (mm, + là nâng lên), góc theo độ.

    roll: quay quanh trục Y (tiến), dương = nghiêng sang phải (bên phải thấp xuống).
    pitch: quay quanh trục X (ngang), dương = ngẩng đầu. yaw: quay quanh Z, dương = ngược chiều kim đồng hồ.
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
