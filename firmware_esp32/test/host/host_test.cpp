// Test firmware trên PC: unit test + kịch bản đối chiếu với bản Python.
#include <math.h>
#include <stdio.h>
#include <string.h>

#include <string>
#include <vector>

#include "app/command_handler.h"
#include "app/robot_app.h"
#include "app/sensor_hub.h"
#include "app/status_reporter.h"
#include "app/watchdog.h"
#include "common/command_codec.h"
#include "common/json_mini.h"
#include "hardware/pca9685_backend.h"
#include "motion_core/motion_controller.h"

using namespace hexapod;

// ------------------------------------------------------------------ khung test
static int gFailures = 0, gChecks = 0;
#define CHECK(cond) do { ++gChecks; if (!(cond)) { ++gFailures; printf("  FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); } } while (0)
#define CHECK_NEAR(a, b, tol) do { ++gChecks; const double va = (a), vb = (b); if (fabs(va - vb) > (tol)) { ++gFailures; \
    printf("  FAIL %s:%d  %s ~ %s  (%.6f vs %.6f)\n", __FILE__, __LINE__, #a, #b, va, vb); } } while (0)
#define CHECK_STR(a, b) do { ++gChecks; if (strcmp((a), (b)) != 0) { ++gFailures; \
    printf("  FAIL %s:%d\n    got:  %s\n    want: %s\n", __FILE__, __LINE__, (a), (b)); } } while (0)
#define TEST(name) static void name(); static struct name##_reg { name##_reg() { registry().push_back({#name, name}); } } name##_instance; static void name()

struct TestCase { const char* name; void (*fn)(); };
static std::vector<TestCase>& registry() { static std::vector<TestCase> r; return r; }

// ------------------------------------------------------------------ đối tượng giả
class FakeBackend : public ActuatorBackend {
public:
    bool enabled = false, failNext = false;
    JointFrame last;
    float rawServo[kNumServos];
    FakeBackend() { for (int i = 0; i < kNumServos; ++i) rawServo[i] = -1.0f; }
    bool enable() override { enabled = true; return true; }
    void disable() override { enabled = false; }
    bool apply(const JointFrame& f) override {
        if (!enabled || failNext) { failNext = false; return false; }
        last = f;
        return true;
    }
    bool applyRawServo(int leg, int joint, float deg) override {
        if (!enabled) return false;
        rawServo[leg * kJointsPerLeg + joint] = deg;
        return true;
    }
};

struct WriteRecord { uint8_t address; std::vector<uint8_t> bytes; };

class FakeI2C : public I2CBus {
public:
    std::vector<WriteRecord> writes;
    bool failWrites = false;
    uint8_t regs[16];                     // dữ liệu trả về cho readRegister
    FakeI2C() { memset(regs, 0, sizeof(regs)); }
    bool write(uint8_t a, const uint8_t* d, size_t n) override {
        if (failWrites) return false;
        writes.push_back({a, std::vector<uint8_t>(d, d + n)});
        return true;
    }
    bool readRegister(uint8_t, uint8_t, uint8_t* out, size_t n) override { memcpy(out, regs, n < 16 ? n : 16); return true; }
    bool probe(uint8_t) override { return true; }
};

class FakeClock : public Clock {
public:
    uint32_t millis() override { return 0; }
    uint32_t micros() override { return 0; }
    void delayMs(uint32_t) override {}
};

class FakeTransport : public Transport {
public:
    std::vector<std::string> incoming, sent;
    bool connected = true, dropped = false;
    bool begin() override { return true; }
    void poll() override {}
    bool readLine(char* b, size_t cap) override {
        if (incoming.empty()) return false;
        snprintf(b, cap, "%s", incoming.front().c_str());
        incoming.erase(incoming.begin());
        return true;
    }
    void sendLine(const char* l) override { sent.push_back(l); }
    bool isConnected() const override { return connected; }
    bool takeDisconnectEvent() override { const bool d = dropped; dropped = false; return d; }
};

// Bộ dựng lõi điều khiển + backend tùy chọn (giống main.cpp).
struct Rig {
    Hexapod hexapod;
    BodyKinematics bodyKin;
    MotionCoordinator coordinator;
    SafetyGuard guard;
    PostureGenerator posture;
    GaitFactory gaits;
    FakeBackend backend;
    MotionController mc;
    Rig() : bodyKin(hexapod), coordinator(hexapod, bodyKin), guard(hexapod), gaits(hexapod),
            mc(hexapod, coordinator, guard, backend, posture, gaits) {}
    void run(float seconds) { const int n = static_cast<int>(floorf(seconds / 0.02f + 0.5f)); for (int i = 0; i < n; ++i) mc.update(0.02f); }
    void standUpFully() { CHECK(mc.standUp().ok()); run(1.6f); }
};

