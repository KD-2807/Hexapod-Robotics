from shared.common.enums import GaitType
from shared.gait_core.base_gait import BaseGait


class WaveGait(BaseGait):
    """Mỗi lần nhấc 1 chân (luôn 5 chân chạm đất). Chậm nhất, ổn định nhất."""
    gait_type = GaitType.WAVE
