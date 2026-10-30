// FILE TỰ SINH bởi tools/gen_firmware_config.py - KHÔNG SỬA TAY. Sửa các file trong config/ rồi sinh lại.
#pragma once
#include <stdint.h>

namespace cfg {
// ---- robot_config.json
constexpr float kCoxaLen = 54.0f, kFemurLen = 45.0f, kTibiaLen = 77.0f;
constexpr float kStanceRadius = 110.0f, kStandHeight = 60.0f, kSitHeight = 20.0f;
struct LegSpec { const char* id; const char* name; float x; float y; float yawDeg; };
constexpr LegSpec kLegs[6] = {
    {"i", "RIGHT_MIDDLE", 60.0f, 0.0f, 0.0f},
    {"j", "RIGHT_REAR", 50.0f, -80.0f, -45.0f},
    {"k", "LEFT_REAR", -50.0f, -80.0f, -135.0f},
    {"l", "LEFT_MIDDLE", -60.0f, 0.0f, 180.0f},
    {"m", "LEFT_FRONT", -50.0f, 80.0f, 135.0f},
    {"n", "RIGHT_FRONT", 50.0f, 80.0f, 45.0f},
};

// ---- servo_map.json: (leg, joint) -> board, channel
struct ServoMap { uint8_t board; uint8_t channel; };
constexpr ServoMap kServoMap[18] = {
    {0, 0},  // i.coxa
    {0, 1},  // i.femur
    {0, 2},  // i.tibia
    {0, 3},  // j.coxa
    {0, 4},  // j.femur
    {0, 5},  // j.tibia
    {0, 6},  // k.coxa
    {0, 7},  // k.femur
    {0, 8},  // k.tibia
    {1, 0},  // l.coxa
    {1, 1},  // l.femur
    {1, 2},  // l.tibia
    {1, 3},  // m.coxa
    {1, 4},  // m.femur
    {1, 5},  // m.tibia
    {1, 6},  // n.coxa
    {1, 7},  // n.femur
    {1, 8},  // n.tibia
};

// ---- servo_calibration.json: servo_deg = offset + direction * joint_deg
struct ServoCal { float offsetDeg; int8_t direction; float pulseMinUs; float pulseMaxUs; };
constexpr ServoCal kServoCal[18] = {
    {90.0f, 1, 500.0f, 2400.0f},
    {90.0f, 1, 500.0f, 2400.0f},
    {150.0f, 1, 500.0f, 2400.0f},
    {90.0f, 1, 500.0f, 2400.0f},
    {90.0f, 1, 500.0f, 2400.0f},
    {150.0f, 1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {30.0f, -1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {30.0f, -1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {90.0f, -1, 500.0f, 2400.0f},
    {30.0f, -1, 500.0f, 2400.0f},
    {90.0f, 1, 500.0f, 2400.0f},
    {90.0f, 1, 500.0f, 2400.0f},
    {150.0f, 1, 500.0f, 2400.0f},
};

// ---- gait_config.json
constexpr float kStepLength = 60.0f, kStepHeight = 20.0f, kTurnAngleDeg = 20.0f;
constexpr float kMaxStride = 70.0f, kLiftRamp = 25.0f, kVelocityRampPerS = 3.0f;
constexpr int kDefaultGait = 0;
constexpr float kDefaultSpeed = 0.6f;
// slotOf[leg] = chỉ số nhóm nhấc chân; slotCount = số nhóm trong 1 chu kỳ
struct GaitProfile { float duty; float cycleTimeS; int slotCount; int8_t slotOf[6]; };
constexpr GaitProfile kGaits[4] = {   // tripod, wave, ripple, rotation
    {0.5f, 1.5f, 2, {0, 1, 0, 1, 0, 1}},  // tripod
    {0.8334f, 4.5f, 6, {1, 0, 3, 4, 5, 2}},  // wave
    {0.6667f, 2.25f, 3, {1, 0, 2, 1, 0, 2}},  // ripple
    {0.5f, 1.5f, 2, {0, 1, 0, 1, 0, 1}},  // rotation
};

// ---- pose_config.json
constexpr float kZMin = -25.0f, kZMax = 30.0f, kRollLimit = 15.0f, kPitchLimit = 15.0f, kYawLimit = 20.0f;
constexpr float kZRate = 40.0f, kAngleRate = 40.0f;
constexpr float kWalkZMin = -2.0f, kWalkZMax = 10.0f, kWalkRollLimit = 2.0f, kWalkPitchLimit = 2.0f, kWalkYawLimit = 5.0f;
constexpr float kPoseCheckMarginDeg = 2.0f;

// ---- safety_config.json
constexpr float kWatchdogTimeoutS = 1.5f, kMaxJointSpeedDps = 360.0f, kAngleMarginDeg = 3.0f;
struct JointLimit { float minDeg; float maxDeg; };
constexpr JointLimit kJointLimits[3] = {   // coxa, femur, tibia
    {-50.0f, 50.0f},
    {-70.0f, 90.0f},
    {-140.0f, 10.0f},
};

// ---- hardware_config.json
constexpr int kI2cSda = 21, kI2cScl = 22;
constexpr uint32_t kI2cFrequencyHz = 400000;
constexpr int kBoardCount = 2;
constexpr uint8_t kBoardAddress[2] = {0x40, 0x41};
constexpr int kPwmHz = 50;
constexpr uint32_t kOscillatorHz = 25000000;
constexpr bool kImuEnabled = true;
constexpr uint8_t kImuAddress = 0x68;
constexpr float kImuAlpha = 0.98f;
constexpr int kBatteryAdcPin = 34;
constexpr float kBatteryDividerRatio = 3.13f;
constexpr int kServoOutputEnablePin = -1;   // -1: không dùng chân OE
constexpr int kLoopHz = 50, kStatusHz = 5;

// ---- network_config.json
constexpr const char* kWifiSsid = "YOUR_WIFI_SSID";
constexpr const char* kWifiPassword = "YOUR_WIFI_PASSWORD";
constexpr int kWifiTimeoutS = 15, kTcpPort = 8888;
constexpr const char* kHostname = "hexapod";
constexpr const char* kApSsid = "Hexapod-AP";
constexpr const char* kApPassword = "hexapod123";
}  // namespace cfg
