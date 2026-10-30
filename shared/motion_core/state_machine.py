"""StateMachine: quản lý RobotState và các lệnh được chấp nhận ở từng trạng thái."""
from typing import Dict, FrozenSet

from shared.common.enums import CommandType as C, ErrorCode, RobotState as S
from shared.motion_core.errors import MotionError

# Lệnh luôn được nhận (không đổi trạng thái chuyển động).
_ALWAYS = frozenset({C.HEARTBEAT, C.GET_STATUS, C.EMERGENCY_STOP, C.SET_GAIT, C.SET_SPEED, C.STOP})

_ACCEPTED: Dict[S, FrozenSet[C]] = {
    S.IDLE: _ALWAYS | {C.ENABLE, C.STAND_UP, C.DISABLE, C.RESET},
    S.SITTING: _ALWAYS | {C.ENABLE, C.STAND_UP, C.SIT_DOWN, C.DISABLE, C.SET_SERVO},
    S.STANDING: _ALWAYS | {C.ENABLE, C.STAND_UP, C.SIT_DOWN, C.MOVE, C.SET_POSE, C.ACTION},
    S.WALKING: _ALWAYS | {C.ENABLE, C.SIT_DOWN, C.MOVE, C.SET_POSE},
    S.ERROR: _ALWAYS | {C.RESET},
}

_TRANSITIONS: Dict[S, FrozenSet[S]] = {
    S.IDLE: frozenset({S.SITTING}),
    S.SITTING: frozenset({S.STANDING, S.IDLE}),
    S.STANDING: frozenset({S.WALKING, S.SITTING}),
    S.WALKING: frozenset({S.STANDING}),
    S.ERROR: frozenset({S.IDLE}),
}


class StateMachine:
    def __init__(self):
        self.state = S.IDLE

    def accepts(self, command: C) -> bool:
        return command in _ACCEPTED[self.state]

    def require(self, command: C) -> None:
        if not self.accepts(command):
            raise MotionError(ErrorCode.BAD_STATE,
                              "Lệnh %s không hợp lệ ở trạng thái %s" % (command.value, self.state.value))

    def transition(self, new_state: S) -> None:
        if new_state == self.state:
            return
        if new_state not in _TRANSITIONS[self.state]:
            raise MotionError(ErrorCode.BAD_STATE,
                              "Không thể chuyển %s -> %s" % (self.state.value, new_state.value))
        self.state = new_state

    def fail(self) -> None:
        """Bất kỳ trạng thái nào -> ERROR."""
        self.state = S.ERROR
