#pragma once
#include "../common/types.h"

namespace hexapod {

// Phần chấp hành: PCA9685 trên robot thật, hoặc đối tượng giả khi test trên máy.
class ActuatorBackend {
public:
    virtual ~ActuatorBackend() {}
    virtual bool enable() = 0;                                  // bật xuất xung servo
    virtual void disable() = 0;                                 // ngắt xung (servo thả lỏng)
    virtual bool apply(const JointFrame& frame) = 0;            // xuất 18 góc khớp (độ)
    virtual bool applyRawServo(int leg, int joint, float servoDeg) = 0;   // góc servo thô 0..180
};

}  // namespace hexapod
