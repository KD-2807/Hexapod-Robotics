#include "leg_kinematics.h"

namespace hexapod {

namespace { constexpr float kReachMargin = 1e-3f; }   // mm - tránh NaN khi duỗi thẳng / gập hết

Vec3 LegKinematics::forward(float t1, float t2, float t3) const {
    const float reach = l1_ + l2_ * cosf(t2) + l3_ * cosf(t2 + t3);
    return Vec3(reach * cosf(t1), reach * sinf(t1), l2_ * sinf(t2) + l3_ * sinf(t2 + t3));
}

IKResult LegKinematics::inverse(const Vec3& p) const {
    IKResult r;
    r.t1 = atan2f(p.y, p.x);
    const float r2 = hypotf(p.x, p.y) - l1_;
    float r1 = hypotf(p.z, r2);

    const float low = fabsf(l2_ - l3_) + kReachMargin;
    const float high = l2_ + l3_ - kReachMargin;
    r.reachable = (r1 >= low && r1 <= high);
    r1 = clampf(r1, low, high);

    const float phi1 = acosf(clampf((l2_ * l2_ + r1 * r1 - l3_ * l3_) / (2.0f * l2_ * r1), -1.0f, 1.0f));
    const float phi2 = atan2f(p.z, r2);
    r.t2 = phi1 + phi2;
    r.t3 = -kPi + acosf(clampf((l2_ * l2_ + l3_ * l3_ - r1 * r1) / (2.0f * l2_ * l3_), -1.0f, 1.0f));
    return r;
}

}  // namespace hexapod
