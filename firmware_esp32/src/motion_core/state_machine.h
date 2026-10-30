#pragma once
#include "../common/enums.h"
#include "../common/types.h"

namespace hexapod {

// Quản lý RobotState và các lệnh được chấp nhận ở từng trạng thái.
class StateMachine {
public:
    RobotState state() const { return state_; }
    bool accepts(CommandType cmd) const;
    Result require(CommandType cmd);              // BAD_STATE nếu lệnh không hợp lệ ở trạng thái hiện tại
    Result transition(RobotState next);           // BAD_STATE nếu chuyển không hợp lệ
    void fail() { state_ = RobotState::Error; }   // bất kỳ trạng thái nào -> ERROR
    void forceState(RobotState s) { state_ = s; } // chỉ dùng cho test

private:
    RobotState state_ = RobotState::Idle;
    char msg_[64] = {0};
};

}  // namespace hexapod
