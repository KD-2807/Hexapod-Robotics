#pragma once
#include "../common/math_utils.h"

namespace hexapod {

// Quy ước: X phải, Y tiến, Z lên; R = Rz(yaw)·Rx(pitch)·Ry(roll). Góc tính bằng radian.
inline Vec3 rotateX(const Vec3& v, float a) {
    const float c = cosf(a), s = sinf(a);
    return Vec3(v.x, c * v.y - s * v.z, s * v.y + c * v.z);
}

inline Vec3 rotateY(const Vec3& v, float a) {
    const float c = cosf(a), s = sinf(a);
    return Vec3(c * v.x + s * v.z, v.y, -s * v.x + c * v.z);
}

// v' = Rᵀ·v
inline Vec3 rotateRpyInverse(const Vec3& v, float roll, float pitch, float yaw) {
    return rotateY(rotateX(v.rotatedZ(-yaw), -pitch), -roll);
}

}  // namespace hexapod
