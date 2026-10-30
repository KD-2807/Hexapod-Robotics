#pragma once
#include <math.h>

namespace hexapod {

constexpr float kPi = 3.14159265358979f;

inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }
inline float deg2rad(float d) { return d * kPi / 180.0f; }
inline float rad2deg(float r) { return r * 180.0f / kPi; }

// Dịch cur về tgt tối đa maxStep (giới hạn tốc độ thay đổi).
inline float moveTowards(float cur, float tgt, float maxStep) {
    const float d = tgt - cur;
    if (fabsf(d) <= maxStep) return tgt;
    return cur + (d > 0.0f ? maxStep : -maxStep);
}

struct Vec3 {
    float x, y, z;
    constexpr Vec3() : x(0.0f), y(0.0f), z(0.0f) {}
    constexpr Vec3(float x_, float y_, float z_) : x(x_), y(y_), z(z_) {}
    Vec3 operator+(const Vec3& o) const { return Vec3(x + o.x, y + o.y, z + o.z); }
    Vec3 operator-(const Vec3& o) const { return Vec3(x - o.x, y - o.y, z - o.z); }
    Vec3 scaled(float k) const { return Vec3(x * k, y * k, z * k); }
    float normXY() const { return hypotf(x, y); }
    Vec3 rotatedZ(float a) const {
        const float c = cosf(a), s = sinf(a);
        return Vec3(c * x - s * y, s * x + c * y, z);
    }
};

}  // namespace hexapod
