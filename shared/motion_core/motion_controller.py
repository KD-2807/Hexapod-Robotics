"""MotionController: nhận lệnh cấp cao, chọn action/gait, mỗi chu kỳ tạo JointFrame và đưa xuống backend."""
from typing import Any, Dict, Optional

from shared.common.enums import CommandType, ErrorCode, GaitType, JointType, LegId, RobotState
from shared.common.math_utils import clamp, move_towards
from shared.common.types import BodyPose, Velocity
from shared.gait_core.gait_config import GaitConfig
from shared.interfaces.actuator_backend import ActuatorBackend
from shared.motion_core.actions.base_action import BaseAction
from shared.motion_core.actions.body_pose import BodyPoseAction
from shared.motion_core.actions.sit_down import SitDown
from shared.motion_core.actions.special import SPECIAL_ACTIONS, SpecialAction, create_special
from shared.motion_core.actions.stand_up import StandUp
from shared.motion_core.actions.strafe import Strafe
from shared.motion_core.actions.turn import Turn
from shared.motion_core.actions.walk import Walk
from shared.motion_core.context import MotionContext
from shared.motion_core.errors import MotionError
from shared.motion_core.state_machine import StateMachine
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.joint_frame import JointFrame
from shared.robot_core.motion_coordinator import MotionCoordinator
from shared.robot_core.safety_guard import SafetyGuard

_ZERO = Velocity()
_USER_GAITS = (GaitType.TRIPOD, GaitType.WAVE, GaitType.RIPPLE)
SPEED_RANGE = (0.1, 1.0)


