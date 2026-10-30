#pragma once
#include "../../include/generated_config.h"
#include "../common/enums.h"
#include "../common/math_utils.h"
#include "leg_kinematics.h"

namespace hexapod {

struct Joint {
    float minDeg = 0.0f, maxDeg = 0.0f;
    float clamped(float a) const { return clampf(a, minDeg, maxDeg); }
};

// Một chân: vị trí gắn lên thân, 3 khớp (giới hạn), động học.
class Leg {
public:
    void init(int index, const cfg::LegSpec& spec);
    int index() const { return index_; }
    const char* id() const { return id_; }
    const char* name() const { return name_; }
    const Joint& joint(int j) const { return joints_[j]; }
    const LegKinematics& kinematics() const { return kin_; }
    const Vec3& neutralFoot() const { return neutral_; }     // bàn chân khi đứng chuẩn, hệ thân
    Vec3 bodyToLeg(const Vec3& p) const { return (p - mount_).rotatedZ(-yaw_); }
    Vec3 legToBody(const Vec3& p) const { return p.rotatedZ(yaw_) + mount_; }

private:
    int index_ = 0;
    const char* id_ = "";
    const char* name_ = "";
    Vec3 mount_;
    float yaw_ = 0.0f;
    LegKinematics kin_;
    Joint joints_[kJointsPerLeg];
    Vec3 neutral_;
};

// Hexapod = 6 Leg, dựng từ generated_config.h.
class Hexapod {
public:
    Hexapod();
    const Leg& leg(int i) const { return legs_[i]; }

private:
    Leg legs_[kNumLegs];
};

}  // namespace hexapod
