"""Ánh xạ phím giữ -> vector vận tốc (không phụ thuộc thư viện UI)."""
from typing import Tuple

# phím -> thành phần vận tốc
_KEYS = {"w": (0.0, 1.0, 0.0), "s": (0.0, -1.0, 0.0), "a": (-1.0, 0.0, 0.0),
         "d": (1.0, 0.0, 0.0), "q": (0.0, 0.0, 1.0), "e": (0.0, 0.0, -1.0)}


class KeyboardMapper:
    """Gộp các phím đang giữ thành một vector (vx, vy, wz) kẹp trong [-1, 1]."""

    def __init__(self):
        self._held = set()

    def press(self, key: str) -> Tuple[float, float, float]:
        if key in _KEYS:
            self._held.add(key)
        return self.vector()

    def release(self, key: str) -> Tuple[float, float, float]:
        self._held.discard(key)
        return self.vector()

    def vector(self) -> Tuple[float, float, float]:
        vx = sum(_KEYS[k][0] for k in self._held)
        vy = sum(_KEYS[k][1] for k in self._held)
        wz = sum(_KEYS[k][2] for k in self._held)
        return (max(-1.0, min(1.0, vx)), max(-1.0, min(1.0, vy)), max(-1.0, min(1.0, wz)))
