#pragma once
#include <math.h>

#include "enums.h"

namespace hexapod {

// Vận tốc chuẩn hóa [-1, 1]. vx: sang phải, vy: tiến, wz: xoay ngược chiều kim đồng hồ.
struct Velocity {
    float vx, vy, wz;
    Velocity() : vx(0), vy(0), wz(0) {}
    Velocity(float x, float y, float w) : vx(x), vy(y), wz(w) {}
    float magnitude() const { return fmaxf(fabsf(vx), fmaxf(fabsf(vy), fabsf(wz))); }
    bool isZero(float eps = 1e-3f) const { return magnitude() < eps; }
};

// Tư thế thân so với tư thế đứng chuẩn: z (mm), roll/pitch/yaw (độ). Quy ước như bản Python.
struct BodyPose {
    float x, y, z, roll, pitch, yaw;
    BodyPose() : x(0), y(0), z(0), roll(0), pitch(0), yaw(0) {}
    bool operator==(const BodyPose& o) const {
        return x == o.x && y == o.y && z == o.z && roll == o.roll && pitch == o.pitch && yaw == o.yaw;
    }
};

// 18 góc khớp (độ), thứ tự leg*3 + joint.
struct JointFrame {
    float angles[kNumServos];
    JointFrame() { for (int i = 0; i < kNumServos; ++i) angles[i] = 0.0f; }
    float get(int leg, int joint) const { return angles[leg * kJointsPerLeg + joint]; }
    void set(int leg, int joint, float deg) { angles[leg * kJointsPerLeg + joint] = deg; }
    bool isFinite() const {
        for (int i = 0; i < kNumServos; ++i) if (!isfinite(angles[i])) return false;
        return true;
    }
    float maxAbsDiff(const JointFrame& o) const {
        float m = 0.0f;
        for (int i = 0; i < kNumServos; ++i) m = fmaxf(m, fabsf(angles[i] - o.angles[i]));
        return m;
    }
};

// Kết quả thao tác (không dùng exception vì Arduino-ESP32 biên dịch với -fno-exceptions).
struct Result {
    ErrorCode code;
    const char* message;   // chuỗi tĩnh hoặc bộ đệm của chủ thể, hợp lệ tới lần gọi kế tiếp
    Result() : code(ErrorCode::None), message("") {}
    Result(ErrorCode c, const char* m) : code(c), message(m) {}
    bool ok() const { return code == ErrorCode::None; }
    static Result success() { return Result(); }
    static Result fail(ErrorCode c, const char* m) { return Result(c, m); }
};

}  // namespace hexapod
