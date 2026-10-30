#pragma once
#include "../interfaces/io.h"

namespace hexapod {

// Đo điện áp pin qua cầu chia áp: V = mV_tại_chân / 1000 * tỉ_lệ_chia. Làm mượt bằng trung bình trượt mũ.
class BatteryMonitor {
public:
    BatteryMonitor(AnalogInput& input, float dividerRatio) : input_(input), ratio_(dividerRatio) {}

    void update() {
        const float v = input_.readMilliVolts() / 1000.0f * ratio_;
        voltage_ = valid_ ? voltage_ + kAlpha * (v - voltage_) : v;
        valid_ = true;
    }
    float voltage() const { return voltage_; }
    bool valid() const { return valid_; }

private:
    static constexpr float kAlpha = 0.1f;
    AnalogInput& input_;
    float ratio_;
    float voltage_ = 0.0f;
    bool valid_ = false;
};

}  // namespace hexapod
