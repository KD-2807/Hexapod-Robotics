#pragma once
#include "pca9685.h"

namespace hexapod {

// 1 mạch PCA9685 + bộ đệm tick của 16 kênh; mọi thay đổi được ghi xuống chip bằng 1 lần flush().
class ServoBoard {
public:
    ServoBoard(I2CBus& bus, Clock& clock, uint8_t address, uint32_t oscHz, int pwmHz)
        : chip_(bus, clock, address, oscHz, pwmHz) {
        for (int c = 0; c < PCA9685::kChannels; ++c) ticks_[c] = PCA9685::kFullOff;
    }
    bool init() { return chip_.init(); }
    void setPulseUs(int channel, float pulseUs) { ticks_[channel] = chip_.ticksForPulse(pulseUs); }
    bool flush() { return chip_.writeChannels(ticks_); }
    bool allOff() { return chip_.allOff(); }
    const PCA9685& chip() const { return chip_; }
    uint16_t ticks(int channel) const { return ticks_[channel]; }

private:
    PCA9685 chip_;
    uint16_t ticks_[PCA9685::kChannels];
};

}  // namespace hexapod
