"""TcpServer (Python) cho robot giả lập: 1 client, mỗi gói là một dòng JSON."""
import queue
import socket
import threading
from typing import Optional

from shared.common.constants import MAX_LINE_BYTES
from shared.interfaces.transport import Transport


class TcpServer(Transport):
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self._host, self._port = host, port
        self._listener: Optional[socket.socket] = None
        self._client: Optional[socket.socket] = None
        self._lines: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        self._running = False
        self.client_dropped = False         # True nếu client vừa ngắt; đọc xong thì xóa

    @property
    def port(self) -> int:
        return self._listener.getsockname()[1] if self._listener else self._port

    def connect(self) -> None:
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind((self._host, self._port))
        self._listener.listen(1)
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self) -> None:
        while self._running:
            try:
                conn, _ = self._listener.accept()
            except OSError:
                return
            with self._lock:
                if self._client:                       # client mới thay client cũ
                    self._close_client()
                self._client = conn
            threading.Thread(target=self._read_loop, args=(conn,), daemon=True).start()

    def _read_loop(self, conn: socket.socket) -> None:
        buffer = b""
        try:
            while self._running:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        self._lines.put(line.decode("utf-8", errors="replace"))
                if len(buffer) > MAX_LINE_BYTES:       # dòng quá dài: bỏ
                    buffer = b""
        except OSError:
            pass
        with self._lock:
            if self._client is conn:
                self._close_client()
                self.client_dropped = True

    def _close_client(self) -> None:
        try:
            self._client.close()
        except OSError:
            pass
        self._client = None

    def send_line(self, line: str) -> None:
        with self._lock:
            if self._client:
                try:
                    self._client.sendall((line + "\n").encode("utf-8"))
                except OSError:
                    self._close_client()
                    self.client_dropped = True

    def receive_line(self, timeout: float = 0.0) -> Optional[str]:
        try:
            return self._lines.get(timeout=timeout) if timeout > 0 else self._lines.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        self._running = False
        with self._lock:
            if self._client:
                self._close_client()
        if self._listener:
            self._listener.close()
            self._listener = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None
