#include "posture_generator.h"

namespace hexapod {

BodyPose PostureGenerator::effectiveTarget() const {
    if (!walking_) return target_;
    BodyPose t = target_;
    t.z = clampf(t.z, cfg::kWalkZMin, cfg::kWalkZMax);
    t.roll = clampf(t.roll, -cfg::kWalkRollLimit, cfg::kWalkRollLimit);
    t.pitch = clampf(t.pitch, -cfg::kWalkPitchLimit, cfg::kWalkPitchLimit);
    t.yaw = clampf(t.yaw, -cfg::kWalkYawLimit, cfg::kWalkYawLimit);
    return t;
}

bool PostureGenerator::inWalkingEnvelope() const {
    const BodyPose& p = current_;
    return cfg::kWalkZMin <= p.z && p.z <= cfg::kWalkZMax && fabsf(p.roll) <= cfg::kWalkRollLimit &&
           fabsf(p.pitch) <= cfg::kWalkPitchLimit && fabsf(p.yaw) <= cfg::kWalkYawLimit;
}

const char* PostureGenerator::validate(float z, float roll, float pitch, float yaw) const {
    if (!elevation_.inRange(z)) return "z";
    if (!roll_.inRange(roll)) return "roll";
    if (!pitch_.inRange(pitch)) return "pitch";
    if (!yaw_.inRange(yaw)) return "yaw";
    return nullptr;
}

BodyPose PostureGenerator::compose(float z, float roll, float pitch, float yaw) const {
    BodyPose pose;
    elevation_.apply(pose, elevation_.clamp(z));
    roll_.apply(pose, roll_.clamp(roll));
    pitch_.apply(pose, pitch_.clamp(pitch));
    yaw_.apply(pose, yaw_.clamp(yaw));
    return pose;
}

const BodyPose& PostureGenerator::update(float dt) {
    const BodyPose tgt = effectiveTarget();
    const float dz = cfg::kZRate * dt, da = cfg::kAngleRate * dt;
    current_.z = moveTowards(current_.z, tgt.z, dz);
    current_.roll = moveTowards(current_.roll, tgt.roll, da);
    current_.pitch = moveTowards(current_.pitch, tgt.pitch, da);
    current_.yaw = moveTowards(current_.yaw, tgt.yaw, da);
    return current_;
}

}  // namespace hexapod
