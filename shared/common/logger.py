"""Logger nhẹ: ghi ra console và giữ vòng đệm để LogPanel hiển thị."""
import logging
from collections import deque
from typing import Callable, Deque, List

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class _RingHandler(logging.Handler):
    def __init__(self, capacity: int = 500):
        super().__init__()
        self.records: Deque[str] = deque(maxlen=capacity)
        self.listeners: List[Callable[[str], None]] = []

    def emit(self, record: logging.LogRecord) -> None:
        line = self.format(record)
        self.records.append(line)
        for listener in list(self.listeners):
            listener(line)


_ring = _RingHandler()
_ring.setFormatter(logging.Formatter(_FORMAT, "%H:%M:%S"))
_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter(_FORMAT, "%H:%M:%S"))


class Logger:
    """Bọc logging chuẩn; mọi Logger dùng chung một vòng đệm."""

    def __init__(self, name: str, level: int = logging.INFO):
        self._log = logging.getLogger(name)
        self._log.setLevel(level)
        self._log.propagate = False
        for handler in (_ring, _console):
            if handler not in self._log.handlers:
                self._log.addHandler(handler)

    def debug(self, msg: str, *args) -> None:
        self._log.debug(msg, *args)

    def info(self, msg: str, *args) -> None:
        self._log.info(msg, *args)

    def warning(self, msg: str, *args) -> None:
        self._log.warning(msg, *args)

    def error(self, msg: str, *args) -> None:
        self._log.error(msg, *args)

    @staticmethod
    def add_listener(listener: Callable[[str], None]) -> None:
        _ring.listeners.append(listener)

    @staticmethod
    def set_console(enabled: bool) -> None:
        _console.setLevel(logging.INFO if enabled else logging.CRITICAL + 1)

    @staticmethod
    def history() -> List[str]:
        return list(_ring.records)
