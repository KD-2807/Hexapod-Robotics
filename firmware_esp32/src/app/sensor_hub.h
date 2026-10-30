#pragma once
#include "../hardware/attitude_estimator.h"
#include "../hardware/battery_monitor.h"
#include "../hardware/mpu6050.h"
#include "status_reporter.h"

namespace hexapod {

// Đọc cảm biến (IMU, pin) mỗi chu kỳ và đẩy kết quả vào StatusReporter. imu/battery có thể là nullptr.
class SensorHub {
public:
    SensorHub(Mpu6050* imu, float imuAlpha, BatteryMonitor* battery, StatusReporter& reporter)
        : imu_(imu), attitude_(imuAlpha), battery_(battery), reporter_(reporter) {}

    void update(float dt) {
        if (imu_) {
            ImuSample s;
            if (imu_->read(s)) {
                attitude_.update(s, dt);
                reporter_.setImu(attitude_.roll(), attitude_.pitch());
            }
        }
        if (battery_) {
            battery_->update();
            reporter_.setBattery(battery_->voltage());
        }
    }

private:
    Mpu6050* imu_;
    AttitudeEstimator attitude_;
    BatteryMonitor* battery_;
    StatusReporter& reporter_;
};

}  // namespace hexapod
