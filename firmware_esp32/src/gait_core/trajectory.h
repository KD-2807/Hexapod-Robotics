#pragma once
#include "../common/math_utils.h"

namespace hexapod {

// Quỹ đạo bàn chân: pha vung (Bézier bậc 2) và pha đứng (đường thẳng). stride = quãng thân đi được trong 1 pha đứng.
struct Trajectory {
    static float bezier2(float p0, float p1, float p2, float t) {
        const float inv = 1.0f - t;
        return inv * inv * p0 + 2.0f * inv * t * p1 + t * t * p2;
    }
    // u in [0,1]: từ -stride/2 (sau) tới +stride/2 (trước), nhấc cao `height` ở giữa.
    static Vec3 swing(float u, const Vec3& stride, float height) {
        return Vec3(lerpf(-stride.x / 2, stride.x / 2, u), lerpf(-stride.y / 2, stride.y / 2, u),
                    bezier2(0.0f, 2.0f * height, 0.0f, u));
    }
    // u in [0,1]: bàn chân bám đất, trượt ngược từ +stride/2 về -stride/2.
    static Vec3 stance(float u, const Vec3& stride) {
        return Vec3(lerpf(stride.x / 2, -stride.x / 2, u), lerpf(stride.y / 2, -stride.y / 2, u), 0.0f);
    }
};

}  // namespace hexapod
