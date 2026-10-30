#pragma once
#include "../common/math_utils.h"

namespace hexapod {

struct IKResult {
    float t1, t2, t3;     // coxa, femur, tibia (radian)
    bool reachable;
};

// Động học thuận/nghịch 1 chân 3 khớp. Hệ chân: gốc tại trục coxa, X ra ngoài, Z lên.
class LegKinematics {
public:
    LegKinematics() : l1_(0), l2_(0), l3_(0) {}
    LegKinematics(float coxa, float femur, float tibia) : l1_(coxa), l2_(femur), l3_(tibia) {}
    Vec3 forward(float t1, float t2, float t3) const;
    IKResult inverse(const Vec3& p) const;

private:
    float l1_, l2_, l3_;
};

}  // namespace hexapod
