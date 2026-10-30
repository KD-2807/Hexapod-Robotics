#include "base_gait.h"

namespace hexapod {

// Quãng đường thân đi được trong 1 pha đứng, theo hướng của chân này (tịnh tiến + xoay).
Vec3 BaseGait::strideFor(const Leg& leg, const Velocity& v) const {
    const float turn = deg2rad(cfg::kTurnAngleDeg) * v.wz;
    const Vec3& foot = leg.neutralFoot();
    Vec3 stride(cfg::kStepLength * v.vx - turn * foot.y, cfg::kStepLength * v.vy + turn * foot.x, 0.0f);
    const float length = stride.normXY();
    if (length > cfg::kMaxStride) stride = stride.scaled(cfg::kMaxStride / length);
    return stride;
}

void BaseGait::footOffsets(const Velocity& velocity, Vec3 out[kNumLegs]) const {
    const Velocity v = shapeVelocity(velocity);
    for (int i = 0; i < kNumLegs; ++i) {
        const Vec3 stride = strideFor(hexapod_.leg(i), v);
        const float height = cfg::kStepHeight * clampf(stride.normXY() / cfg::kLiftRamp, 0.0f, 1.0f);
        float u = 0.0f;
        const bool swinging = phase_.locate(t_, i, u);
        out[i] = swinging ? Trajectory::swing(u, stride, height) : Trajectory::stance(u, stride);
    }
}

}  // namespace hexapod
