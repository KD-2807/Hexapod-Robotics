#include "actions.h"

namespace hexapod {

namespace { constexpr float kTau = 2.0f * kPi; }

void Walk::update(float dt, ActionOutput& out) {
    BaseGait& g = gait();
    g.advance(dt, ctx_.speed);
    g.footOffsets(shape(ctx_.velocity), out.footOffsets);
    out.pose = ctx_.posture.update(dt);
}

constexpr float SpecialAction::kRamp;

void SpecialAction::update(float dt, ActionOutput& out) {
    t_ = fminf(t_ + dt, duration_);
    const float env = clampf(fminf(t_ / kRamp, (duration_ - t_) / kRamp), 0.0f, 1.0f);
    const BodyPose base = ctx_.posture.update(dt);
    BodyPose d;
    deltaPose(t_, env, d);
    out.pose = base;
    out.pose.z = base.z + d.z;
    out.pose.roll = base.roll + d.roll;
    out.pose.pitch = base.pitch + d.pitch;
    out.pose.yaw = base.yaw + d.yaw;
    footOffsets(t_, env, out);
}

void WaveAction::deltaPose(float, float env, BodyPose& d) const { d.pitch = -5.0f * env; }

void WaveAction::footOffsets(float t, float env, ActionOutput& out) const {
    zeroOffsets(out);
    out.footOffsets[5] = Vec3(12.0f * sinf(kTau * 1.5f * t) * env, 8.0f * env, 32.0f * env);   // RIGHT_FRONT
}

void BobAction::deltaPose(float t, float env, BodyPose& d) const {
    d.z = -10.0f * env * (1.0f - cosf(kTau * 1.5f * t)) / 2.0f;
}

void DanceAction::deltaPose(float t, float env, BodyPose& d) const {
    d.z = -4.0f * env * sinf(kTau * 1.6f * t);
    d.roll = 10.0f * env * sinf(kTau * 0.8f * t);
    d.yaw = 12.0f * env * sinf(kTau * 0.4f * t);
}

}  // namespace hexapod
