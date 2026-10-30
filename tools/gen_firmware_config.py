"""Sinh firmware_esp32/include/generated_config.h từ các file JSON trong config/.

Một nguồn cấu hình duy nhất (DRY): Python đọc JSON trực tiếp, firmware C++ dùng header sinh ra từ cùng JSON.
PlatformIO tự gọi script này trước mỗi lần build (xem firmware_esp32/platformio.ini).

    python -m tools.gen_firmware_config            # ghi file
    python -m tools.gen_firmware_config --check    # kiểm tra file hiện có còn khớp JSON không
"""
import argparse
import os
import sys
from typing import List

from shared.common.config_loader import ConfigLoader
from shared.common.enums import JointType
from shared.gait_core.gait_config import GaitConfig
from shared.posture_core.pose_config import PoseConfig
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.safety_config import SafetyConfig
from shared.robot_core.servo_calibration import CalibrationTable

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "firmware_esp32", "include", "generated_config.h")
_GAIT_ORDER = ["tripod", "wave", "ripple", "rotation"]        # phải khớp enum GaitType trong firmware


def f(value: float) -> str:
    text = repr(float(value))
    return text + "f"


def c_str(text: str) -> str:
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


def generate(loader: ConfigLoader) -> str:
    robot = RobotConfig.from_dict(loader.load("robot_config"))
    safety = SafetyConfig.from_dict(loader.load("safety_config"))
    gait = GaitConfig.from_dict(loader.load("gait_config"))
    pose = PoseConfig.from_dict(loader.load("pose_config"))
    hw = loader.load("hardware_config")
    net = loader.load("network_config")
    servo_map = loader.load("servo_map")
    calibration = CalibrationTable.from_dict(loader.load("servo_calibration"), robot)
    leg_ids = [spec.id for spec in robot.legs]

    out: List[str] = []
    w = out.append
    w("// FILE TỰ SINH bởi tools/gen_firmware_config.py - KHÔNG SỬA TAY. Sửa các file trong config/ rồi sinh lại.")
    w("#pragma once")
    w("#include <stdint.h>")
    w("")
    w("namespace cfg {")
    w("// ---- robot_config.json")
    w("constexpr float kCoxaLen = %s, kFemurLen = %s, kTibiaLen = %s;" % (f(robot.coxa), f(robot.femur), f(robot.tibia)))
    w("constexpr float kStanceRadius = %s, kStandHeight = %s, kSitHeight = %s;" % (
        f(robot.stance_radius), f(robot.stand_height), f(robot.sit_height)))
    w("struct LegSpec { const char* id; const char* name; float x; float y; float yawDeg; };")
    w("constexpr LegSpec kLegs[6] = {")
    for s in robot.legs:
        w("    {%s, %s, %s, %s, %s}," % (c_str(s.id), c_str(s.name), f(s.x), f(s.y), f(s.yaw_deg)))
    w("};")
    w("")
    w("// ---- servo_map.json: (leg, joint) -> board, channel")
    w("struct ServoMap { uint8_t board; uint8_t channel; };")
    w("constexpr ServoMap kServoMap[18] = {")
    for lid in leg_ids:
        for joint in JointType:
            board, channel = servo_map[lid][joint.name.lower()]
            w("    {%d, %d},  // %s.%s" % (board, channel, lid, joint.name.lower()))
    w("};")
    w("")
    w("// ---- servo_calibration.json: servo_deg = offset + direction * joint_deg")
    w("struct ServoCal { float offsetDeg; int8_t direction; float pulseMinUs; float pulseMaxUs; };")
    w("constexpr ServoCal kServoCal[18] = {")
    for leg in range(6):
        for joint in JointType:
            c = calibration.get(leg, int(joint))
            w("    {%s, %d, %s, %s}," % (f(c.offset_deg), c.direction, f(c.pulse_min_us), f(c.pulse_max_us)))
    w("};")
    w("")
    w("// ---- gait_config.json")
    w("constexpr float kStepLength = %s, kStepHeight = %s, kTurnAngleDeg = %s;" % (
        f(gait.step_length), f(gait.step_height), f(gait.turn_angle_deg)))
    w("constexpr float kMaxStride = %s, kLiftRamp = %s, kVelocityRampPerS = %s;" % (
        f(gait.max_stride), f(gait.lift_ramp), f(gait.velocity_ramp_per_s)))
    w("constexpr int kDefaultGait = %d;" % _GAIT_ORDER.index(gait.default_gait.value))
    w("constexpr float kDefaultSpeed = %s;" % f(gait.default_speed))
    w("// slotOf[leg] = chỉ số nhóm nhấc chân; slotCount = số nhóm trong 1 chu kỳ")
    w("struct GaitProfile { float duty; float cycleTimeS; int slotCount; int8_t slotOf[6]; };")
    w("constexpr GaitProfile kGaits[4] = {   // tripod, wave, ripple, rotation")
    for name in _GAIT_ORDER:
        profile = next(p for g, p in gait.profiles.items() if g.value == name)
        slot_of = [-1] * 6
        for slot_index, slot in enumerate(profile.swing_slots):
            for lid in slot:
                slot_of[leg_ids.index(lid)] = slot_index
        w("    {%s, %s, %d, {%s}},  // %s" % (f(profile.duty), f(profile.cycle_time_s), len(profile.swing_slots),
                                           ", ".join(map(str, slot_of)), name))
    w("};")
    w("")
    w("// ---- pose_config.json")
    w("constexpr float kZMin = %s, kZMax = %s, kRollLimit = %s, kPitchLimit = %s, kYawLimit = %s;" % (
        f(pose.z_limits[0]), f(pose.z_limits[1]), f(pose.roll_limit), f(pose.pitch_limit), f(pose.yaw_limit)))
    w("constexpr float kZRate = %s, kAngleRate = %s;" % (f(pose.z_rate), f(pose.angle_rate)))
    w("constexpr float kWalkZMin = %s, kWalkZMax = %s, kWalkRollLimit = %s, kWalkPitchLimit = %s, kWalkYawLimit = %s;" % (
        f(pose.walk_z_limits[0]), f(pose.walk_z_limits[1]), f(pose.walk_roll_limit), f(pose.walk_pitch_limit),
        f(pose.walk_yaw_limit)))
    w("constexpr float kPoseCheckMarginDeg = %s;" % f(pose.check_margin_deg))
    w("")
    w("// ---- safety_config.json")
    w("constexpr float kWatchdogTimeoutS = %s, kMaxJointSpeedDps = %s, kAngleMarginDeg = %s;" % (
        f(safety.watchdog_timeout_s), f(safety.max_joint_speed_dps), f(safety.angle_margin_deg)))
    w("struct JointLimit { float minDeg; float maxDeg; };")
    w("constexpr JointLimit kJointLimits[3] = {   // coxa, femur, tibia")
    for jt in JointType:
        lo, hi = safety.joint_limits[jt]
        w("    {%s, %s}," % (f(lo), f(hi)))
    w("};")
    w("")
    w("// ---- hardware_config.json")
    w("constexpr int kI2cSda = %d, kI2cScl = %d;" % (hw["i2c"]["sda_pin"], hw["i2c"]["scl_pin"]))
    w("constexpr uint32_t kI2cFrequencyHz = %d;" % hw["i2c"]["frequency_hz"])
    addresses = hw["pca9685"]["addresses"]
    w("constexpr int kBoardCount = %d;" % len(addresses))
    w("constexpr uint8_t kBoardAddress[%d] = {%s};" % (len(addresses), ", ".join("0x%02X" % a for a in addresses)))
    w("constexpr int kPwmHz = %d;" % hw["pca9685"]["pwm_hz"])
    w("constexpr uint32_t kOscillatorHz = %d;" % hw["pca9685"]["oscillator_hz"])
    w("constexpr bool kImuEnabled = %s;" % ("true" if hw["mpu6050"]["enabled"] else "false"))
    w("constexpr uint8_t kImuAddress = 0x%02X;" % hw["mpu6050"]["address"])
    w("constexpr float kImuAlpha = %s;" % f(hw["mpu6050"]["complementary_alpha"]))
    w("constexpr int kBatteryAdcPin = %d;" % hw["battery"]["adc_pin"])
    w("constexpr float kBatteryDividerRatio = %s;" % f(hw["battery"]["divider_ratio"]))
    w("constexpr int kServoOutputEnablePin = %d;   // -1: không dùng chân OE" % hw["servo_output_enable_pin"])
    w("constexpr int kLoopHz = %d, kStatusHz = %d;" % (hw["loop_hz"], hw["status_hz"]))
    w("")
    w("// ---- network_config.json")
    w("constexpr const char* kWifiSsid = %s;" % c_str(net["ssid"]))
    w("constexpr const char* kWifiPassword = %s;" % c_str(net["password"]))
    w("constexpr int kWifiTimeoutS = %d, kTcpPort = %d;" % (net["connect_timeout_s"], net["tcp_port"]))
    w("constexpr const char* kHostname = %s;" % c_str(net["hostname"]))
    w("constexpr const char* kApSsid = %s;" % c_str(net["fallback_ap"]["ssid"]))
    w("constexpr const char* kApPassword = %s;" % c_str(net["fallback_ap"]["password"]))
    w("}  // namespace cfg")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="chỉ kiểm tra, không ghi")
    parser.add_argument("--config-dir")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args(argv)
    text = generate(ConfigLoader(args.config_dir))
    if args.check:
        current = open(args.output, encoding="utf-8").read() if os.path.exists(args.output) else ""
        if current != text:
            print("generated_config.h đã cũ so với config/*.json - hãy chạy: python -m tools.gen_firmware_config")
            return 1
        print("generated_config.h khớp với config/*.json")
        return 0
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("đã ghi", os.path.relpath(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
