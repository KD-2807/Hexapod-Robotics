#pragma once
#include "../interfaces/actuator_backend.h"
#include "../interfaces/io.h"
#include "servo_manager.h"

namespace hexapod {

// ActuatorBackend cho robot thật: xuất xung qua 2 PCA9685. outputEnable (tùy chọn) là chân OE, tích cực mức thấp.
class PCA9685Backend : public ActuatorBackend {
public:
    PCA9685Backend(ServoManager& servos, DigitalOutput* outputEnable)
        : servos_(servos), oe_(outputEnable) {}

    bool enable() override {
        if (!servos_.begin()) return false;
        if (oe_) oe_->write(false);
        return true;
    }
    void disable() override {
        servos_.allOff();
        if (oe_) oe_->write(true);        // OE cao: ngắt cứng mọi đầu ra
    }
    bool apply(const JointFrame& frame) override { return servos_.writeFrame(frame); }
    bool applyRawServo(int leg, int joint, float servoDeg) override { return servos_.writeRaw(leg, joint, servoDeg); }

private:
    ServoManager& servos_;
    DigitalOutput* oe_;
};

}  // namespace hexapod
