#pragma once

namespace hexapod {

constexpr int kNumLegs = 6;
constexpr int kJointsPerLeg = 3;
constexpr int kNumServos = kNumLegs * kJointsPerLeg;

enum class GaitType : int { Tripod = 0, Wave = 1, Ripple = 2, Rotation = 3 };   // thứ tự = generated_config.h
enum class RobotState : int { Idle, Standing, Walking, Sitting, Error };
enum class CommandType : int {
    Enable, Disable, StandUp, SitDown, Move, Stop, SetGait, SetSpeed, SetPose, Action,
    EmergencyStop, Reset, Heartbeat, GetStatus, SetServo
};
enum class ErrorCode : int { None, BadFormat, BadCommand, BadParams, BadState, Limit, Hardware, EStop };

const char* toString(RobotState s);
const char* toString(GaitType g);        // "tripod" | "wave" | "ripple" | "rotation"
const char* toString(ErrorCode c);       // "BAD_STATE" ...
bool commandFromString(const char* text, CommandType& out);
bool gaitFromString(const char* text, GaitType& out);

}  // namespace hexapod
