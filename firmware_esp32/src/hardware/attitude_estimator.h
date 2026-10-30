#pragma once
#include <math.h>

#include "../common/math_utils.h"
#include "mpu6050.h"

namespace hexapod {

// Ước lượng roll/pitch bằng bộ lọc bù (con quay tích phân + gia tốc kế làm mốc).
// Quy ước gắn cảm biến: trục X của MPU6050 hướng về phía trước robot, mặt linh kiện hướng lên.
class AttitudeEstimator {
public:
    explicit AttitudeEstimator(float alpha) : alpha_(alpha) {}

    void update(const ImuSample& s, float dt) {
        const float accRoll = rad2deg(atan2f(s.ay, s.az));
        const float accPitch = rad2deg(atan2f(-s.ax, sqrtf(s.ay * s.ay + s.az * s.az)));
        if (!initialized_) {
            roll_ = accRoll;
            pitch_ = accPitch;
            initialized_ = true;
            return;
        }
        roll_ = alpha_ * (roll_ + s.gx * dt) + (1.0f - alpha_) * accRoll;
        pitch_ = alpha_ * (pitch_ + s.gy * dt) + (1.0f - alpha_) * accPitch;
    }
    float roll() const { return roll_; }
    float pitch() const { return pitch_; }
    bool valid() const { return initialized_; }

private:
    float alpha_;
    float roll_ = 0.0f, pitch_ = 0.0f;
    bool initialized_ = false;
};

}  // namespace hexapod
