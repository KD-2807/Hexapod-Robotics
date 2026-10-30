#pragma once
#include "../common/types.h"
#include "hexapod.h"

namespace hexapod {

struct SafetyResult {
    bool ok = true;
    JointFrame frame;
    char reason[72] = {0};
};

// Kiểm tra JointFrame (NaN, giới hạn góc, tốc độ) trước khi xuất ra servo.
class SafetyGuard {
public:
    explicit SafetyGuard(const Hexapod& hexapod) : hexapod_(hexapod) {}
    void reset(const JointFrame& frame) { previous_ = frame; hasPrevious_ = true; }
    void clear() { hasPrevious_ = false; }
    void filter(const JointFrame& frame, float dt, SafetyResult& out);

private:
    const Hexapod& hexapod_;
    JointFrame previous_;
    bool hasPrevious_ = false;
};

}  // namespace hexapod
