"""Phép quay hệ tọa độ thân. Quy ước: X phải, Y tiến, Z lên; R = Rz(yaw)·Rx(pitch)·Ry(roll)."""
import math

from shared.common.math_utils import Vec3


def rotate_x(v: Vec3, angle: float) -> Vec3:
    c, s = math.cos(angle), math.sin(angle)
    return Vec3(v.x, c * v.y - s * v.z, s * v.y + c * v.z)


def rotate_y(v: Vec3, angle: float) -> Vec3:
    c, s = math.cos(angle), math.sin(angle)
    return Vec3(c * v.x + s * v.z, v.y, -s * v.x + c * v.z)


def rotate_rpy(v: Vec3, roll: float, pitch: float, yaw: float) -> Vec3:
    """v' = R·v (đổi từ hệ thân sang hệ nền khi thân nghiêng)."""
    return rotate_x(rotate_y(v, roll), pitch).rotated_z(yaw)


def rotate_rpy_inverse(v: Vec3, roll: float, pitch: float, yaw: float) -> Vec3:
    """v' = Rᵀ·v."""
    return rotate_y(rotate_x(v.rotated_z(-yaw), -pitch), -roll)
