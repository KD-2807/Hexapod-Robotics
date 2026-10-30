"""SimBackend: ActuatorBackend giả lập - chỉ lưu khung góc cuối để hiển thị/kiểm thử."""
from typing import Optional

from shared.common.constants import NUM_SERVOS
from shared.interfaces.actuator_backend import ActuatorBackend
from shared.robot_core.joint_frame import JointFrame
from shared.robot_core.servo_calibration import CalibrationTable


class SimBackend(ActuatorBackend):
    def __init__(self, calibration: Optional[CalibrationTable] = None):
        self._calibration = calibration
        self.enabled = False
        self.last_frame = JointFrame()
        self.raw_servo_deg = {}
        self.fail_next_apply = False        # dùng để mô phỏng lỗi I2C khi kiểm thử

    def enable(self) -> bool:
        self.enabled = True
        return True

    def disable(self) -> None:
        self.enabled = False

    def apply(self, frame: JointFrame) -> bool:
        if not self.enabled or self.fail_next_apply:
            self.fail_next_apply = False
            return False
        self.last_frame = frame.copy()
        return True

    def apply_raw_servo(self, leg: int, joint: int, servo_deg: float) -> bool:
        if not self.enabled:
            return False
        self.raw_servo_deg[(leg, joint)] = servo_deg
        return True

    def servo_angles(self):
        """18 góc servo (0..180) tương ứng khung cuối - cần calibration."""
        if self._calibration is None:
            raise RuntimeError("SimBackend chưa có calibration")
        return [self._calibration.get(i // 3, i % 3).servo_angle(a)
                for i, a in enumerate(self.last_frame.angles[:NUM_SERVOS])]