// ------------------------------------------------------------------ JSON / codec
TEST(json_reader_parses_command) {
    JsonReader r;
    CHECK(r.parse("{\"seq\":7,\"cmd\":\"MOVE\",\"params\":{\"vx\":0.5,\"vy\":-1,\"speed\":0.8,\"raw\":true}}"));
    float v = 0; const char* s = nullptr; bool b = false;
    CHECK(r.getNumber("seq", v)); CHECK_NEAR(v, 7, 1e-6);
    CHECK(r.getString("cmd", s)); CHECK_STR(s, "MOVE");
    CHECK(r.getNumber("params.vx", v)); CHECK_NEAR(v, 0.5, 1e-6);
    CHECK(r.getNumber("params.vy", v)); CHECK_NEAR(v, -1, 1e-6);
    CHECK(r.getBool("params.raw", b)); CHECK(b);
    CHECK(!r.has("params.wz"));
    CHECK(!r.getNumber("cmd", v));                          // sai kiểu
}

TEST(json_reader_rejects_bad_input) {
    JsonReader r;
    const char* bad[] = {"", "not json", "{", "{\"a\":}", "{\"a\":1,}", "{\"a\":[1]}", "{\"a\":1} trailing",
                         "{\"a\":{\"b\":{\"c\":1}}}", "{\"seq\":\"unterminated}"};
    for (const char* text : bad) CHECK(!r.parse(text));
    CHECK(r.parse("  { \"a\" : 1 ,\n \"b\" : \"x\\\"y\" }  "));          // khoảng trắng + escape
    const char* s = nullptr;
    CHECK(r.getString("b", s)); CHECK_STR(s, "x\"y");
}

TEST(json_writer_matches_python_format) {
    char buf[200];
    CHECK(encodeAck(buf, sizeof(buf), 1) > 0);
    CHECK_STR(buf, "{\"seq\":1,\"type\":\"ACK\",\"data\":{}}");
    encodeError(buf, sizeof(buf), 4, ErrorCode::BadState, "x\"y");
    CHECK_STR(buf, "{\"seq\":4,\"type\":\"ERROR\",\"data\":{\"code\":\"BAD_STATE\",\"message\":\"x\\\"y\"}}");
    JsonWriter w(buf, sizeof(buf));
    w.beginObject().key("a").beginArray().number(1.25f).number(-0.04f).endArray().key("n").null().key("t").boolean(true).endObject();
    CHECK_STR(buf, "{\"a\":[1.2,-0.0],\"n\":null,\"t\":true}");
}

TEST(json_writer_reports_overflow) {
    char tiny[16];
    JsonWriter w(tiny, sizeof(tiny));
    w.beginObject().key("a_long_key_here").string("a long value that does not fit").endObject();
    CHECK(!w.ok());
}

TEST(codec_decode_cases) {
    JsonReader r;
    Command c;
    DecodeStatus st = decodeCommand("{\"seq\":2,\"cmd\":\"STOP\"}", r, c);
    CHECK(st.ok()); CHECK(c.type == CommandType::Stop); CHECK(c.seq == 2);
    st = decodeCommand("not json", r, c);                CHECK(st.code == ErrorCode::BadFormat);
    st = decodeCommand("{\"cmd\":\"MOVE\"}", r, c);      CHECK(st.code == ErrorCode::BadFormat);
    st = decodeCommand("{\"seq\":1,\"cmd\":\"FLY\"}", r, c);
    CHECK(st.code == ErrorCode::BadCommand); CHECK(st.seq == 1);
    st = decodeCommand("{\"seq\":1,\"cmd\":\"MOVE\",\"params\":5}", r, c);   CHECK(st.code == ErrorCode::BadFormat);
    st = decodeCommand("{\"seq\":1.5,\"cmd\":\"MOVE\"}", r, c);              CHECK(st.code == ErrorCode::BadFormat);
}

// ------------------------------------------------------------------ động học & dáng đi
TEST(leg_ik_fk_roundtrip_and_limits) {
    LegKinematics k(54, 45, 77);
    const Vec3 targets[] = {Vec3(110, 0, -60), Vec3(120, 30, -50), Vec3(90, -20, -30), Vec3(100, 10, -75)};
    for (const Vec3& t : targets) {
        const IKResult r = k.inverse(t);
        CHECK(r.reachable);
        const Vec3 b = k.forward(r.t1, r.t2, r.t3);
        CHECK_NEAR(b.x, t.x, 1e-3); CHECK_NEAR(b.y, t.y, 1e-3); CHECK_NEAR(b.z, t.z, 1e-3);
    }
    IKResult far = k.inverse(Vec3(500, 0, -60));
    CHECK(!far.reachable); CHECK(isfinite(far.t1) && isfinite(far.t2) && isfinite(far.t3));
    IKResult near = k.inverse(Vec3(54, 0, -5));
    CHECK(!near.reachable); CHECK(isfinite(near.t2) && isfinite(near.t3));
}

