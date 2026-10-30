#pragma once
#include "../common/types.h"
#include "body_kinematics.h"
#include "hexapod.h"

namespace hexapod {

// Ghép (độ dịch bàn chân từ gait) + (tư thế thân) -> IK -> JointFrame. Trả về false nếu có chân không với tới.
class MotionCoordinator {
public:
    MotionCoordinator(const Hexapod& hexapod, const BodyKinematics& bodyKin)
        : hexapod_(hexapod), bodyKin_(bodyKin) {}

    bool compute(const Vec3 footOffsets[kNumLegs], const BodyPose& pose, JointFrame& out) const {
        Vec3 feet[kNumLegs], targets[kNumLegs];
        for (int i = 0; i < kNumLegs; ++i) feet[i] = hexapod_.leg(i).neutralFoot() + footOffsets[i];
        bodyKin_.legTargets(pose, feet, targets);
        bool reachable = true;
        for (int i = 0; i < kNumLegs; ++i) {
            const IKResult r = hexapod_.leg(i).kinematics().inverse(targets[i]);
            reachable = reachable && r.reachable;
            out.set(i, 0, rad2deg(r.t1));
            out.set(i, 1, rad2deg(r.t2));
            out.set(i, 2, rad2deg(r.t3));
        }
        return reachable;
    }

private:
    const Hexapod& hexapod_;
    const BodyKinematics& bodyKin_;
};

}  // namespace hexapod
