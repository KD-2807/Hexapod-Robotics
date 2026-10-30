"""Cấu hình an toàn, đọc từ safety_config.json."""
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from shared.common.enums import JointType


@dataclass(frozen=True)
class SafetyConfig:
    watchdog_timeout_s: float
    max_joint_speed_dps: float
    angle_margin_deg: float
    joint_limits: Dict[JointType, Tuple[float, float]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyConfig":
        lim = data["joint_limits_deg"]
        limits = {JointType.COXA: tuple(lim["coxa"]), JointType.FEMUR: tuple(lim["femur"]),
                  JointType.TIBIA: tuple(lim["tibia"])}
        return cls(data["watchdog_timeout_s"], data["max_joint_speed_dps"],
                   data["angle_margin_deg"], limits)
