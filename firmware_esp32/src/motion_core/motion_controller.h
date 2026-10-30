#pragma once
#include "../common/enums.h"
#include "../common/types.h"
#include "../interfaces/actuator_backend.h"
#include "../robot_core/motion_coordinator.h"
#include "../robot_core/safety_guard.h"
#include "actions.h"
#include "state_machine.h"

namespace hexapod {

struct ErrorInfo {
    bool active = false;
    ErrorCode code = ErrorCode::None;
    char message[72] = {0};
};

// Nhận lệnh cấp cao, chọn action/gait, mỗi chu kỳ tạo JointFrame và đưa xuống backend.
// Mọi lệnh trả về Result (không dùng exception).
class MotionController {
public:
    MotionController(const Hexapod& hexapod, const MotionCoordinator& coordinator, SafetyGuard& guard,
                     ActuatorBackend& backend, PostureGenerator& posture, GaitFactory& gaits);

    // ---- trạng thái
    RobotState state() const { return machine_.state(); }
    GaitType gait() const { return requestedGait_; }
    float speed() const { return ctx_.speed; }
    const BodyPose& pose() const { return ctx_.posture.current(); }
    const JointFrame& frame() const { return frame_; }
    const ErrorInfo& error() const { return error_; }
    bool accepts(CommandType c) const { return machine_.accepts(c); }
    const Velocity& smoothedVelocity() const { return ctx_.velocity; }

    // ---- lệnh
    Result enable();
    Result disable();
    Result standUp();
    Result sitDown();
    Result move(float vx, float vy, float wz, bool hasSpeed, float speed);
    Result stop();
    Result setGait(GaitType gait);
    Result setSpeed(float speed);
    Result setPose(float z, float roll, float pitch, float yaw);
    Result runAction(const char* name);
    Result setServo(int leg, int joint, float angle, bool raw);
    void emergencyStop();
    Result reset();
    void onLinkLost();                  // mất heartbeat/kết nối: dừng rồi ngồi xuống

    // ---- vòng điều khiển
    void update(float dt);

private:
    enum class Family { None, Turn, Translate };

    const Hexapod& hexapod_;
    const MotionCoordinator& coordinator_;
    SafetyGuard& guard_;
    ActuatorBackend& backend_;
    MotionContext ctx_;
    StateMachine machine_;

    BodyPoseAction hold_;
    Walk walk_;
    Strafe strafe_;
    Turn turn_;
    StandUp standUp_;
    SitDown sitDown_;
    WaveAction wave_;
    BobAction bob_;
    DanceAction dance_;
    BaseAction* action_;

    Velocity desired_;
    bool pendingSit_ = false;
    GaitType requestedGait_;
    bool manual_ = false;
    JointFrame frame_;
    ErrorInfo error_;
    char msg_[80] = {0};

    void start(BaseAction* action) { action_ = action; action_->start(); }
    bool busyWithSpecial() const { return action_->kind() == ActionKind::Special; }
    void beginSit();
    void applyRequestedGait();
    bool poseFeasible(const BodyPose& pose) const;
    static Family familyOf(const Velocity& v);
    BaseAction* actionFor(const Velocity& v);
    void updateLocomotion(float dt);
    Velocity ramp(const Velocity& cur, const Velocity& target, float dt) const;
    void finishTransitions();
    void fail(ErrorCode code, const char* message);
    SpecialAction* findSpecial(const char* name);
};

}  // namespace hexapod
