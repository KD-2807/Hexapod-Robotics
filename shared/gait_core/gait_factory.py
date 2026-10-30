"""GaitFactory: tạo đối tượng dáng đi theo GaitType."""
from typing import Dict, Sequence, Type

from shared.common.enums import GaitType
from shared.gait_core.base_gait import BaseGait
from shared.gait_core.gait_config import GaitConfig
from shared.gait_core.ripple_gait import RippleGait
from shared.gait_core.rotation_gait import RotationGait
from shared.gait_core.tripod_gait import TripodGait
from shared.gait_core.wave_gait import WaveGait
from shared.robot_core.leg import Leg

_REGISTRY: Dict[GaitType, Type[BaseGait]] = {
    GaitType.TRIPOD: TripodGait,
    GaitType.WAVE: WaveGait,
    GaitType.RIPPLE: RippleGait,
    GaitType.ROTATION: RotationGait,
}


class GaitFactory:
    def __init__(self, config: GaitConfig, legs: Sequence[Leg]):
        self._config = config
        self._legs = legs

    def create(self, gait_type: GaitType) -> BaseGait:
        return _REGISTRY[gait_type](self._config, self._config.profiles[gait_type], self._legs)
