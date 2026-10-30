#pragma once
#include "../../include/generated_config.h"
#include "../common/math_utils.h"

namespace hexapod {

// Calibration 1 servo: góc khớp (độ) -> góc servo (0..180) -> độ rộng xung (µs).
class Servo {
public:
    Servo() : cal_{90.0f, 1, 500.0f, 2400.0f} {}
    explicit Servo(const cfg::ServoCal& cal) : cal_(cal) {}

    float servoAngle(float jointDeg) const {
        return clampf(cal_.offsetDeg + static_cast<float>(cal_.direction) * jointDeg, 0.0f, 180.0f);
    }
    float pulseUs(float servoDeg) const {
        return lerpf(cal_.pulseMinUs, cal_.pulseMaxUs, clampf(servoDeg, 0.0f, 180.0f) / 180.0f);
    }

private:
    cfg::ServoCal cal_;
};

}  // namespace hexapod
