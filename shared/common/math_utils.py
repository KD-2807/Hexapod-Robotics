"""Hàm toán nhỏ và Vec3 (không dùng numpy để mô hình giống firmware C++)."""
import math
from dataclasses import dataclass


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def deg2rad(deg: float) -> float:
    return deg * math.pi / 180.0


def rad2deg(rad: float) -> float:
    return rad * 180.0 / math.pi


def move_towards(current: float, target: float, max_step: float) -> float:
    """Dịch current về target tối đa max_step (giới hạn tốc độ thay đổi)."""
    delta = target - current
    if abs(delta) <= max_step:
        return target
    return current + math.copysign(max_step, delta)


@dataclass(frozen=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def scaled(self, k: float) -> "Vec3":
        return Vec3(self.x * k, self.y * k, self.z * k)

    def norm_xy(self) -> float:
        return math.hypot(self.x, self.y)

    def rotated_z(self, angle: float) -> "Vec3":
        c, s = math.cos(angle), math.sin(angle)
        return Vec3(c * self.x - s * self.y, s * self.x + c * self.y, self.z)
