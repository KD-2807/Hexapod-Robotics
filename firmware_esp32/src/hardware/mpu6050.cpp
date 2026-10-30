#include "mpu6050.h"

namespace hexapod {

namespace {
constexpr uint8_t kPwrMgmt1 = 0x6B, kConfig = 0x1A, kGyroConfig = 0x1B, kAccelConfig = 0x1C, kAccelXout = 0x3B;
constexpr float kAccelLsbPerG = 16384.0f, kGyroLsbPerDps = 131.0f;

int16_t be16(const uint8_t* p) { return static_cast<int16_t>((static_cast<uint16_t>(p[0]) << 8) | p[1]); }
}  // namespace

bool Mpu6050::writeReg(uint8_t reg, uint8_t value) {
    const uint8_t data[2] = {reg, value};
    return bus_.write(address_, data, 2);
}

bool Mpu6050::begin() {
    if (!bus_.probe(address_)) return false;
    bool ok = writeReg(kPwrMgmt1, 0x00);       // thoát chế độ ngủ
    clock_.delayMs(10);
    ok = writeReg(kConfig, 0x03) && ok;        // lọc thông thấp ~44 Hz
    ok = writeReg(kGyroConfig, 0x00) && ok;    // ±250 °/s
    ok = writeReg(kAccelConfig, 0x00) && ok;   // ±2 g
    return ok;
}

bool Mpu6050::read(ImuSample& out) {
    uint8_t raw[14];
    if (!bus_.readRegister(address_, kAccelXout, raw, sizeof(raw))) return false;
    out.ax = be16(&raw[0]) / kAccelLsbPerG;
    out.ay = be16(&raw[2]) / kAccelLsbPerG;
    out.az = be16(&raw[4]) / kAccelLsbPerG;
    // raw[6..7] là nhiệt độ
    out.gx = be16(&raw[8]) / kGyroLsbPerDps;
    out.gy = be16(&raw[10]) / kGyroLsbPerDps;
    out.gz = be16(&raw[12]) / kGyroLsbPerDps;
    return true;
}

}  // namespace hexapod
