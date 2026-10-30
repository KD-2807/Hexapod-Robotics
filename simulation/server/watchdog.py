"""Watchdog: mất heartbeat quá timeout -> gọi callback một lần (robot dừng và ngồi xuống)."""
from typing import Callable


class Watchdog:
    def __init__(self, timeout_s: float, on_timeout: Callable[[], None]):
        self._timeout = timeout_s
        self._on_timeout = on_timeout
        self._elapsed = 0.0
        self._armed = False
        self._fired = False

    def feed(self) -> None:
        """Gọi khi nhận bất kỳ gói nào từ PC."""
        self._elapsed, self._armed, self._fired = 0.0, True, False

    def disarm(self) -> None:
        self._armed = False

    def trigger(self) -> None:
        """Kích hoạt ngay (ví dụ mất kết nối TCP)."""
        if self._armed and not self._fired:
            self._fired = True
            self._on_timeout()

    def update(self, dt: float) -> None:
        if not self._armed or self._fired:
            return
        self._elapsed += dt
        if self._elapsed > self._timeout:
            self.trigger()
