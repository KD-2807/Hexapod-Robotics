#include "enums.h"

#include <string.h>

namespace hexapod {

const char* toString(RobotState s) {
    switch (s) {
        case RobotState::Idle: return "IDLE";
        case RobotState::Standing: return "STANDING";
        case RobotState::Walking: return "WALKING";
        case RobotState::Sitting: return "SITTING";
        case RobotState::Error: return "ERROR";
    }
    return "UNKNOWN";
}

const char* toString(GaitType g) {
    switch (g) {
        case GaitType::Tripod: return "tripod";
        case GaitType::Wave: return "wave";
        case GaitType::Ripple: return "ripple";
        case GaitType::Rotation: return "rotation";
    }
    return "tripod";
}

const char* toString(ErrorCode c) {
    switch (c) {
        case ErrorCode::None: return "NONE";
        case ErrorCode::BadFormat: return "BAD_FORMAT";
        case ErrorCode::BadCommand: return "BAD_COMMAND";
        case ErrorCode::BadParams: return "BAD_PARAMS";
        case ErrorCode::BadState: return "BAD_STATE";
        case ErrorCode::Limit: return "LIMIT";
        case ErrorCode::Hardware: return "HARDWARE";
        case ErrorCode::EStop: return "ESTOP";
    }
    return "UNKNOWN";
}

namespace {
struct CommandName { const char* name; CommandType type; };
const CommandName kCommands[] = {
    {"ENABLE", CommandType::Enable}, {"DISABLE", CommandType::Disable}, {"STAND_UP", CommandType::StandUp},
    {"SIT_DOWN", CommandType::SitDown}, {"MOVE", CommandType::Move}, {"STOP", CommandType::Stop},
    {"SET_GAIT", CommandType::SetGait}, {"SET_SPEED", CommandType::SetSpeed}, {"SET_POSE", CommandType::SetPose},
    {"ACTION", CommandType::Action}, {"EMERGENCY_STOP", CommandType::EmergencyStop}, {"RESET", CommandType::Reset},
    {"HEARTBEAT", CommandType::Heartbeat}, {"GET_STATUS", CommandType::GetStatus}, {"SET_SERVO", CommandType::SetServo},
};
}  // namespace

bool commandFromString(const char* text, CommandType& out) {
    for (const CommandName& c : kCommands) {
        if (strcmp(text, c.name) == 0) { out = c.type; return true; }
    }
    return false;
}

bool gaitFromString(const char* text, GaitType& out) {
    static const GaitType all[] = {GaitType::Tripod, GaitType::Wave, GaitType::Ripple, GaitType::Rotation};
    for (GaitType g : all) {
        if (strcmp(text, toString(g)) == 0) { out = g; return true; }
    }
    return false;
}

}  // namespace hexapod
