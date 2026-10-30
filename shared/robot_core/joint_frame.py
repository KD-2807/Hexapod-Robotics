"""JointFrame: 18 góc khớp (độ) tại một thời điểm, thứ tự leg*3 + joint."""
import math
from typing import Iterable, List, Optional

from shared.common.constants import JOINTS_PER_LEG, NUM_SERVOS


class JointFrame:
    def __init__(self, angles: Optional[Iterable[float]] = None, timestamp: float = 0.0):
        self.angles: List[float] = list(angles) if angles is not None else [0.0] * NUM_SERVOS
        if len(self.angles) != NUM_SERVOS:
            raise ValueError("JointFrame cần đúng %d góc" % NUM_SERVOS)
        self.timestamp = timestamp

    @staticmethod
    def index(leg: int, joint: int) -> int:
        return leg * JOINTS_PER_LEG + joint

    def get(self, leg: int, joint: int) -> float:
        return self.angles[self.index(leg, joint)]

    def set(self, leg: int, joint: int, angle_deg: float) -> None:
        self.angles[self.index(leg, joint)] = angle_deg

    def copy(self) -> "JointFrame":
        return JointFrame(self.angles, self.timestamp)

    def is_finite(self) -> bool:
        return all(math.isfinite(a) for a in self.angles)

    def max_abs_diff(self, other: "JointFrame") -> float:
        return max(abs(a - b) for a, b in zip(self.angles, other.angles))
