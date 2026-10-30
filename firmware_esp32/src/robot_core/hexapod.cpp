#include "hexapod.h"

namespace hexapod {

void Leg::init(int index, const cfg::LegSpec& spec) {
    index_ = index;
    id_ = spec.id;
    name_ = spec.name;
    mount_ = Vec3(spec.x, spec.y, 0.0f);
    yaw_ = deg2rad(spec.yawDeg);
    kin_ = LegKinematics(cfg::kCoxaLen, cfg::kFemurLen, cfg::kTibiaLen);
    for (int j = 0; j < kJointsPerLeg; ++j) {
        joints_[j].minDeg = cfg::kJointLimits[j].minDeg;
        joints_[j].maxDeg = cfg::kJointLimits[j].maxDeg;
    }
    neutral_ = legToBody(Vec3(cfg::kStanceRadius, 0.0f, -cfg::kStandHeight));
}

Hexapod::Hexapod() {
    for (int i = 0; i < kNumLegs; ++i) legs_[i].init(i, cfg::kLegs[i]);
}

}  // namespace hexapod
