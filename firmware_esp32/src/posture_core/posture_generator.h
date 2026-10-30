#pragma once
#include "../../include/generated_config.h"
#include "../common/types.h"
#include "posture.h"

namespace hexapod {

// Nội suy mượt tư thế thân về tư thế đích (giới hạn tốc độ từng bậc tự do).
class PostureGenerator {
public:
    PostureGenerator()
        : elevation_(cfg::kZMin, cfg::kZMax), roll_(-cfg::kRollLimit, cfg::kRollLimit),
          pitch_(-cfg::kPitchLimit, cfg::kPitchLimit), yaw_(-cfg::kYawLimit, cfg::kYawLimit) {}

    const BodyPose& current() const { return current_; }
    const BodyPose& target() const { return target_; }
    bool walking() const { return walking_; }
    void setWalking(bool w) { walking_ = w; }     // true: tư thế đích bị kẹp vào vùng cho phép khi bước
    bool reached() const { return current_ == effectiveTarget(); }
    bool inWalkingEnvelope() const;

    // nullptr nếu hợp lệ, ngược lại là tên bậc tự do vượt giới hạn.
    const char* validate(float z, float roll, float pitch, float yaw) const;
    BodyPose compose(float z, float roll, float pitch, float yaw) const;
    void setTarget(const BodyPose& pose) { target_ = pose; }
    void reset(const BodyPose& pose) { current_ = target_ = pose; walking_ = false; }
    const BodyPose& update(float dt);

private:
    Elevation elevation_;
    Roll roll_;
    Pitch pitch_;
    Yaw yaw_;
    bool walking_ = false;
    BodyPose current_, target_;

    BodyPose effectiveTarget() const;
};

}  // namespace hexapod