TEST(gait_ground_contact_matches_report) {
    Hexapod hx;
    GaitFactory gaits(hx);
    const struct { GaitType type; int minOnGround; } cases[] = {{GaitType::Tripod, 3}, {GaitType::Wave, 5}, {GaitType::Ripple, 4}};
    for (const auto& c : cases) {
        BaseGait& g = gaits.get(c.type);
        int worst = 6;
        for (int k = 0; k < 1200; ++k) {
            g.setPhaseT((k + 0.5f) / 1200.0f);
            Vec3 o[kNumLegs];
            g.footOffsets(Velocity(0, 1, 0), o);
            int swinging = 0;
            for (int i = 0; i < kNumLegs; ++i) if (o[i].z > 1e-4f) ++swinging;
            if (6 - swinging < worst) worst = 6 - swinging;
        }
        CHECK(worst == c.minOnGround);
    }
}

TEST(gait_zero_velocity_zero_offsets_and_turn_is_tangential) {
    Hexapod hx;
    GaitFactory gaits(hx);
    BaseGait& g = gaits.get(GaitType::Tripod);
    for (int k = 0; k < 50; ++k) {
        g.advance(0.02f, 1.0f);
        Vec3 o[kNumLegs];
        g.footOffsets(Velocity(), o);
        for (int i = 0; i < kNumLegs; ++i) CHECK(o[i].x == 0 && o[i].y == 0 && o[i].z == 0);
    }
    for (int i = 0; i < kNumLegs; ++i) {
        const Vec3 s = g.strideFor(hx.leg(i), Velocity(0, 0, 1));
        const Vec3& f = hx.leg(i).neutralFoot();
        CHECK_NEAR(s.x * f.x + s.y * f.y, 0.0, 1e-2);
        CHECK(g.strideFor(hx.leg(i), Velocity(1, 1, 1)).normXY() <= cfg::kMaxStride + 1e-3f);
    }
}

TEST(posture_generator) {
    PostureGenerator p;
    CHECK(p.validate(0, 0, 0, 0) == nullptr);
    CHECK_STR(p.validate(100, 0, 0, 0), "z");
    CHECK_STR(p.validate(0, 0, 99, 0), "pitch");
    const BodyPose c = p.compose(100, -99, 99, -99);
    CHECK_NEAR(c.z, 30, 1e-6); CHECK_NEAR(c.roll, -15, 1e-6); CHECK_NEAR(c.pitch, 15, 1e-6); CHECK_NEAR(c.yaw, -20, 1e-6);
    BodyPose t; t.z = 20; t.roll = 10;
    p.setTarget(t);
    const BodyPose first = p.update(0.1f);
    CHECK_NEAR(first.z, 4.0, 1e-5); CHECK_NEAR(first.roll, 4.0, 1e-5);
    for (int i = 0; i < 20; ++i) p.update(0.1f);
    CHECK(p.reached());
}

TEST(state_machine_rules) {
    StateMachine m;
    CHECK(!m.accepts(CommandType::Move));
    CHECK(m.transition(RobotState::Sitting).ok());
    CHECK(m.transition(RobotState::Standing).ok());
    CHECK(m.accepts(CommandType::Move));
    CHECK(m.transition(RobotState::Walking).ok());
    CHECK(m.transition(RobotState::Standing).ok());
    CHECK(!m.transition(RobotState::Idle).ok());                       // Standing -> Idle không hợp lệ
    m.fail();
    CHECK(!m.accepts(CommandType::StandUp)); CHECK(!m.accepts(CommandType::SitDown)); CHECK(m.accepts(CommandType::Reset));
    CHECK(m.require(CommandType::StandUp).code == ErrorCode::BadState);
    for (int s = 0; s <= static_cast<int>(RobotState::Error); ++s) {
        m.forceState(static_cast<RobotState>(s));
        CHECK(m.accepts(CommandType::EmergencyStop)); CHECK(m.accepts(CommandType::Heartbeat));
    }
}

