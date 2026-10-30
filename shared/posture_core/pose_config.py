"""Cấu hình tư thế thân, đọc từ pose_config.json."""
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class PoseConfig:
    z_limits: Tuple[float, float]
    roll_limit: float
    pitch_limit: float
    yaw_limit: float
    z_rate: float                  # mm/s
    angle_rate: float              # độ/s
    walk_z_limits: Tuple[float, float]   # vùng tư thế cho phép khi đang bước (hẹp hơn khi đứng yên)
    walk_roll_limit: float
    walk_pitch_limit: float
    walk_yaw_limit: float
    check_margin_deg: float        # biên cách giới hạn khớp khi kiểm tra tư thế tĩnh

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PoseConfig":
        return cls(tuple(data["z_limits_mm"]), data["roll_limit_deg"], data["pitch_limit_deg"],
                   data["yaw_limit_deg"], data["z_rate_mm_s"], data["angle_rate_deg_s"],
                   tuple(data["walk_z_limits_mm"]), data["walk_roll_limit_deg"],
                   data["walk_pitch_limit_deg"], data["walk_yaw_limit_deg"], data["pose_check_margin_deg"])
