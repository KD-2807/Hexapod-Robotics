"""GaitPhase: pha và thứ tự nhấc của 6 chân trong 1 chu kỳ chuẩn hóa t in [0,1)."""
from typing import Sequence, Tuple

from shared.gait_core.gait_config import GaitProfile


class GaitPhase:
    def __init__(self, duty: float, offsets: Sequence[float]):
        self.duty = duty
        self.offsets = list(offsets)

    @classmethod
    def from_profile(cls, profile: GaitProfile, leg_ids: Sequence[str]) -> "GaitPhase":
        slots = profile.swing_slots
        offsets = [0.0] * len(leg_ids)
        for slot_index, slot in enumerate(slots):
            for leg_id in slot:
                offsets[leg_ids.index(leg_id)] = (1.0 - slot_index / len(slots)) % 1.0
        return cls(profile.duty, offsets)

    def locate(self, t: float, leg: int) -> Tuple[bool, float]:
        """Trả về (đang_vung, u): u in [0,1] là tiến độ trong pha hiện tại. Pha vung đi trước pha đứng."""
        local = (t + self.offsets[leg]) % 1.0
        swing_len = 1.0 - self.duty
        if local < swing_len:
            return True, local / swing_len
        return False, (local - swing_len) / self.duty
