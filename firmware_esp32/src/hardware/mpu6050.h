#pragma once
#include <stdint.h>

#include "../interfaces/clock.h"
#include "../interfaces/i2c_bus.h"

namespace hexapod {

struct ImuSample {
    float ax, ay, az;     // g
    float gx, gy, gz;     // độ/giây
};

// Driver MPU6050 qua I2C (gia tốc ±2 g, con quay ±250 °/s).
class Mpu6050 {
public:
    Mpu6050(I2CBus& bus, Clock& clock, uint8_t address) : bus_(bus), clock_(clock), address_(address) {}
    bool begin();
    bool read(ImuSample& out);

private:
    I2CBus& bus_;
    Clock& clock_;
    uint8_t address_;
    bool writeReg(uint8_t reg, uint8_t value);
};

}  // namespace hexapod
