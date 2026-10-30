#pragma once
#include <stdint.h>

#include "../interfaces/clock.h"
#include "../interfaces/i2c_bus.h"

namespace hexapod {

// Driver PCA9685 (16 kênh PWM, I2C). Mỗi kênh ghi bằng số tick tắt (0..4095); kFullOff = tắt hẳn kênh.
class PCA9685 {
public:
    static constexpr int kChannels = 16;
    static constexpr uint16_t kFullOff = 0x1000;

    PCA9685(I2CBus& bus, Clock& clock, uint8_t address, uint32_t oscillatorHz, int pwmHz)
        : bus_(bus), clock_(clock), address_(address), oscillatorHz_(oscillatorHz), pwmHz_(pwmHz) {}

    uint8_t address() const { return address_; }
    bool init();                                          // reset + đặt tần số PWM
    bool writeChannels(const uint16_t offTicks[kChannels]);   // ghi cả 16 kênh trong 1 lần (auto-increment)
    bool allOff();                                        // ngắt xung mọi kênh
    uint8_t prescale() const;
    uint16_t ticksForPulse(float pulseUs) const;          // µs -> tick (0..4095)

private:
    I2CBus& bus_;
    Clock& clock_;
    uint8_t address_;
    uint32_t oscillatorHz_;
    int pwmHz_;

    bool writeReg(uint8_t reg, uint8_t value);
};

}  // namespace hexapod
