"""RobotStatus: dữ liệu trạng thái hiển thị trên UI (parse từ gói STATUS)."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RobotStatus:
    state: str = "UNKNOWN"
    gait: str = "tripod"
    speed: float = 0.0
    pose: Dict[str, float] = field(default_factory=lambda: {"z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0})
    angles: List[float] = field(default_factory=lambda: [0.0] * 18)
    battery_v: Optional[float] = None
    imu_roll: Optional[float] = None
    imu_pitch: Optional[float] = None
    error: Optional[Dict[str, str]] = None
    connected: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RobotStatus":
        imu = data.get("imu") or {}
        return cls(state=data.get("state", "UNKNOWN"), gait=data.get("gait", "tripod"),
                   speed=float(data.get("speed", 0.0)), pose=dict(data.get("pose", {})) or cls().pose,
                   angles=list(data.get("angles", [0.0] * 18)), battery_v=data.get("battery_v"),
                   imu_roll=imu.get("roll"), imu_pitch=imu.get("pitch"),
                   error=data.get("error"), connected=bool(data.get("connected", True)))
