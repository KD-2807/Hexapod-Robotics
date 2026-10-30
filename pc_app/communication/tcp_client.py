"""TcpClient: Transport phía PC, kết nối tới TcpServer của ESP32 (mỗi gói là một dòng)."""
import select
import socket
from typing import Optional

from shared.common.constants import MAX_LINE_BYTES
from shared.interfaces.transport import Transport


class TcpClient(Transport):
    def __init__(self, host: str, port: int, connect_timeout: float = 3.0):
        self._host, self._port, self._connect_timeout = host, port, connect_timeout
        self._sock: Optional[socket.socket] = None
        self._buffer = b""

    def connect(self) -> None:
        sock = socket.create_connection((self._host, self._port), self._connect_timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)     # lệnh nhỏ: gửi ngay, không gom
        self._sock, self._buffer = sock, b""

    def send_line(self, line: str) -> None:
        if not self._sock:
            raise ConnectionError("Chưa kết nối")
        try:
            self._sock.sendall((line + "\n").encode("utf-8"))
        except OSError as exc:
            raise ConnectionError(str(exc)) from exc

    def receive_line(self, timeout: float) -> Optional[str]:
        sock = self._sock                       # bản sao cục bộ: close() có thể chạy song song
        if not sock:
            raise ConnectionError("Chưa kết nối")
        while b"\n" not in self._buffer:
            try:
                ready, _, _ = select.select([sock], [], [], timeout)
                if not ready:
                    return None
                chunk = sock.recv(1024)
            except (OSError, ValueError) as exc:     # ValueError: socket đã đóng (fd = -1)
                raise ConnectionError(str(exc)) from exc
            if not chunk:
                raise ConnectionError("Robot đã đóng kết nối")
            self._buffer += chunk
            if len(self._buffer) > 4 * MAX_LINE_BYTES and b"\n" not in self._buffer:
                self._buffer = b""                          # rác không có xuống dòng
            timeout = 0.0
        line, self._buffer = self._buffer.split(b"\n", 1)
        return line.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        sock, self._sock = self._sock, None
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    @property
    def is_connected(self) -> bool:
        return self._sock is not None
