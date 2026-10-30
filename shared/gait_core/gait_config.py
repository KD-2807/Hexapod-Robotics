"""Cấu hình dáng đi, đọc từ gait_config.json."""
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from shared.common.enums import GaitType


@dataclass(frozen=True)
class GaitProfile:
    duty: float                              # hệ số chu kỳ beta = thời gian pha đứng / chu kỳ
    cycle_time_s: float
    swing_slots: Tuple[Tuple[str, ...], ...]  # các nhóm chân nhấc lần lượt trong 1 chu kỳ


@dataclass(frozen=True)
class GaitConfig:
    step_length: float
    step_height: float
    turn_angle_deg: float
    max_stride: float
    lift_ramp: float
    velocity_ramp_per_s: float
    default_gait: GaitType
    default_speed: float
    profiles: Dict[GaitType, GaitProfile]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GaitConfig":
        profiles = {GaitType(name): GaitProfile(p["duty"], p["cycle_time_s"],
                                                tuple(tuple(slot) for slot in p["swing_slots"]))
                    for name, p in data["gaits"].items()}
        return cls(data["step_length_mm"], data["step_height_mm"], data["turn_angle_deg_per_cycle"],
                   data["max_stride_mm"], data["lift_ramp_mm"], data["velocity_ramp_per_s"],
                   GaitType(data["default_gait"]), data["default_speed"], profiles)