// ------------------------------------------------------------------ MotionController
TEST(controller_lifecycle) {
    Rig r;
    CHECK(r.mc.state() == RobotState::Idle);
    CHECK(r.mc.standUp().ok());                                        // IDLE: tự ENABLE
    CHECK(r.mc.state() == RobotState::Sitting); CHECK(r.backend.enabled);
    r.run(1.6f);
    CHECK(r.mc.state() == RobotState::Standing);
    CHECK(r.mc.move(0, 1, 0, false, 0).ok());
    r.run(0.3f);
    CHECK(r.mc.state() == RobotState::Walking);
    CHECK(r.mc.stop().ok());
    r.run(1.0f);
    CHECK(r.mc.state() == RobotState::Standing);
    CHECK(r.mc.sitDown().ok());
    r.run(1.6f);
    CHECK(r.mc.state() == RobotState::Sitting);
    CHECK(r.mc.disable().ok());
    CHECK(r.mc.state() == RobotState::Idle); CHECK(!r.backend.enabled);
}

TEST(controller_validation_and_errors) {
    Rig r;
    CHECK(r.mc.move(0, 1, 0, false, 0).code == ErrorCode::BadState);
    r.standUpFully();
    CHECK(r.mc.move(0, 1.5f, 0, false, 0).code == ErrorCode::BadParams);
    CHECK(r.mc.setSpeed(5.0f).code == ErrorCode::BadParams);
    CHECK(r.mc.setPose(99, 0, 0, 0).code == ErrorCode::BadParams);
    CHECK(r.mc.setPose(-25, 15, 15, 20).code == ErrorCode::Limit);     // từng trục hợp lệ, tổ hợp vượt tầm
    CHECK(r.mc.setPose(10, 5, -5, 10).ok());
    CHECK(r.mc.setGait(GaitType::Rotation).code == ErrorCode::BadParams);
    CHECK(r.mc.runAction("fly").code == ErrorCode::BadParams);
}

TEST(controller_all_gaits_and_motions_within_limits) {
    const GaitType gaits[] = {GaitType::Tripod, GaitType::Wave, GaitType::Ripple};
    const float motions[][3] = {{0, 1, 0}, {0, -1, 0}, {1, 0, 0}, {-1, 0, 0}, {1, 1, 0}, {0, 0, 1}, {0, 0, -1}, {0, 1, 1}, {-1, -1, -1}};
    for (GaitType g : gaits) {
        Rig r;
        r.standUpFully();
        CHECK(r.mc.setGait(g).ok());
        for (const auto& m : motions) {
            CHECK(r.mc.move(m[0], m[1], m[2], true, 1.0f).ok());
            r.run(5.0f);
            CHECK(r.mc.state() != RobotState::Error);
            r.mc.stop();
            r.run(1.5f);
        }
    }
}

TEST(controller_joint_speed_is_limited) {
    Rig r;
    r.standUpFully();
    r.mc.move(0, 1, 0.5f, true, 1.0f);
    JointFrame prev = r.mc.frame();
    for (int i = 0; i < 400; ++i) {
        r.mc.update(0.02f);
        CHECK(r.mc.frame().maxAbsDiff(prev) / 0.02f <= cfg::kMaxJointSpeedDps + 1e-2f);
        prev = r.mc.frame();
    }
}

TEST(controller_estop_hardware_error_and_link_lost) {
    {
        Rig r;
        r.standUpFully();
        r.mc.move(0, 1, 0, false, 0);
        r.run(0.5f);
        r.mc.emergencyStop();
        CHECK(r.mc.state() == RobotState::Error); CHECK(!r.backend.enabled);
        CHECK(r.mc.error().code == ErrorCode::EStop);
        CHECK(r.mc.standUp().code == ErrorCode::BadState); CHECK(r.mc.sitDown().code == ErrorCode::BadState);
        CHECK(r.mc.reset().ok()); CHECK(r.mc.state() == RobotState::Idle); CHECK(!r.mc.error().active);
    }
    {
        Rig r;
        r.standUpFully();
        r.backend.failNext = true;
        r.mc.update(0.02f);
        CHECK(r.mc.state() == RobotState::Error); CHECK(r.mc.error().code == ErrorCode::Hardware);
    }
    {
        Rig r;
        r.standUpFully();
        r.mc.move(0, 1, 0, false, 0);
        r.run(1.0f);
        r.mc.onLinkLost();
        r.run(3.0f);
        CHECK(r.mc.state() == RobotState::Sitting); CHECK(r.mc.smoothedVelocity().isZero());
    }
}

