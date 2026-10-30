#pragma once
#include <math.h>

#include "../../include/generated_config.h"
#include "../common/enums.h"

namespace hexapod {

// Pha và thứ tự nhấc của 6 chân trong 1 chu kỳ chuẩn hóa t in [0,1). Pha vung đi trước pha đứng.
class GaitPhase {
public:
    void init(const cfg::GaitProfile& profile) {
        duty_ = profile.duty;
        for (int leg = 0; leg < kNumLegs; ++leg) {
            const int slot = profile.slotOf[leg];
            offsets_[leg] = fmodf(1.0f - static_cast<float>(slot) / static_cast<float>(profile.slotCount), 1.0f);
        }
    }

    // Trả về true nếu đang vung; u in [0,1] là tiến độ trong pha hiện tại.
    bool locate(float t, int leg, float& u) const {
        const float local = fmodf(t + offsets_[leg], 1.0f);
        const float swingLen = 1.0f - duty_;
        if (local < swingLen) { u = local / swingLen; return true; }
        u = (local - swingLen) / duty_;
        return false;
    }

private:
    float duty_ = 0.5f;
    float offsets_[kNumLegs] = {0, 0, 0, 0, 0, 0};
};

}  // namespace hexapod
