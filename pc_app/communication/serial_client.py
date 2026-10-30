"""SerialClient (tùy chọn): Transport qua cáp USB-UART, cùng giao thức dòng JSON."""
from typing import Optional

from shared.interfaces.transport import Transport


class SerialClient(Transport):
    def __init__(self, port: str, baudrate: int = 115200):
        self._port, self._baud = port, baudrate
        self._serial = None

    def connect(self) -> None:
        try:
            import serial                     # pyserial: chỉ cần khi dùng USB
        except ImportError as exc:
            raise OSError("Cần cài pyserial: pip install pyserial") from exc
        self._serial = serial.Serial(self._port, self._baud, timeout=0)

    def send_line(self, line: str) -> None:
        if not self._serial:
            raise ConnectionError("Chưa kết nối")
        self._serial.write((line + "\n").encode("utf-8"))

    def receive_line(self, timeout: float) -> Optional[str]:
        if not self._serial:
            raise ConnectionError("Chưa kết nối")
        self._serial.timeout = timeout
        raw = self._serial.readline()
        return raw.decode("utf-8", errors="replace").strip() if raw.endswith(b"\n") else None

    def close(self) -> None:
        if self._serial:
            self._serial.close()
            self._serial = None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None