TEST(controller_special_actions_and_pose_envelope) {
    const char* names[] = {"wave", "bob", "dance"};
    for (const char* n : names) {
        Rig r;
        r.standUpFully();
        CHECK(r.mc.runAction(n).ok());
        CHECK(r.mc.move(0, 1, 0, false, 0).code == ErrorCode::BadState);   // đang bận
        r.run(7.0f);
        CHECK(r.mc.state() == RobotState::Standing);
        CHECK_NEAR(r.posture.current().z, 0.0, 1e-5);
    }
    Rig r;
    r.standUpFully();
    r.mc.setPose(25, 10, 0, 0);
    r.run(2.0f);
    r.mc.move(0, 1, 0, false, 0);
    r.run(4.0f);
    CHECK(r.mc.state() == RobotState::Walking);
    CHECK(r.posture.current().z <= cfg::kWalkZMax + 1e-4f); CHECK(r.posture.current().roll <= cfg::kWalkRollLimit + 1e-4f);
    r.mc.stop();
    r.run(3.0f);
    CHECK_NEAR(r.posture.current().z, 25.0, 1e-4);
}

TEST(controller_servo_test_mode) {
    Rig r;
    CHECK(r.mc.enable().ok());
    CHECK(r.mc.setServo(0, 1, 20.0f, false).ok());
    CHECK(r.mc.setServo(0, 1, 100.0f, true).ok());
    CHECK_NEAR(r.backend.rawServo[1], 100.0, 1e-6);
    CHECK(r.mc.setServo(0, 1, 500.0f, false).code == ErrorCode::BadParams);
    CHECK(r.mc.setServo(9, 1, 0.0f, false).code == ErrorCode::BadParams);
    r.mc.standUp();
    r.run(1.6f);
    CHECK(r.mc.setServo(0, 1, 20.0f, false).code == ErrorCode::BadState);
}

// ------------------------------------------------------------------ phần cứng
TEST(pca9685_registers_and_ticks) {
    FakeI2C bus; FakeClock clock;
    PCA9685 chip(bus, clock, 0x40, 25000000, 50);
    CHECK(chip.prescale() == 121);
    CHECK(chip.ticksForPulse(1500.0f) == 307);
    CHECK(chip.ticksForPulse(500.0f) == 102);
    CHECK(chip.ticksForPulse(2400.0f) == 492);
    CHECK(chip.ticksForPulse(99999.0f) == 4095);
    CHECK(chip.init());
    // MODE1=sleep, PRESCALE, MODE1=AI, MODE1=restart|AI, ALL_LED_OFF
    CHECK(bus.writes.size() == 5);
    CHECK(bus.writes[0].bytes == (std::vector<uint8_t>{0x00, 0x10}));
    CHECK(bus.writes[1].bytes == (std::vector<uint8_t>{0xFE, 121}));
    CHECK(bus.writes[3].bytes == (std::vector<uint8_t>{0x00, 0xA0}));
    CHECK(bus.writes[4].bytes == (std::vector<uint8_t>{0xFC, 0x00, 0x10}));
    uint16_t ticks[16];
    for (int c = 0; c < 16; ++c) ticks[c] = PCA9685::kFullOff;
    ticks[2] = 307;
    bus.writes.clear();
    CHECK(chip.writeChannels(ticks));
    CHECK(bus.writes.size() == 1 && bus.writes[0].bytes.size() == 65);
    const std::vector<uint8_t>& p = bus.writes[0].bytes;
    CHECK(p[0] == 0x06);
    CHECK(p[1 + 4 * 2 + 2] == (307 & 0xFF) && p[1 + 4 * 2 + 3] == (307 >> 8));
    CHECK(p[1 + 4 * 0 + 3] == 0x10);                                   // kênh 0: full off
}

TEST(servo_calibration_math) {
    const Servo s(cfg::kServoCal[0]);                                  // coxa chân i: offset 90, direction +1
    CHECK_NEAR(s.servoAngle(0), 90, 1e-5); CHECK_NEAR(s.servoAngle(30), 120, 1e-5);
    CHECK_NEAR(s.servoAngle(500), 180, 1e-5);
    CHECK_NEAR(s.pulseUs(0), 500, 1e-3); CHECK_NEAR(s.pulseUs(180), 2400, 1e-3); CHECK_NEAR(s.pulseUs(90), 1450, 1e-3);
    const Servo left(cfg::kServoCal[3 * 3 + 1]);                       // femur chân l (bên trái): đảo chiều
    CHECK_NEAR(left.servoAngle(20), 70, 1e-5);
}

