"""BaseAction: một hành vi cấp cao; mỗi chu kỳ trả về độ dịch bàn chân + tư thế thân."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from shared.common.math_utils import Vec3
from shared.common.types import BodyPose
from shared.motion_core.context import MotionContext


@dataclass
class ActionOutput:
    foot_offsets: List[Vec3]
    pose: BodyPose


class BaseAction(ABC):
    name = "action"

    def __init__(self, ctx: MotionContext):
        self._ctx = ctx

    def start(self) -> None:
        """Gọi một lần khi action được kích hoạt."""

    @abstractmethod
    def update(self, dt: float) -> ActionOutput:
        ...

    @property
    def finished(self) -> bool:
        return False
