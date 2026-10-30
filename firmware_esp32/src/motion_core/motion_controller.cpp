#include "motion_controller.h"

#include <stdio.h>
#include <string.h>

namespace hexapod {

namespace {
const Velocity kZero;
constexpr float kSpeedMin = 0.1f, kSpeedMax = 1.0f;
}  // namespace

MotionController::MotionController(const Hexapod& hexapod, const MotionCoordinator& coordinator, SafetyGuard& guard,
                                   ActuatorBackend& backend, PostureGenerator& posture, GaitFactory& gaits)
    : hexapod_(hexapod), coordinator_(coordinator), guard_(guard), backend_(backend),
      ctx_{posture, gaits, BodyPose(), BodyPose(), cfg::kDefaultSpeed, static_cast<GaitType>(cfg::kDefaultGait), Velocity()},
      hold_(ctx_), walk_(ctx_), strafe_(ctx_), turn_(ctx_), standUp_(ctx_), sitDown_(ctx_),
      wave_(ctx_), bob_(ctx_), dance_(ctx_), action_(&hold_),
      requestedGait_(static_cast<GaitType>(cfg::kDefaultGait)) {
    ctx_.sitPose.z = -(cfg::kStandHeight - cfg::kSitHeight);
}

// ------------------------------------------------------------------ lệnh
Result MotionController::enable() {
    Result r = machine_.require(CommandType::Enable);
    if (!r.ok()) return r;
    if (state() != RobotState::Idle) return Result::success();
    if (!backend_.enable()) return Result::fail(ErrorCode::Hardware, "Không bật được driver servo");
    ctx_.posture.reset(ctx_.sitPose);
    ctx_.velocity = kZero;
    desired_ = kZero;
    Vec3 zeros[kNumLegs];
    JointFrame first;
    coordinator_.compute(zeros, ctx_.sitPose, first);
    guard_.reset(first);
    if (!backend_.apply(first)) return Result::fail(ErrorCode::Hardware, "Không ghi được servo");
    frame_ = first;
    machine_.transition(RobotState::Sitting);
    start(&sitDown_);
    return Result::success();
}

Result MotionController::disable() {
    Result r = machine_.require(CommandType::Disable);
    if (!r.ok()) return r;
    if (state() == RobotState::Idle) return Result::success();
    if (!(action_->kind() == ActionKind::SitDown && action_->finished())) {
        return Result::fail(ErrorCode::BadState, "Cần ngồi xuống xong trước khi tắt servo");
    }
    backend_.disable();
    manual_ = false;
    return machine_.transition(RobotState::Idle);
}

Result MotionController::standUp() {
    Result r = machine_.require(CommandType::StandUp);
    if (!r.ok()) return r;
    if (state() == RobotState::Idle) {
        r = enable();
        if (!r.ok()) return r;
    }
    if (state() == RobotState::Standing || action_->kind() == ActionKind::StandUp) return Result::success();
    manual_ = false;
    pendingSit_ = false;
    ctx_.posture.setWalking(false);
    start(&standUp_);
    return Result::success();
}

Result MotionController::sitDown() {
    Result r = machine_.require(CommandType::SitDown);
    if (!r.ok()) return r;
    desired_ = kZero;
    if (state() == RobotState::Walking) pendingSit_ = true;        // dừng hẳn rồi mới ngồi
    else if (state() == RobotState::Standing) beginSit();
    return Result::success();
}

Result MotionController::move(float vx, float vy, float wz, bool hasSpeed, float speed) {
    Result r = machine_.require(CommandType::Move);
    if (!r.ok()) return r;
    if (!(vx >= -1.0f && vx <= 1.0f)) return Result::fail(ErrorCode::BadParams, "vx phải trong [-1, 1]");
    if (!(vy >= -1.0f && vy <= 1.0f)) return Result::fail(ErrorCode::BadParams, "vy phải trong [-1, 1]");
    if (!(wz >= -1.0f && wz <= 1.0f)) return Result::fail(ErrorCode::BadParams, "wz phải trong [-1, 1]");
    if (hasSpeed) {
        r = setSpeed(speed);
        if (!r.ok()) return r;
    }
    if (busyWithSpecial()) return Result::fail(ErrorCode::BadState, "Đang chạy action đặc biệt, hãy STOP trước");
    desired_ = Velocity(vx, vy, wz);
    pendingSit_ = false;
    return Result::success();
}

Result MotionController::stop() {
    Result r = machine_.require(CommandType::Stop);
    if (!r.ok()) return r;
    desired_ = kZero;
    if (busyWithSpecial()) start(&hold_);
    return Result::success();
}

Result MotionController::setGait(GaitType gait) {
    Result r = machine_.require(CommandType::SetGait);
    if (!r.ok()) return r;
    if (gait == GaitType::Rotation) return Result::fail(ErrorCode::BadParams, "Dáng đi phải là tripod/wave/ripple");
    requestedGait_ = gait;
    applyRequestedGait();
    return Result::success();
}

Result MotionController::setSpeed(float speed) {
    Result r = machine_.require(CommandType::SetSpeed);
    if (!r.ok()) return r;
    if (!(speed >= kSpeedMin && speed <= kSpeedMax)) {
        return Result::fail(ErrorCode::BadParams, "speed phải trong [0.1, 1.0]");
    }
    ctx_.speed = speed;
    return Result::success();
}

Result MotionController::setPose(float z, float roll, float pitch, float yaw) {
    Result r = machine_.require(CommandType::SetPose);
    if (!r.ok()) return r;
    const char* bad = ctx_.posture.validate(z, roll, pitch, yaw);
    if (bad) {
        snprintf(msg_, sizeof(msg_), "%s vượt giới hạn cho phép", bad);
        return Result::fail(ErrorCode::BadParams, msg_);
    }
    const BodyPose pose = ctx_.posture.compose(z, roll, pitch, yaw);
    if (!poseFeasible(pose)) return Result::fail(ErrorCode::Limit, "Tổ hợp tư thế vượt tầm với của chân");
    ctx_.posture.setTarget(pose);
    return Result::success();
}

SpecialAction* MotionController::findSpecial(const char* name) {
    SpecialAction* all[] = {&wave_, &bob_, &dance_};
    for (SpecialAction* s : all) if (strcmp(s->name(), name) == 0) return s;
    return nullptr;
}

Result MotionController::runAction(const char* name) {
    Result r = machine_.require(CommandType::Action);
    if (!r.ok()) return r;
    SpecialAction* special = findSpecial(name);
    if (!special) return Result::fail(ErrorCode::BadParams, "Action không tồn tại");
    if (busyWithSpecial() || state() != RobotState::Standing) {
        return Result::fail(ErrorCode::BadState, "Chỉ chạy action khi đang đứng yên");
    }
    start(special);
    return Result::success();
}

void MotionController::emergencyStop() {
    backend_.disable();
    fail(ErrorCode::EStop, "Dừng khẩn cấp");
}

Result MotionController::reset() {
    Result r = machine_.require(CommandType::Reset);
    if (!r.ok()) return r;
    if (state() == RobotState::Error) machine_.transition(RobotState::Idle);
    error_ = ErrorInfo();
    manual_ = false;
    desired_ = kZero;
    ctx_.velocity = kZero;
    pendingSit_ = false;
    start(&hold_);
    return Result::success();
}

Result MotionController::setServo(int leg, int joint, float angle, bool raw) {
    Result r = machine_.require(CommandType::SetServo);
    if (!r.ok()) return r;
    if (leg < 0 || leg >= kNumLegs || joint < 0 || joint >= kJointsPerLeg) {
        return Result::fail(ErrorCode::BadParams, "leg phải 0..5, joint phải 0..2");
    }
    bool ok;
    if (raw) {
        if (!(angle >= 0.0f && angle <= 180.0f)) return Result::fail(ErrorCode::BadParams, "góc servo phải trong [0, 180]");
        ok = backend_.applyRawServo(leg, joint, angle);
    } else {
        const Joint& j = hexapod_.leg(leg).joint(joint);
        if (!(angle >= j.minDeg && angle <= j.maxDeg)) {
            snprintf(msg_, sizeof(msg_), "góc khớp phải trong [%.0f, %.0f]", j.minDeg, j.maxDeg);
            return Result::fail(ErrorCode::BadParams, msg_);
        }
        JointFrame f = frame_;
        f.set(leg, joint, angle);
        ok = backend_.apply(f);
        if (ok) frame_ = f;
    }
    if (!ok) return Result::fail(ErrorCode::Hardware, "Ghi servo thất bại");
    manual_ = true;
    return Result::success();
}

void MotionController::onLinkLost() {
    desired_ = kZero;
    if (busyWithSpecial()) start(&hold_);
    if (state() == RobotState::Standing || state() == RobotState::Walking) pendingSit_ = true;
}

// ------------------------------------------------------------------ vòng điều khiển
void MotionController::update(float dt) {
    if (state() == RobotState::Idle || state() == RobotState::Error || manual_) return;
    updateLocomotion(dt);
    ActionOutput out;
    action_->update(dt, out);
    JointFrame raw;
    const bool reachable = coordinator_.compute(out.footOffsets, out.pose, raw);
    SafetyResult safe;
    guard_.filter(raw, dt, safe);
    if (!reachable) return fail(ErrorCode::Limit, "Bàn chân ngoài tầm với của chân");
    if (!safe.ok) return fail(ErrorCode::Limit, safe.reason);
    if (!backend_.apply(safe.frame)) return fail(ErrorCode::Hardware, "Lỗi I2C khi ghi servo");
    frame_ = safe.frame;
    finishTransitions();
}

// ------------------------------------------------------------------ nội bộ
void MotionController::beginSit() {
    pendingSit_ = false;
    ctx_.posture.setWalking(false);
    machine_.transition(RobotState::Sitting);
    start(&sitDown_);
}

void MotionController::applyRequestedGait() {
    if (state() != RobotState::Walking && requestedGait_ != ctx_.gaitType) {
        ctx_.gaitType = requestedGait_;
        ctx_.gaits.get(requestedGait_).reset();
    }
}

bool MotionController::poseFeasible(const BodyPose& pose) const {
    Vec3 zeros[kNumLegs];
    JointFrame f;
    if (!coordinator_.compute(zeros, pose, f)) return false;
    const float m = cfg::kPoseCheckMarginDeg;
    for (int l = 0; l < kNumLegs; ++l) {
        for (int j = 0; j < kJointsPerLeg; ++j) {
            const Joint& joint = hexapod_.leg(l).joint(j);
            const float a = f.get(l, j);
            if (!(joint.minDeg + m <= a && a <= joint.maxDeg - m)) return false;
        }
    }
    return true;
}

MotionController::Family MotionController::familyOf(const Velocity& v) {
    if (v.isZero()) return Family::None;
    return (fabsf(v.vx) < 1e-3f && fabsf(v.vy) < 1e-3f) ? Family::Turn : Family::Translate;
}

BaseAction* MotionController::actionFor(const Velocity& v) {
    if (familyOf(v) == Family::Turn) return &turn_;
    if (fabsf(v.vy) < 1e-3f && fabsf(v.wz) < 1e-3f) return &strafe_;
    return &walk_;
}

Velocity MotionController::ramp(const Velocity& cur, const Velocity& target, float dt) const {
    const float step = cfg::kVelocityRampPerS * dt;
    return Velocity(moveTowards(cur.vx, target.vx, step), moveTowards(cur.vy, target.vy, step),
                    moveTowards(cur.wz, target.wz, step));
}

void MotionController::updateLocomotion(float dt) {
    if (state() != RobotState::Standing && state() != RobotState::Walking) return;
    if (pendingSit_ && ctx_.velocity.isZero()) return beginSit();
    if (state() == RobotState::Standing) applyRequestedGait();

    const Family active = familyOf(ctx_.velocity), wanted = familyOf(desired_);
    const bool switching = active != Family::None && wanted != Family::None && active != wanted;
    const bool wantWalk = !desired_.isZero() || !ctx_.velocity.isZero();
    ctx_.posture.setWalking(wantWalk);
    const bool hold = switching || pendingSit_ || busyWithSpecial() || (wantWalk && !ctx_.posture.inWalkingEnvelope());
    const Velocity target = hold ? kZero : desired_;
    ctx_.velocity = ramp(ctx_.velocity, target, dt);

    const bool moving = !ctx_.velocity.isZero() || !target.isZero();
    if (ctx_.velocity.isZero() && desired_.isZero()) ctx_.posture.setWalking(false);
    if (moving) {
        if (state() == RobotState::Standing) machine_.transition(RobotState::Walking);
        action_ = actionFor(ctx_.velocity.isZero() ? target : ctx_.velocity);
    } else if (state() == RobotState::Walking) {
        machine_.transition(RobotState::Standing);
        start(&hold_);
    }
}

void MotionController::finishTransitions() {
    if (state() == RobotState::Sitting && action_->kind() == ActionKind::StandUp && action_->finished()) {
        machine_.transition(RobotState::Standing);
        start(&hold_);
    } else if (busyWithSpecial() && action_->finished()) {
        start(&hold_);
    }
}

void MotionController::fail(ErrorCode code, const char* message) {
    machine_.fail();
    error_.active = true;
    error_.code = code;
    snprintf(error_.message, sizeof(error_.message), "%s", message);
    desired_ = kZero;
    ctx_.velocity = kZero;
    pendingSit_ = false;
    manual_ = false;
    ctx_.posture.setWalking(false);
    backend_.disable();
}

}  // namespace hexapod