class MotionController:
    def __init__(self, hexapod: Hexapod, coordinator: MotionCoordinator, guard: SafetyGuard,
                 backend: ActuatorBackend, ctx: MotionContext, gait_config: GaitConfig,
                 pose_margin_deg: float = 2.0):
        self.hexapod = hexapod
        self._coordinator = coordinator
        self._guard = guard
        self._backend = backend
        self._ctx = ctx
        self._gait_config = gait_config
        self._pose_margin = pose_margin_deg
        self._machine = StateMachine()

        self._hold = BodyPoseAction(ctx)
        self._walk, self._strafe, self._turn = Walk(ctx), Strafe(ctx), Turn(ctx)
        self._action: BaseAction = self._hold

        self._desired = _ZERO
        self._pending_sit = False
        self._requested_gait = ctx.gait_type
        self._manual = False
        self._frame = JointFrame()
        self._error: Optional[Dict[str, str]] = None

    # ------------------------------------------------------------------ trạng thái
    @property
    def state(self) -> RobotState:
        return self._machine.state

    @property
    def frame(self) -> JointFrame:
        return self._frame

    @property
    def body_pose(self) -> BodyPose:
        """Tư thế hiện tại, cùng quy ước với BodyKinematics và firmware."""
        return self._ctx.posture.current

    def stance_phase_mask(self):
        """Lịch pha chống hiện tại, KHÔNG phải cảm biến tiếp xúc."""
        if self.state != RobotState.WALKING or not isinstance(self._action, Walk):
            return [True]*len(self.hexapod.legs)
        gait = self._action._gait()
        return gait.stance_phase_mask(self._action.shape(self._ctx.velocity))

    def accepts(self, command: CommandType) -> bool:
        return self._machine.accepts(command)

    def snapshot(self) -> Dict[str, Any]:
        pose = self._ctx.posture.current
        return {"state": self.state.value, "gait": self._requested_gait.value,
                "speed": round(self._ctx.speed, 2),
                "pose": {"z": round(pose.z, 1), "roll": round(pose.roll, 1),
                         "pitch": round(pose.pitch, 1), "yaw": round(pose.yaw, 1)},
                "angles": [round(a, 1) for a in self._frame.angles],
                "error": self._error}

    # ------------------------------------------------------------------ lệnh
    def enable(self) -> None:
        self._machine.require(CommandType.ENABLE)
        if self.state != RobotState.IDLE:
            return
        if not self._backend.enable():
            raise MotionError(ErrorCode.HARDWARE, "Không bật được driver servo")
        self._ctx.posture.reset(self._ctx.sit_pose)
        self._ctx.velocity = _ZERO
        self._desired = _ZERO
        first = self._coordinator.compute(self._ctx.zero_offsets(), self._ctx.sit_pose).frame
        self._guard.reset(first)
        if not self._backend.apply(first):
            raise MotionError(ErrorCode.HARDWARE, "Không ghi được servo")
        self._frame = first
        self._machine.transition(RobotState.SITTING)
        self._start(SitDown(self._ctx))

    def disable(self) -> None:
        self._machine.require(CommandType.DISABLE)
        if self.state == RobotState.IDLE:
            return
        if not (isinstance(self._action, SitDown) and self._action.finished):
            raise MotionError(ErrorCode.BAD_STATE, "Cần ngồi xuống xong trước khi tắt servo")
        self._backend.disable()
        self._manual = False
        self._machine.transition(RobotState.IDLE)

    def stand_up(self) -> None:
        self._machine.require(CommandType.STAND_UP)
        if self.state == RobotState.IDLE:
            self.enable()
        if self.state == RobotState.STANDING or isinstance(self._action, StandUp):
            return
        self._manual = False
        self._pending_sit = False
        self._ctx.posture.walking = False
        self._start(StandUp(self._ctx))

    def sit_down(self) -> None:
        self._machine.require(CommandType.SIT_DOWN)
        self._desired = _ZERO
        if self.state == RobotState.WALKING:
            self._pending_sit = True          # dừng hẳn rồi mới ngồi
        elif self.state == RobotState.STANDING:
            self._begin_sit()

    def move(self, vx: float, vy: float, wz: float, speed: Optional[float] = None) -> None:
        self._machine.require(CommandType.MOVE)
        for name, value in (("vx", vx), ("vy", vy), ("wz", wz)):
            if not -1.0 <= value <= 1.0:
                raise MotionError(ErrorCode.BAD_PARAMS, "%s phải trong [-1, 1]" % name)
        if speed is not None:
            self.set_speed(speed)
        if self._busy_with_special():
            raise MotionError(ErrorCode.BAD_STATE, "Đang chạy action đặc biệt, hãy STOP trước")
        self._desired = Velocity(vx, vy, wz)
        self._pending_sit = False

    def stop(self) -> None:
        self._machine.require(CommandType.STOP)
        self._desired = _ZERO
        if self._busy_with_special():
            self._start(self._hold)

    def set_gait(self, gait: GaitType) -> None:
        self._machine.require(CommandType.SET_GAIT)
        if gait not in _USER_GAITS:
            raise MotionError(ErrorCode.BAD_PARAMS, "Dáng đi phải là tripod/wave/ripple")
        self._requested_gait = gait
        self._apply_requested_gait()

    def set_speed(self, speed: float) -> None:
        self._machine.require(CommandType.SET_SPEED)
        if not SPEED_RANGE[0] <= speed <= SPEED_RANGE[1]:
            raise MotionError(ErrorCode.BAD_PARAMS, "speed phải trong [%.1f, %.1f]" % SPEED_RANGE)
        self._ctx.speed = speed

    def set_pose(self, z: float, roll: float, pitch: float, yaw: float) -> None:
        self._machine.require(CommandType.SET_POSE)
        bad = self._ctx.posture.validate(z, roll, pitch, yaw)
        if bad:
            raise MotionError(ErrorCode.BAD_PARAMS, "%s vượt giới hạn cho phép" % bad)
        pose = self._ctx.posture.compose(z, roll, pitch, yaw)
        if not self._pose_feasible(pose):
            raise MotionError(ErrorCode.LIMIT, "Tổ hợp tư thế vượt tầm với của chân")
        self._ctx.posture.set_target(pose)

    def run_action(self, name: str) -> None:
        self._machine.require(CommandType.ACTION)
        if name not in SPECIAL_ACTIONS:
            raise MotionError(ErrorCode.BAD_PARAMS, "Action không tồn tại: %s" % name)
        if self._busy_with_special() or self.state != RobotState.STANDING:
            raise MotionError(ErrorCode.BAD_STATE, "Chỉ chạy action khi đang đứng yên")
        self._start(create_special(name, self._ctx))

    def emergency_stop(self) -> None:
        self._backend.disable()
        self._fail(ErrorCode.ESTOP, "Dừng khẩn cấp")

    def reset(self) -> None:
        self._machine.require(CommandType.RESET)
        if self.state == RobotState.ERROR:
            self._machine.transition(RobotState.IDLE)
        self._error = None
        self._manual = False
        self._desired = _ZERO
        self._ctx.velocity = _ZERO
        self._pending_sit = False
        self._start(self._hold)

    def set_servo(self, leg: int, joint: int, angle: float, raw: bool = False) -> None:
        """Chế độ test (chỉ khi đang ngồi): đặt 1 servo. raw=True: góc servo 0..180, bỏ qua calibration."""
        self._machine.require(CommandType.SET_SERVO)
        if not (0 <= leg < 6 and 0 <= joint < 3):
            raise MotionError(ErrorCode.BAD_PARAMS, "leg phải 0..5, joint phải 0..2")
        if raw:
            if not 0.0 <= angle <= 180.0:
                raise MotionError(ErrorCode.BAD_PARAMS, "góc servo phải trong [0, 180]")
            ok = self._backend.apply_raw_servo(leg, joint, angle)
        else:
            limit = self.hexapod.legs[leg].joints[joint]
            if not limit.min_deg <= angle <= limit.max_deg:
                raise MotionError(ErrorCode.BAD_PARAMS, "góc khớp phải trong [%.0f, %.0f]" % (limit.min_deg, limit.max_deg))
            frame = self._frame.copy()
            frame.set(leg, joint, angle)
            ok = self._backend.apply(frame)
            if ok:
                self._frame = frame
        if not ok:
            raise MotionError(ErrorCode.HARDWARE, "Ghi servo thất bại")
        self._manual = True

    def on_link_lost(self) -> None:
        """Mất heartbeat/kết nối: dừng đi rồi ngồi xuống."""
        self._desired = _ZERO
        if self._busy_with_special():
            self._start(self._hold)
        if self.state in (RobotState.STANDING, RobotState.WALKING):
            self._pending_sit = True

    # ------------------------------------------------------------------ vòng lặp điều khiển
    def update(self, dt: float) -> None:
        if self.state in (RobotState.IDLE, RobotState.ERROR) or self._manual:
            return
        self._update_locomotion(dt)
        out = self._action.update(dt)
        result = self._coordinator.compute(out.foot_offsets, out.pose)
        safe = self._guard.filter(result.frame, dt)
        if not result.reachable:
            return self._fail(ErrorCode.LIMIT, "Bàn chân ngoài tầm với của chân")
        if not safe.ok:
            return self._fail(ErrorCode.LIMIT, safe.reason)
        if not self._backend.apply(safe.frame):
            return self._fail(ErrorCode.HARDWARE, "Lỗi I2C khi ghi servo")
        self._frame = safe.frame
        self._finish_transitions()

    # ------------------------------------------------------------------ nội bộ
    def _pose_feasible(self, pose: BodyPose) -> bool:
        """Tư thế đứng yên có nằm trong tầm với và cách giới hạn khớp >= biên an toàn không."""
        result = self._coordinator.compute(self._ctx.zero_offsets(), pose)
        if not result.reachable:
            return False
        margin = self._pose_margin
        return all(joint.min_deg + margin <= result.frame.get(leg.index, joint.type) <= joint.max_deg - margin
                   for leg in self.hexapod.legs for joint in leg.joints)

    def _start(self, action: BaseAction) -> None:
        self._action = action
        action.start()

    def _busy_with_special(self) -> bool:
        return isinstance(self._action, SpecialAction)

    def _begin_sit(self) -> None:
        self._pending_sit = False
        self._ctx.posture.walking = False
        self._machine.transition(RobotState.SITTING)
        self._start(SitDown(self._ctx))

    def _apply_requested_gait(self) -> None:
        if self.state != RobotState.WALKING and self._requested_gait != self._ctx.gait_type:
            self._ctx.gait_type = self._requested_gait
            self._ctx.gait(self._requested_gait).reset()

    @staticmethod
    def _family(v: Velocity) -> Optional[str]:
        if v.is_zero():
            return None
        return "turn" if abs(v.vx) < 1e-3 and abs(v.vy) < 1e-3 else "translate"

    def _action_for(self, v: Velocity) -> BaseAction:
        if self._family(v) == "turn":
            return self._turn
        if abs(v.vy) < 1e-3 and abs(v.wz) < 1e-3:
            return self._strafe
        return self._walk

    def _update_locomotion(self, dt: float) -> None:
        if self.state not in (RobotState.STANDING, RobotState.WALKING):
            return
        if self._pending_sit and self._ctx.velocity.is_zero():
            return self._begin_sit()
        if self.state == RobotState.STANDING:
            self._apply_requested_gait()

        active, wanted = self._family(self._ctx.velocity), self._family(self._desired)
        switching = active is not None and wanted is not None and active != wanted
        want_walk = not self._desired.is_zero() or not self._ctx.velocity.is_zero()
        self._ctx.posture.walking = want_walk
        hold = switching or self._pending_sit or self._busy_with_special() or (
            want_walk and not self._ctx.posture.in_walking_envelope())
        target = _ZERO if hold else self._desired
        self._ctx.velocity = self._ramp(self._ctx.velocity, target, dt)

        moving = not self._ctx.velocity.is_zero() or not target.is_zero()
        if self._ctx.velocity.is_zero() and self._desired.is_zero():
            self._ctx.posture.walking = False
        if moving:
            if self.state == RobotState.STANDING:
                self._machine.transition(RobotState.WALKING)
            self._action = self._action_for(self._ctx.velocity if not self._ctx.velocity.is_zero() else target)
        elif self.state == RobotState.WALKING:
            self._machine.transition(RobotState.STANDING)
            self._start(self._hold)

    def _ramp(self, current: Velocity, target: Velocity, dt: float) -> Velocity:
        step = self._gait_config.velocity_ramp_per_s * dt
        return Velocity(move_towards(current.vx, target.vx, step),
                        move_towards(current.vy, target.vy, step),
                        move_towards(current.wz, target.wz, step))

    def _finish_transitions(self) -> None:
        if self.state == RobotState.SITTING and isinstance(self._action, StandUp) and self._action.finished:
            self._machine.transition(RobotState.STANDING)
            self._start(self._hold)
        elif isinstance(self._action, SpecialAction) and self._action.finished:
            self._start(self._hold)

    def _fail(self, code: ErrorCode, message: str) -> None:
        self._machine.fail()
        self._error = {"code": code.value, "message": message}
        self._desired = _ZERO
        self._ctx.velocity = _ZERO
        self._pending_sit = False
        self._manual = False
        self._ctx.posture.walking = False
        self._backend.disable()