TEST(servo_manager_and_backend_write_whole_frame) {
    FakeI2C bus; FakeClock clock;
    ServoManager servos(bus, clock);
    PCA9685Backend backend(servos, nullptr);
    CHECK(backend.enable());
    bus.writes.clear();
    JointFrame f;                                                      // mọi góc = 0 -> coxa/femur 90°, tibia theo offset
    CHECK(backend.apply(f));
    CHECK(bus.writes.size() == 2);                                     // mỗi board đúng 1 lần ghi 65 byte
    CHECK(bus.writes[0].address == cfg::kBoardAddress[0] && bus.writes[1].address == cfg::kBoardAddress[1]);
    CHECK(bus.writes[0].bytes.size() == 65);
    const PCA9685 chip(bus, clock, 0x40, cfg::kOscillatorHz, cfg::kPwmHz);
    CHECK(servos.board(0).ticks(0) == chip.ticksForPulse(1450.0f));    // leg i coxa -> board 0 kênh 0
    CHECK(servos.board(1).ticks(8) == servos.board(1).ticks(8));
    CHECK(servos.board(0).ticks(9) == PCA9685::kFullOff);              // kênh không dùng vẫn tắt
    CHECK(backend.applyRawServo(0, 1, 0.0f));
    CHECK(servos.board(0).ticks(1) == chip.ticksForPulse(500.0f));
    bus.failWrites = true;
    CHECK(!backend.apply(f));                                          // lỗi I2C được báo lên
}

TEST(mpu6050_and_attitude) {
    FakeI2C bus; FakeClock clock;
    Mpu6050 imu(bus, clock, 0x68);
    CHECK(imu.begin());
    // ax=0, ay=0, az=1g (16384), gx=131 -> 1 °/s ; dữ liệu big-endian
    const uint8_t raw[14] = {0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x83, 0x00, 0x00, 0x00, 0x00};
    memcpy(bus.regs, raw, 14);
    ImuSample s;
    CHECK(imu.read(s));
    CHECK_NEAR(s.az, 1.0, 1e-4); CHECK_NEAR(s.ax, 0.0, 1e-4); CHECK_NEAR(s.gx, 1.0, 1e-3);
    AttitudeEstimator est(0.98f);
    ImuSample tilt = {0.0f, 0.5f, 0.866f, 0, 0, 0};                    // nghiêng ~30° quanh trục X
    for (int i = 0; i < 400; ++i) est.update(tilt, 0.02f);
    CHECK_NEAR(est.roll(), 30.0, 0.5); CHECK_NEAR(est.pitch(), 0.0, 0.5);
}

class FixedAnalog : public AnalogInput { public: float mv = 2500.0f; float readMilliVolts() override { return mv; } };

TEST(battery_monitor) {
    FixedAnalog adc;
    BatteryMonitor battery(adc, 3.13f);
    CHECK(!battery.valid());
    battery.update();
    CHECK_NEAR(battery.voltage(), 2.5 * 3.13, 1e-3);
    adc.mv = 2000.0f;
    for (int i = 0; i < 100; ++i) battery.update();
    CHECK_NEAR(battery.voltage(), 2.0 * 3.13, 0.01);
}

// ------------------------------------------------------------------ RobotApp (toàn bộ đường lệnh -> phản hồi)
struct AppRig {
    Rig rig;
    FakeTransport transport;
    struct Lost : WatchdogListener { MotionController& mc; int count = 0;
        explicit Lost(MotionController& m) : mc(m) {} void onTimeout() override { ++count; mc.onLinkLost(); } } lost;
    Watchdog watchdog;
    StatusReporter reporter;
    CommandHandler handler;
    RobotApp app;
    AppRig() : lost(rig.mc), watchdog(cfg::kWatchdogTimeoutS, lost), reporter(rig.mc, 5.0f),
               handler(rig.mc, reporter, watchdog), app(transport, rig.mc, reporter, handler, watchdog) {}
    void send(const char* line) { transport.incoming.push_back(line); transport.sent.clear(); app.step(0.02f); }
    std::string reply() const { return transport.sent.empty() ? "" : transport.sent.front(); }
    // Chạy n chu kỳ, giữ kết nối "sống" bằng HEARTBEAT mỗi 0.4 s như PC thật.
    void runAlive(int steps) {
        for (int i = 0; i < steps; ++i) {
            if (i % 20 == 0) transport.incoming.push_back("{\"seq\":99,\"cmd\":\"HEARTBEAT\"}");
            app.step(0.02f);
        }
    }
};

