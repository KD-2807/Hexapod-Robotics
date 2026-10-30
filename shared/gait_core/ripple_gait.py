from shared.common.enums import GaitType
from shared.gait_core.base_gait import BaseGait


class RippleGait(BaseGait):
    """Mỗi lần nhấc 2 chân lệch pha (luôn 4 chân chạm đất)."""
    gait_type = GaitType.RIPPLE
