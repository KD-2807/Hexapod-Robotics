#include "state_machine.h"

#include <stdio.h>

namespace hexapod {

bool StateMachine::accepts(CommandType c) const {
    switch (c) {   // luôn được nhận
        case CommandType::Heartbeat: case CommandType::GetStatus: case CommandType::EmergencyStop:
        case CommandType::SetGait: case CommandType::SetSpeed: case CommandType::Stop:
            return true;
        default: break;
    }
    switch (state_) {
        case RobotState::Idle:
            return c == CommandType::Enable || c == CommandType::StandUp || c == CommandType::Disable ||
                   c == CommandType::Reset;
        case RobotState::Sitting:
            return c == CommandType::Enable || c == CommandType::StandUp || c == CommandType::SitDown ||
                   c == CommandType::Disable || c == CommandType::SetServo;
        case RobotState::Standing:
            return c == CommandType::Enable || c == CommandType::StandUp || c == CommandType::SitDown ||
                   c == CommandType::Move || c == CommandType::SetPose || c == CommandType::Action;
        case RobotState::Walking:
            return c == CommandType::Enable || c == CommandType::SitDown || c == CommandType::Move ||
                   c == CommandType::SetPose;
        case RobotState::Error:
            return c == CommandType::Reset;
    }
    return false;
}

Result StateMachine::require(CommandType c) {
    if (accepts(c)) return Result::success();
    snprintf(msg_, sizeof(msg_), "Lệnh không hợp lệ ở trạng thái %s", toString(state_));
    return Result::fail(ErrorCode::BadState, msg_);
}

Result StateMachine::transition(RobotState next) {
    if (next == state_) return Result::success();
    bool allowed = false;
    switch (state_) {
        case RobotState::Idle: allowed = (next == RobotState::Sitting); break;
        case RobotState::Sitting: allowed = (next == RobotState::Standing || next == RobotState::Idle); break;
        case RobotState::Standing: allowed = (next == RobotState::Walking || next == RobotState::Sitting); break;
        case RobotState::Walking: allowed = (next == RobotState::Standing); break;
        case RobotState::Error: allowed = (next == RobotState::Idle); break;
    }
    if (!allowed) {
        snprintf(msg_, sizeof(msg_), "Không thể chuyển %s -> %s", toString(state_), toString(next));
        return Result::fail(ErrorCode::BadState, msg_);
    }
    state_ = next;
    return Result::success();
}

}  // namespace hexapod
