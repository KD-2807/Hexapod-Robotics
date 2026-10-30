#pragma once
#include <math.h>

#include "../../include/generated_config.h"
#include "../common/math_utils.h"
#include "../common/types.h"
#include "../gait_core/base_gait.h"
#include "../posture_core/posture_generator.h"

namespace hexapod {

// Trạng thái dùng chung giữa MotionController và các action.
struct MotionContext {
    PostureGenerator& posture;
    GaitFactory& gaits;
    BodyPose standPose;
    BodyPose sitPose;
    float speed;
    GaitType gaitType;
    Velocity velocity;          // vận tốc đã làm mượt
};

struct ActionOutput {
    Vec3 footOffsets[kNumLegs];
    BodyPose pose;
};

enum class ActionKind { BodyPose, StandUp, SitDown, Walk, Strafe, Turn, Special };

// Một hành vi cấp cao; mỗi chu kỳ trả về độ dịch bàn chân + tư thế thân.
class BaseAction {
public:
    explicit BaseAction(MotionContext& ctx) : ctx_(ctx) {}
    virtual ~BaseAction() {}
    virtual ActionKind kind() const = 0;
    virtual void start() {}
    virtual void update(float dt, ActionOutput& out) = 0;
    virtual bool finished() const { return false; }

protected:
    MotionContext& ctx_;
    void zeroOffsets(ActionOutput& out) const { for (int i = 0; i < kNumLegs; ++i) out.footOffsets[i] = Vec3(); }
};

// Giữ các chân; thân nội suy mượt về tư thế đích.
class BodyPoseAction : public BaseAction {
public:
    using BaseAction::BaseAction;
    ActionKind kind() const override { return ActionKind::BodyPose; }
    void update(float dt, ActionOutput& out) override { zeroOffsets(out); out.pose = ctx_.posture.update(dt); }
};

class StandUp : public BaseAction {
public:
    using BaseAction::BaseAction;
    ActionKind kind() const override { return ActionKind::StandUp; }
    void start() override { ctx_.posture.setTarget(ctx_.standPose); }
    void update(float dt, ActionOutput& out) override { zeroOffsets(out); out.pose = ctx_.posture.update(dt); }
    bool finished() const override { return ctx_.posture.reached(); }
};

class SitDown : public BaseAction {
public:
    using BaseAction::BaseAction;
    ActionKind kind() const override { return ActionKind::SitDown; }
    void start() override { ctx_.posture.setTarget(ctx_.sitPose); }
    void update(float dt, ActionOutput& out) override { zeroOffsets(out); out.pose = ctx_.posture.update(dt); }
    bool finished() const override { return ctx_.posture.reached(); }
};

// Đi tiến/lùi (kèm đi chéo, vòng cung) bằng dáng đi đang chọn.
class Walk : public BaseAction {
public:
    using BaseAction::BaseAction;
    ActionKind kind() const override { return ActionKind::Walk; }
    void update(float dt, ActionOutput& out) override;

protected:
    virtual Velocity shape(const Velocity& v) const { return v; }
    virtual BaseGait& gait() { return ctx_.gaits.get(ctx_.gaitType); }
};

class Strafe : public Walk {         // đi ngang: chỉ dùng vx
public:
    using Walk::Walk;
    ActionKind kind() const override { return ActionKind::Strafe; }

protected:
    Velocity shape(const Velocity& v) const override { return Velocity(v.vx, 0.0f, 0.0f); }
};

class Turn : public Walk {           // xoay tại chỗ bằng RotationGait: chỉ dùng wz
public:
    using Walk::Walk;
    ActionKind kind() const override { return ActionKind::Turn; }

protected:
    Velocity shape(const Velocity& v) const override { return Velocity(0.0f, 0.0f, v.wz); }
    BaseGait& gait() override { return ctx_.gaits.get(GaitType::Rotation); }
};

// Hành động đặc biệt theo thời gian: cộng độ lệch (có bao đóng vào/ra) lên tư thế đang giữ.
class SpecialAction : public BaseAction {
public:
    SpecialAction(MotionContext& ctx, const char* name, float duration)
        : BaseAction(ctx), name_(name), duration_(duration) {}
    const char* name() const { return name_; }
    ActionKind kind() const override { return ActionKind::Special; }
    void start() override { t_ = 0.0f; }
    bool finished() const override { return t_ >= duration_; }
    void update(float dt, ActionOutput& out) override;

protected:
    virtual void deltaPose(float t, float env, BodyPose& delta) const = 0;
    virtual void footOffsets(float t, float env, ActionOutput& out) const { zeroOffsets(out); (void)t; (void)env; }

private:
    const char* name_;
    float duration_;
    float t_ = 0.0f;
    static constexpr float kRamp = 0.5f;
};

class WaveAction : public SpecialAction {          // chào: cúi người, nhấc chân trước bên phải và vẫy
public:
    explicit WaveAction(MotionContext& c) : SpecialAction(c, "wave", 4.0f) {}

protected:
    void deltaPose(float t, float env, BodyPose& d) const override;
    void footOffsets(float t, float env, ActionOutput& out) const override;
};

class BobAction : public SpecialAction {           // nhún
public:
    explicit BobAction(MotionContext& c) : SpecialAction(c, "bob", 3.0f) {}

protected:
    void deltaPose(float t, float env, BodyPose& d) const override;
};

class DanceAction : public SpecialAction {         // múa
public:
    explicit DanceAction(MotionContext& c) : SpecialAction(c, "dance", 6.0f) {}

protected:
    void deltaPose(float t, float env, BodyPose& d) const override;
};

}  // namespace hexapod
