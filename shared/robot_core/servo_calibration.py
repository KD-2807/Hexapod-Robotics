"""Calibration servo: góc khớp (độ) <-> góc servo (0..180) <-> độ rộng xung (µs)."""
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from shared.common.math_utils import clamp, lerp
from shared.common.enums import JointType
from shared.robot_core.robot_config import RobotConfig


@dataclass(frozen=True)
class ServoCalibration:
    offset_deg: float = 90.0     # góc servo khi góc khớp = 0
    direction: int = 1           # +1 hoặc -1
    pulse_min_us: float = 500.0  # xung tại 0°
    pulse_max_us: float = 2400.0  # xung tại 180°

    def servo_angle(self, joint_deg: float) -> float:
        return clamp(self.offset_deg + self.direction * joint_deg, 0.0, 180.0)

    def joint_angle(self, servo_deg: float) -> float:
        return (servo_deg - self.offset_deg) * self.direction

    def pulse_us(self, servo_deg: float) -> float:
        return lerp(self.pulse_min_us, self.pulse_max_us, clamp(servo_deg, 0.0, 180.0) / 180.0)


class CalibrationTable:
    """18 ServoCalibration, truy cập theo (leg_index, JointType)."""

    def __init__(self, entries: Dict[Tuple[int, int], ServoCalibration]):
        self._entries = entries

    def get(self, leg: int, joint: int) -> ServoCalibration:
        return self._entries[(leg, int(joint))]

    @classmethod
    def from_dict(cls, data: Dict[str, Any], robot: RobotConfig) -> "CalibrationTable":
        leg_index = {spec.id: i for i, spec in enumerate(robot.legs)}
        entries = {}
        for item in data["servos"]:
            key = (leg_index[item["leg"]], int(JointType[item["joint"].upper()]))
            entries[key] = ServoCalibration(item["offset_deg"], item["direction"],
                                            item["pulse_min_us"], item["pulse_max_us"])
        missing = [(l, j) for l in range(len(robot.legs)) for j in range(3) if (l, j) not in entries]
        if missing:
            raise ValueError("servo_calibration.json thiếu servo: %s" % missing)
        return cls(entries)
