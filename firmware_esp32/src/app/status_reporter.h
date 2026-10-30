#pragma once
#include <stddef.h>
#include <stdint.h>

#include "../motion_core/motion_controller.h"

namespace hexapod {

// Dựng gói STATUS và quyết định khi nào đẩy định kỳ về PC.
class StatusReporter {
public:
    StatusReporter(const MotionController& controller, float rateHz)
        : controller_(controller), period_(1.0f / rateHz) {}

    void setConnected(bool connected) { connected_ = connected; }
    void setBattery(float volts) { batteryV_ = volts; hasBattery_ = true; }
    void setImu(float rollDeg, float pitchDeg) { imuRoll_ = rollDeg; imuPitch_ = pitchDeg; hasImu_ = true; }
    void setI2cDevices(const uint8_t* addresses, int count);

    bool due(float dt) {
        elapsed_ += dt;
        if (elapsed_ < period_) return false;
        elapsed_ = 0.0f;
        return true;
    }
    size_t encode(char* buffer, size_t capacity, long seq) const;

private:
    static constexpr int kMaxDevices = 8;
    const MotionController& controller_;
    float period_;
    float elapsed_ = 0.0f;
    bool connected_ = false;
    bool hasBattery_ = false, hasImu_ = false;
    float batteryV_ = 0.0f, imuRoll_ = 0.0f, imuPitch_ = 0.0f;
    uint8_t i2c_[kMaxDevices] = {0};
    int i2cCount_ = 0;
};

}  // namespace hexapod