TEST(app_command_flow_and_error_responses) {
    AppRig a;
    a.send("{\"seq\":1,\"cmd\":\"STAND_UP\",\"params\":{}}");
    CHECK_STR(a.reply().c_str(), "{\"seq\":1,\"type\":\"ACK\",\"data\":{}}");
    a.runAlive(90);
    CHECK(a.rig.mc.state() == RobotState::Standing);
    a.send("{\"seq\":2,\"cmd\":\"MOVE\",\"params\":{\"vx\":0,\"vy\":1,\"wz\":0,\"speed\":0.8}}");
    CHECK_STR(a.reply().c_str(), "{\"seq\":2,\"type\":\"ACK\",\"data\":{}}");
    a.send("{\"seq\":3,\"cmd\":\"MOVE\",\"params\":{\"vx\":2}}");
    CHECK(a.reply().find("\"BAD_PARAMS\"") != std::string::npos);
    a.send("{\"seq\":4,\"cmd\":\"MOVE\",\"params\":{\"vx\":\"fast\"}}");
    CHECK(a.reply().find("\"BAD_PARAMS\"") != std::string::npos);
    a.send("{\"seq\":5,\"cmd\":\"BOGUS\"}");
    CHECK(a.reply().find("\"BAD_COMMAND\"") != std::string::npos);
    a.send("garbage");
    CHECK(a.reply().find("\"BAD_FORMAT\"") != std::string::npos);
    a.send("{\"seq\":6,\"cmd\":\"SET_GAIT\",\"params\":{\"gait\":\"hop\"}}");
    CHECK(a.reply().find("\"BAD_PARAMS\"") != std::string::npos);
    a.send("{\"seq\":7,\"cmd\":\"SET_GAIT\",\"params\":{\"gait\":\"wave\"}}");
    CHECK(a.reply().find("\"ACK\"") != std::string::npos);
    a.send("{\"seq\":8,\"cmd\":\"SET_SERVO\",\"params\":{\"leg\":0,\"joint\":0}}");
    CHECK(a.reply().find("\"BAD_PARAMS\"") != std::string::npos);        // thiếu angle
}

TEST(app_status_packet_is_valid_json_with_expected_fields) {
    AppRig a;
    const uint8_t devices[] = {0x40, 0x41, 0x68};
    a.reporter.setI2cDevices(devices, 3);
    a.reporter.setBattery(7.84f);
    a.reporter.setImu(1.5f, -2.5f);
    a.send("{\"seq\":9,\"cmd\":\"GET_STATUS\"}");
    const std::string s = a.reply();
    CHECK(s.size() > 0 && s.size() < 768);
    CHECK(s.find("\"seq\":9,\"type\":\"STATUS\"") != std::string::npos);
    CHECK(s.find("\"state\":\"IDLE\"") != std::string::npos);
    CHECK(s.find("\"i2c\":[64,65,104]") != std::string::npos);
    CHECK(s.find("\"battery_v\":7.84") != std::string::npos);
    CHECK(s.find("\"imu\":{\"roll\":1.5,\"pitch\":-2.5}") != std::string::npos);
    CHECK(s.find("\"error\":null") != std::string::npos);
    JsonReader r;                                                       // JSON hợp lệ (qua bộ đọc; mảng angles không hỗ trợ -> bỏ qua kiểm tra này)
    size_t commas = 0; for (char c : s) if (c == ',') ++commas;
    CHECK(commas > 30);
}

TEST(app_pushes_status_periodically_and_watchdog_sits_robot) {
    AppRig a;
    a.send("{\"seq\":1,\"cmd\":\"STAND_UP\"}");
    for (int i = 0; i < 90; ++i) a.app.step(0.02f);
    a.transport.sent.clear();
    for (int i = 0; i < 60; ++i) a.app.step(0.02f);                     // 1.2 s -> ~6 gói STATUS (5 Hz)
    int pushes = 0;
    for (const std::string& s : a.transport.sent) if (s.find("\"seq\":0,\"type\":\"STATUS\"") != std::string::npos) ++pushes;
    CHECK(pushes >= 5 && pushes <= 7);
    for (int i = 0; i < 80; ++i) a.app.step(0.02f);                     // > 1.5 s im lặng -> watchdog
    CHECK(a.lost.count == 1);
    for (int i = 0; i < 200; ++i) a.app.step(0.02f);
    CHECK(a.rig.mc.state() == RobotState::Sitting);
}

TEST(app_client_drop_triggers_watchdog_immediately) {
    AppRig a;
    a.send("{\"seq\":1,\"cmd\":\"STAND_UP\"}");
    for (int i = 0; i < 90; ++i) a.app.step(0.02f);
    a.transport.dropped = true;
    a.transport.connected = false;
    a.app.step(0.02f);
    CHECK(a.lost.count == 1);
}

TEST(app_emergency_stop_is_always_processed) {
    AppRig a;
    a.send("{\"seq\":1,\"cmd\":\"STAND_UP\"}");
    a.runAlive(90);
    a.send("{\"seq\":2,\"cmd\":\"MOVE\",\"params\":{\"vy\":1}}");
    a.runAlive(20);
    a.send("{\"seq\":3,\"cmd\":\"EMERGENCY_STOP\"}");
    CHECK(a.reply().find("\"ACK\"") != std::string::npos);
    CHECK(a.rig.mc.state() == RobotState::Error); CHECK(!a.rig.backend.enabled);
}

