"""RobotClient: gửi Command, nhận Response/STATUS qua một Transport; tự gửi HEARTBEAT."""
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from shared.common.command_codec import CommandDecoder, CommandEncoder, ProtocolError
from shared.common.constants import STATUS_SEQ
from shared.common.enums import CommandType, ResponseType
from shared.common.logger import Logger
from shared.common.protocol import Command, Response
from shared.interfaces.transport import Transport

TransportFactory = Callable[[str, int], Transport]


class RobotClient:
    def __init__(self, transport_factory: TransportFactory, response_timeout: float = 1.0,
                 heartbeat_interval: float = 0.3):
        self._factory = transport_factory
        self._timeout = response_timeout
        self._heartbeat_interval = heartbeat_interval
        self._transport: Optional[Transport] = None
        self._seq = 0
        self._lock = threading.Lock()
        self._pending: Dict[int, "_Waiter"] = {}
        self._running = False
        self._status_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._connection_listeners: List[Callable[[bool, str], None]] = []
        self._log = Logger("robot_client")

    # ------------------------------------------------------------------ listeners
    def add_status_listener(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._status_listeners.append(fn)

    def add_connection_listener(self, fn: Callable[[bool, str], None]) -> None:
        self._connection_listeners.append(fn)

    # ------------------------------------------------------------------ kết nối
    @property
    def is_connected(self) -> bool:
        return self._running and self._transport is not None and self._transport.is_connected

    def connect(self, host: str, port: int) -> None:
        self.disconnect()
        transport = self._factory(host, port)
        transport.connect()                       # ném OSError nếu thất bại
        self._transport, self._running = transport, True
        threading.Thread(target=self._reader_loop, args=(transport,), daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, args=(transport,), daemon=True).start()
        self._notify_connection(True, "Đã kết nối %s:%d" % (host, port))

    def disconnect(self, reason: str = "Đã ngắt kết nối") -> None:
        was_running, self._running = self._running, False
        transport, self._transport = self._transport, None
        if transport:
            transport.close()
        self._fail_pending()
        if was_running:
            self._notify_connection(False, reason)

    # ------------------------------------------------------------------ gửi lệnh
    def send(self, cmd: CommandType, params: Optional[Dict[str, Any]] = None, wait: bool = True) -> Optional[Response]:
        """wait=True: chờ ACK/ERROR cùng seq (ném TimeoutError nếu quá hạn). wait=False: gửi rồi bỏ qua."""
        transport = self._transport
        if not self.is_connected or transport is None:
            raise ConnectionError("Chưa kết nối tới robot")
        with self._lock:
            self._seq = self._seq % 1_000_000 + 1
            seq = self._seq
            waiter = _Waiter()
            if wait:
                self._pending[seq] = waiter
        try:
            transport.send_line(CommandEncoder.encode(Command(seq, cmd, params or {})))
        except (ConnectionError, OSError) as exc:
            self._pending.pop(seq, None)
            self.disconnect("Mất kết nối: %s" % exc)
            raise ConnectionError(str(exc)) from exc
        if not wait:
            return None
        if not waiter.event.wait(self._timeout):
            self._pending.pop(seq, None)
            raise TimeoutError("Robot không phản hồi lệnh %s" % cmd.value)
        if waiter.response is None:
            raise ConnectionError("Mất kết nối khi đang chờ phản hồi")
        return waiter.response

    # ------------------------------------------------------------------ luồng nền
    def _reader_loop(self, transport: Transport) -> None:
        while self._running and transport is self._transport:
            try:
                line = transport.receive_line(0.2)
            except (ConnectionError, OSError) as exc:
                if transport is self._transport:
                    self.disconnect("Mất kết nối: %s" % exc)
                return
            if line:
                self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        try:
            response = CommandDecoder.decode_response(line)
        except ProtocolError as exc:
            self._log.warning("Bỏ qua gói hỏng: %s", exc.message)
            return
        if response.type == ResponseType.STATUS and response.seq == STATUS_SEQ:
            for listener in list(self._status_listeners):
                listener(response.data)
            return
        waiter = self._pending.pop(response.seq, None)
        if waiter:
            waiter.response = response
            waiter.event.set()

    def _heartbeat_loop(self, transport: Transport) -> None:
        while self._running and transport is self._transport:
            try:
                self.send(CommandType.HEARTBEAT, wait=False)
            except (ConnectionError, OSError):
                return
            time.sleep(self._heartbeat_interval)

    def _fail_pending(self) -> None:
        for waiter in list(self._pending.values()):
            waiter.event.set()                    # response=None -> ConnectionError ở người chờ
        self._pending.clear()

    def _notify_connection(self, connected: bool, message: str) -> None:
        for listener in list(self._connection_listeners):
            listener(connected, message)


class _Waiter:
    def __init__(self):
        self.event = threading.Event()
        self.response: Optional[Response] = None
