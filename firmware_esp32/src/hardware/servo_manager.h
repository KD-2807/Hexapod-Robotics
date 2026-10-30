#pragma once
#include "../../include/generated_config.h"
#include "../common/types.h"
#include "servo.h"
#include "servo_board.h"

namespace hexapod {

// Quản lý 18 servo trên các ServoBoard theo servo_map: JointFrame -> xung -> ghi mỗi board 1 lần.
class ServoManager {
public:
    ServoManager(I2CBus& bus, Clock& clock);
    bool begin();                                   // khởi tạo mọi PCA9685
    bool writeFrame(const JointFrame& frame);       // góc khớp (đã qua calibration)
    bool writeRaw(int leg, int joint, float servoDeg);
    void allOff();
    const ServoBoard& board(int i) const { return boards_[i]; }
    const Servo& servo(int leg, int joint) const { return servos_[leg * kJointsPerLeg + joint]; }

private:
    ServoBoard boards_[cfg::kBoardCount];
    Servo servos_[kNumServos];
    bool flushAll();
};

}  // namespace hexapod
