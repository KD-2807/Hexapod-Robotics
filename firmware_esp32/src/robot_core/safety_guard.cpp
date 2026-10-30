#include "safety_guard.h"

#include <stdio.h>

namespace hexapod {

void SafetyGuard::filter(const JointFrame& frame, float dt, SafetyResult& out) {
    out.reason[0] = '\0';
    if (!frame.isFinite()) {
        out.ok = false;
        out.frame = hasPrevious_ ? previous_ : frame;
        snprintf(out.reason, sizeof(out.reason), "NaN trong JointFrame");
        return;
    }

    JointFrame safe = frame;
    const float margin = cfg::kAngleMarginDeg;
    bool violated = false;
    for (int l = 0; l < kNumLegs; ++l) {
        for (int j = 0; j < kJointsPerLeg; ++j) {
            const Joint& joint = hexapod_.leg(l).joint(j);
            const float a = safe.get(l, j);
            if (!violated && !(joint.minDeg - margin <= a && a <= joint.maxDeg + margin)) {
                static const char* kNames[3] = {"coxa", "femur", "tibia"};
                violated = true;
                snprintf(out.reason, sizeof(out.reason), "%s.%s=%.1f ngoài [%.0f, %.0f]",
                         hexapod_.leg(l).name(), kNames[j], a, joint.minDeg, joint.maxDeg);
            }
            safe.set(l, j, joint.clamped(a));
        }
    }

    if (hasPrevious_) {
        const float maxStep = cfg::kMaxJointSpeedDps * dt;
        for (int i = 0; i < kNumServos; ++i) {
            safe.angles[i] = clampf(safe.angles[i], previous_.angles[i] - maxStep, previous_.angles[i] + maxStep);
        }
    }

    if (violated) {
        out.ok = false;
        out.frame = hasPrevious_ ? previous_ : safe;
        return;
    }
    previous_ = safe;
    hasPrevious_ = true;
    out.ok = true;
    out.frame = safe;
}

}  // namespace hexapod
