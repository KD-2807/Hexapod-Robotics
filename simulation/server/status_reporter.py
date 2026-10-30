"""StatusReporter: dựng gói STATUS và đẩy định kỳ về PC."""
from typing import Any, Callable, Dict

from shared.common.constants import STATUS_SEQ
from shared.common.protocol import Response
from shared.motion_core.motion_controller import MotionController


class StatusReporter:
    def __init__(self, controller: MotionController, rate_hz: float, extra: Callable[[], Dict[str, Any]] = dict):
        self._mc = controller
        self._period = 1.0 / rate_hz
        self._extra = extra
        self._elapsed = 0.0

    def build(self, connected: bool) -> Dict[str, Any]:
        data = self._mc.snapshot()
        data.update(self._extra())
        data["connected"] = connected
        return data

    def due(self, dt: float) -> bool:
        self._elapsed += dt
        if self._elapsed >= self._period:
            self._elapsed = 0.0
            return True
        return False

    def packet(self, connected: bool) -> Response:
        return Response.status(STATUS_SEQ, self.build(connected))
