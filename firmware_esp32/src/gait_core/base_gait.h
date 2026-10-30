#pragma once
#include "../../include/generated_config.h"
#include "../common/enums.h"
#include "../common/math_utils.h"
#include "../common/types.h"
#include "../robot_core/hexapod.h"
#include "gait_phase.h"
#include "trajectory.h"

namespace hexapod {

// Khung chung của mọi dáng đi. Lớp con chỉ khai báo loại dáng đi (và hiệu chỉnh vận tốc nếu cần).
class BaseGait {
public:
    BaseGait(GaitType type, const Hexapod& hexapod) : type_(type), hexapod_(hexapod) {
        profile_ = &cfg::kGaits[static_cast<int>(type)];
        cycleTimeS_ = profile_->cycleTimeS;
        phase_.init(*profile_);
    }
    virtual ~BaseGait() {}

    GaitType type() const { return type_; }
    void reset() { t_ = 0.0f; }
    void advance(float dt, float speed) { t_ = fmodf(t_ + dt * speed / cycleTimeS_, 1.0f); }
    float phaseT() const { return t_; }
    void setPhaseT(float t) { t_ = t; }

    virtual Velocity shapeVelocity(const Velocity& v) const { return v; }
    Vec3 strideFor(const Leg& leg, const Velocity& v) const;
    void footOffsets(const Velocity& v, Vec3 out[kNumLegs]) const;

private:
    GaitType type_;
    const Hexapod& hexapod_;
    const cfg::GaitProfile* profile_;
    float cycleTimeS_;
    GaitPhase phase_;
    float t_ = 0.0f;
};

class TripodGait : public BaseGait {          // 3 chân nhấc / 3 chân chống luân phiên
public:
    explicit TripodGait(const Hexapod& h) : BaseGait(GaitType::Tripod, h) {}
};

class WaveGait : public BaseGait {            // mỗi lần nhấc 1 chân (luôn 5 chân chạm đất)
public:
    explicit WaveGait(const Hexapod& h) : BaseGait(GaitType::Wave, h) {}
};

class RippleGait : public BaseGait {          // mỗi lần nhấc 2 chân lệch pha (luôn 4 chân chạm đất)
public:
    explicit RippleGait(const Hexapod& h) : BaseGait(GaitType::Ripple, h) {}
};

class RotationGait : public BaseGait {        // bước theo cung tròn quanh tâm thân: chỉ dùng wz
public:
    explicit RotationGait(const Hexapod& h) : BaseGait(GaitType::Rotation, h) {}
    Velocity shapeVelocity(const Velocity& v) const override { return Velocity(0.0f, 0.0f, v.wz); }
};

// Sở hữu 4 đối tượng dáng đi (không cấp phát động); pha của mỗi dáng được giữ giữa các lần dùng.
class GaitFactory {
public:
    explicit GaitFactory(const Hexapod& h) : tripod_(h), wave_(h), ripple_(h), rotation_(h) {}
    BaseGait& get(GaitType type) {
        switch (type) {
            case GaitType::Wave: return wave_;
            case GaitType::Ripple: return ripple_;
            case GaitType::Rotation: return rotation_;
            default: return tripod_;
        }
    }

private:
    TripodGait tripod_;
    WaveGait wave_;
    RippleGait ripple_;
    RotationGait rotation_;
};

}  // namespace hexapod
