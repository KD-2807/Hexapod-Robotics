#include "servo_manager.h"

namespace hexapod {

// Dựng mảng board bằng chỉ số (C++11 không cho mảng đối tượng không có constructor mặc định).
ServoManager::ServoManager(I2CBus& bus, Clock& clock)
    : boards_{ServoBoard(bus, clock, cfg::kBoardAddress[0], cfg::kOscillatorHz, cfg::kPwmHz),
              ServoBoard(bus, clock, cfg::kBoardAddress[1], cfg::kOscillatorHz, cfg::kPwmHz)} {
    static_assert(cfg::kBoardCount == 2, "ServoManager được viết cho 2 board PCA9685 (18 servo)");
    for (int i = 0; i < kNumServos; ++i) servos_[i] = Servo(cfg::kServoCal[i]);
}

bool ServoManager::begin() {
    bool ok = true;
    for (int b = 0; b < cfg::kBoardCount; ++b) ok = boards_[b].init() && ok;
    return ok;
}

bool ServoManager::flushAll() {
    bool ok = true;
    for (int b = 0; b < cfg::kBoardCount; ++b) ok = boards_[b].flush() && ok;
    return ok;
}

bool ServoManager::writeFrame(const JointFrame& frame) {
    for (int i = 0; i < kNumServos; ++i) {
        const float servoDeg = servos_[i].servoAngle(frame.angles[i]);
        boards_[cfg::kServoMap[i].board].setPulseUs(cfg::kServoMap[i].channel, servos_[i].pulseUs(servoDeg));
    }
    return flushAll();
}

bool ServoManager::writeRaw(int leg, int joint, float servoDeg) {
    const int i = leg * kJointsPerLeg + joint;
    ServoBoard& board = boards_[cfg::kServoMap[i].board];
    board.setPulseUs(cfg::kServoMap[i].channel, servos_[i].pulseUs(servoDeg));
    return board.flush();
}

void ServoManager::allOff() {
    for (int b = 0; b < cfg::kBoardCount; ++b) boards_[b].allOff();
}

}  // namespace hexapod
