"""BasePosture: một bậc tự do của tư thế thân, có giới hạn."""
from abc import ABC, abstractmethod

from shared.common.math_utils import clamp
from shared.common.types import BodyPose


class BasePosture(ABC):
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def in_range(self, value: float) -> bool:
        return self.low <= value <= self.high

    def clamp(self, value: float) -> float:
        return clamp(value, self.low, self.high)

    @abstractmethod
    def apply(self, pose: BodyPose, value: float) -> BodyPose:
        """Trả về pose mới với bậc tự do này đặt bằng value."""
