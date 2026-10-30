#include "pca9685.h"

#include <math.h>

namespace hexapod {

namespace {
constexpr uint8_t kMode1 = 0x00, kPrescale = 0xFE, kLed0OnL = 0x06, kAllLedOffL = 0xFC;
constexpr uint8_t kSleep = 0x10, kAutoIncrement = 0x20, kRestart = 0x80;
}  // namespace

constexpr int PCA9685::kChannels;
constexpr uint16_t PCA9685::kFullOff;

uint8_t PCA9685::prescale() const {
    // prescale = round(osc / (4096 * freq)) - 1
    return static_cast<uint8_t>(floorf(static_cast<float>(oscillatorHz_) / (4096.0f * pwmHz_) + 0.5f) - 1.0f);
}

uint16_t PCA9685::ticksForPulse(float pulseUs) const {
    const float periodUs = 1000000.0f / static_cast<float>(pwmHz_);
    float ticks = floorf(pulseUs / periodUs * 4096.0f + 0.5f);
    if (ticks < 0.0f) ticks = 0.0f;
    if (ticks > 4095.0f) ticks = 4095.0f;
    return static_cast<uint16_t>(ticks);
}

bool PCA9685::writeReg(uint8_t reg, uint8_t value) {
    const uint8_t data[2] = {reg, value};
    return bus_.write(address_, data, 2);
}

bool PCA9685::init() {
    bool ok = writeReg(kMode1, kSleep);              // ngủ để được phép đổi prescale
    ok = writeReg(kPrescale, prescale()) && ok;
    ok = writeReg(kMode1, kAutoIncrement) && ok;     // thức dậy, bật auto-increment
    clock_.delayMs(1);                               // dao động ổn định (>= 500 µs)
    ok = writeReg(kMode1, kRestart | kAutoIncrement) && ok;
    return ok && allOff();
}

bool PCA9685::writeChannels(const uint16_t offTicks[kChannels]) {
    uint8_t data[1 + 4 * kChannels];
    data[0] = kLed0OnL;
    for (int c = 0; c < kChannels; ++c) {
        uint8_t* p = &data[1 + 4 * c];
        p[0] = 0;                                    // ON = 0
        p[1] = 0;
        p[2] = static_cast<uint8_t>(offTicks[c] & 0xFF);
        p[3] = static_cast<uint8_t>((offTicks[c] >> 8) & 0xFF);   // bit 4 = full off
    }
    return bus_.write(address_, data, sizeof(data));
}

bool PCA9685::allOff() {
    const uint8_t data[3] = {kAllLedOffL, 0x00, 0x10};           // ALL_LED_OFF = full off
    return bus_.write(address_, data, 3);
}

}  // namespace hexapod
