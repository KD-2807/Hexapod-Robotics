from shared.common.enums import GaitType
from shared.gait_core.base_gait import BaseGait


class TripodGait(BaseGait):
    """3 chân nhấc / 3 chân chống luân phiên. Nhanh nhất, là dáng đi mặc định."""
    gait_type = GaitType.TRIPOD
