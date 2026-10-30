"""Cấu hình hình học robot, đọc từ robot_config.json."""
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class LegSpec:
    id: str
    name: str
    x: float
    y: float
    yaw_deg: float
    group: str


@dataclass(frozen=True)
class RobotConfig:
    coxa: float
    femur: float
    tibia: float
    legs: Tuple[LegSpec, ...]
    stance_radius: float
    stand_height: float
    sit_height: float

    @property
    def sit_offset_z(self) -> float:
        """Độ dịch z của thân khi ngồi so với khi đứng (âm)."""
        return -(self.stand_height - self.sit_height)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RobotConfig":
        links, stance = data["link_lengths_mm"], data["stance"]
        legs = tuple(LegSpec(l["id"], l["name"], l["x"], l["y"], l["yaw_deg"], l["group"])
                     for l in data["legs"])
        return cls(links["coxa"], links["femur"], links["tibia"], legs,
                   stance["radius_mm"], stance["height_mm"], stance["sit_height_mm"])
