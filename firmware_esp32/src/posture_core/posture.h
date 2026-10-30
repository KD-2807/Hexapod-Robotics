#pragma once
#include "../common/math_utils.h"
#include "../common/types.h"

namespace hexapod {

// Một bậc tự do của tư thế thân, có giới hạn.
class BasePosture {
public:
    BasePosture(float low, float high) : low_(low), high_(high) {}
    virtual ~BasePosture() {}
    bool inRange(float v) const { return low_ <= v && v <= high_; }
    float clamp(float v) const { return clampf(v, low_, high_); }
    virtual void apply(BodyPose& pose, float value) const = 0;   // đặt bậc tự do này bằng value

private:
    float low_, high_;
};

class Elevation : public BasePosture {     // nâng/hạ thân (mm)
public:
    using BasePosture::BasePosture;
    void apply(BodyPose& p, float v) const override { p.z = v; }
};

class Roll : public BasePosture {          // nghiêng trái/phải (độ)
public:
    using BasePosture::BasePosture;
    void apply(BodyPose& p, float v) const override { p.roll = v; }
};

class Pitch : public BasePosture {         // nghiêng trước/sau (độ)
public:
    using BasePosture::BasePosture;
    void apply(BodyPose& p, float v) const override { p.pitch = v; }
};

class Yaw : public BasePosture {           // xoay thân quanh trục đứng (độ)
public:
    using BasePosture::BasePosture;
    void apply(BodyPose& p, float v) const override { p.yaw = v; }
};

}  // namespace hexapod