// ------------------------------------------------------------------ kịch bản đối chiếu với Python
static void printStep(const MotionController& mc) {
    printf("S %s", toString(mc.state()));
    for (int i = 0; i < kNumServos; ++i) printf(" %.4f", mc.frame().angles[i]);
    printf("\n");
}

static int dumpScenario(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) { fprintf(stderr, "không mở được %s\n", path); return 2; }
    Rig r;
    char line[160];
    while (fgets(line, sizeof(line), f)) {
        char cmd[24] = "", arg[24] = "";
        float a = 0, b = 0, c = 0, d = 0;
        if (line[0] == '#' || sscanf(line, "%23s", cmd) != 1) continue;
        Result res;
        if (!strcmp(cmd, "run")) {
            sscanf(line, "%*s %f", &a);
            const int n = static_cast<int>(floorf(a / 0.02f + 0.5f));
            for (int i = 0; i < n; ++i) { r.mc.update(0.02f); printStep(r.mc); }
            continue;
        }
        if (!strcmp(cmd, "stand_up")) res = r.mc.standUp();
        else if (!strcmp(cmd, "sit_down")) res = r.mc.sitDown();
        else if (!strcmp(cmd, "enable")) res = r.mc.enable();
        else if (!strcmp(cmd, "disable")) res = r.mc.disable();
        else if (!strcmp(cmd, "stop")) res = r.mc.stop();
        else if (!strcmp(cmd, "reset")) res = r.mc.reset();
        else if (!strcmp(cmd, "estop")) r.mc.emergencyStop();
        else if (!strcmp(cmd, "link_lost")) r.mc.onLinkLost();
        else if (!strcmp(cmd, "move")) { sscanf(line, "%*s %f %f %f %f", &a, &b, &c, &d); res = r.mc.move(a, b, c, true, d); }
        else if (!strcmp(cmd, "speed")) { sscanf(line, "%*s %f", &a); res = r.mc.setSpeed(a); }
        else if (!strcmp(cmd, "pose")) { sscanf(line, "%*s %f %f %f %f", &a, &b, &c, &d); res = r.mc.setPose(a, b, c, d); }
        else if (!strcmp(cmd, "gait")) { sscanf(line, "%*s %23s", arg); GaitType g = GaitType::Tripod; gaitFromString(arg, g); res = r.mc.setGait(g); }
        else if (!strcmp(cmd, "action")) { sscanf(line, "%*s %23s", arg); res = r.mc.runAction(arg); }
        else { fprintf(stderr, "lệnh không biết: %s\n", cmd); return 2; }
        if (!res.ok()) printf("ERR %s\n", toString(res.code));
    }
    fclose(f);
    return 0;
}

// Đứng yên hoàn toàn rồi in tick PWM của 18 kênh (đối chiếu calibration + servo_map + công thức tick với Python).
static int dumpTicks() {
    FakeI2C bus; FakeClock clock;
    ServoManager servos(bus, clock);
    PCA9685Backend backend(servos, nullptr);
    Hexapod hexapod; BodyKinematics bodyKin(hexapod); MotionCoordinator coordinator(hexapod, bodyKin);
    SafetyGuard guard(hexapod); PostureGenerator posture; GaitFactory gaits(hexapod);
    MotionController mc(hexapod, coordinator, guard, backend, posture, gaits);
    mc.standUp();
    for (int i = 0; i < 90; ++i) mc.update(0.02f);
    for (int s = 0; s < kNumServos; ++s) {
        printf("T %d %d %d\n", s, cfg::kServoMap[s].board, servos.board(cfg::kServoMap[s].board).ticks(cfg::kServoMap[s].channel));
    }
    return 0;
}

int main(int argc, char** argv) {
    if (argc >= 3 && !strcmp(argv[1], "dump")) return dumpScenario(argv[2]);
    if (argc >= 2 && !strcmp(argv[1], "ticks")) return dumpTicks();
    int failedTests = 0;
    for (const TestCase& t : registry()) {
        const int before = gFailures;
        t.fn();
        printf("%s %s\n", gFailures == before ? "[ OK ]" : "[FAIL]", t.name);
        if (gFailures != before) ++failedTests;
    }
    printf("\n%zu test, %d check, %d lỗi\n", registry().size(), gChecks, gFailures);
    return failedTests == 0 ? 0 : 1;
}
