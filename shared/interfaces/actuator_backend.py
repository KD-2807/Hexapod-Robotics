"""Lớp trừu tượng cho phần chấp hành (robot thật hoặc giả lập)."""
from abc import ABC, abstractmethod

from shared.robot_core.joint_frame import JointFrame


class ActuatorBackend(ABC):
    @abstractmethod
    def enable(self) -> bool:
        """Bật xuất xung servo. Trả về False nếu lỗi phần cứng."""

    @abstractmethod
    def disable(self) -> None:
        """Ngắt xung servo (servo thả lỏng)."""

    @abstractmethod
    def apply(self, frame: JointFrame) -> bool:
        """Xuất 18 góc khớp. Trả về False nếu lỗi phần cứng."""

    @abstractmethod
    def apply_raw_servo(self, leg: int, joint: int, servo_deg: float) -> bool:
        """Đặt thẳng góc servo (0..180, bỏ qua calibration) - dùng khi hiệu chỉnh."""
