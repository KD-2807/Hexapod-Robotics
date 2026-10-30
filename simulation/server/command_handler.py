"""CommandHandler (bản tham chiếu Python của firmware): Command -> MotionController -> Response."""
from typing import Any, Callable, Dict

from shared.common.enums import CommandType as C, ErrorCode, GaitType
from shared.common.protocol import Command, Response
from shared.motion_core.errors import MotionError
from shared.motion_core.motion_controller import MotionController


class CommandHandler:
    def __init__(self, controller: MotionController, status_provider: Callable[[], Dict[str, Any]]):
        self._mc = controller
        self._status = status_provider
        self._table: Dict[C, Callable[[Dict[str, Any]], None]] = {
            C.ENABLE: lambda p: self._mc.enable(),
            C.DISABLE: lambda p: self._mc.disable(),
            C.STAND_UP: lambda p: self._mc.stand_up(),
            C.SIT_DOWN: lambda p: self._mc.sit_down(),
            C.MOVE: self._move,
            C.STOP: lambda p: self._mc.stop(),
            C.SET_GAIT: self._set_gait,
            C.SET_SPEED: lambda p: self._mc.set_speed(self._num(p, "speed")),
            C.SET_POSE: self._set_pose,
            C.ACTION: lambda p: self._mc.run_action(str(p.get("name", ""))),
            C.EMERGENCY_STOP: lambda p: self._mc.emergency_stop(),
            C.RESET: lambda p: self._mc.reset(),
            C.HEARTBEAT: lambda p: None,
            C.GET_STATUS: lambda p: None,
            C.SET_SERVO: self._set_servo,
        }

    def handle(self, command: Command) -> Response:
        try:
            self._table[command.cmd](command.params)
        except MotionError as exc:
            return Response.error(command.seq, exc.code, exc.message)
        if command.cmd == C.GET_STATUS:
            return Response.status(command.seq, self._status())
        return Response.ack(command.seq)

    # ------------------------------------------------------------------ chuyển đổi tham số
    @staticmethod
    def _num(params: Dict[str, Any], key: str, default=None) -> float:
        value = params.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MotionError(ErrorCode.BAD_PARAMS, "Thiếu/sai tham số số: %s" % key)
        return float(value)

    def _move(self, p: Dict[str, Any]) -> None:
        speed = self._num(p, "speed") if "speed" in p else None
        self._mc.move(self._num(p, "vx", 0.0), self._num(p, "vy", 0.0), self._num(p, "wz", 0.0), speed)

    def _set_gait(self, p: Dict[str, Any]) -> None:
        try:
            self._mc.set_gait(GaitType(p.get("gait")))
        except ValueError:
            raise MotionError(ErrorCode.BAD_PARAMS, "gait không hợp lệ")

    def _set_pose(self, p: Dict[str, Any]) -> None:
        self._mc.set_pose(self._num(p, "z", 0.0), self._num(p, "roll", 0.0),
                          self._num(p, "pitch", 0.0), self._num(p, "yaw", 0.0))

    def _set_servo(self, p: Dict[str, Any]) -> None:
        self._mc.set_servo(int(self._num(p, "leg")), int(self._num(p, "joint")),
                           self._num(p, "angle"), bool(p.get("raw", False)))
