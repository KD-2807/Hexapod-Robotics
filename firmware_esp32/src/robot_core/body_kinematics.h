#pragma once
#include "../common/types.h"
#include "hexapod.h"
#include "transforms.h"

namespace hexapod {

// Tư thế thân + vị trí bàn chân trên nền -> mục tiêu trong hệ từng chân.
class BodyKinematics {
public:
    explicit BodyKinematics(const Hexapod& hexapod) : hexapod_(hexapod) {}

    void legTargets(const BodyPose& pose, const Vec3 feetGround[kNumLegs], Vec3 out[kNumLegs]) const {
        const Vec3 translation(pose.x, pose.y, pose.z);
        const float roll = deg2rad(pose.roll), pitch = deg2rad(pose.pitch), yaw = deg2rad(pose.yaw);
        for (int i = 0; i < kNumLegs; ++i) {
            const Vec3 inBody = rotateRpyInverse(feetGround[i] - translation, roll, pitch, yaw);
            out[i] = hexapod_.leg(i).bodyToLeg(inBody);
        }
    }

private:
    const Hexapod& hexapod_;
};

}  // namespace hexapod
