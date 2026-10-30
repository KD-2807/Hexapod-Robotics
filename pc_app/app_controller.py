"""AppController: cầu nối UI <-> RobotClient. Không phụ thuộc thư viện UI nên test được."""
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from pc_app.models.robot_status import RobotStatus
from pc_app.robot_client import RobotClient
from shared.common.enums import CommandType, ResponseType
from shared.common.logger import Logger


class AppController:
    def __init__(self, client: RobotClient, config: Dict[str, Any]):
        self._client = client
        self._cfg = config
        self._log = Logger("app")
        self._pool = ThreadPoolExecutor(max_workers=1)            # lệnh được gửi tuần tự, không chặn UI
        self._status_listeners: List[Callable[[RobotStatus], None]] = []
        self._connection_listeners: List[Callable[[bool, str], None]] = []
        self._vector = (0.0, 0.0, 0.0)
        self._vector_changed = threading.Event()
        self._speed = float(config.get("default_speed", 0.6))
        self._stop_repeater = threading.Event()
        self._repeater: Optional[threading.Thread] = None
        client.add_status_listener(lambda d: self._emit_status(RobotStatus.from_dict(d)))
        client.add_connection_listener(self._on_connection)

    # ------------------------------------------------------------------ đăng ký lắng nghe
    def add_status_listener(self, fn: Callable[[RobotStatus], None]) -> None:
        self._status_listeners.append(fn)

    def add_connection_listener(self, fn: Callable[[bool, str], None]) -> None:
        self._connection_listeners.append(fn)

    def _emit_status(self, status: RobotStatus) -> None:
        for fn in list(self._status_listeners):
            fn(status)

    def _on_connection(self, connected: bool, message: str) -> None:
        self._log.info(message)
        if connected:
            self._start_repeater()
        else:
            self._stop_repeater.set()
            self._vector = (0.0, 0.0, 0.0)
        for fn in list(self._connection_listeners):
            fn(connected, message)

    # ------------------------------------------------------------------ kết nối
    def connect(self, host: str, port: int) -> None:
        def job() -> None:
            try:
                self._client.connect(host, port)
            except OSError as exc:
                self._log.error("Không kết nối được %s:%d - %s", host, port, exc)
                for fn in list(self._connection_listeners):
                    fn(False, "Kết nối thất bại: %s" % exc)
        self._pool.submit(job)

    def disconnect(self) -> None:
        self._pool.submit(self._client.disconnect)

    # ------------------------------------------------------------------ lệnh đơn
    def command(self, cmd: CommandType, **params: Any) -> None:
        """Gửi lệnh bất đồng bộ; ERROR/timeout được ghi vào log."""
        self._pool.submit(self._send_and_log, cmd, params)

    def _send_and_log(self, cmd: CommandType, params: Dict[str, Any]) -> None:
        try:
            response = self._client.send(cmd, params)
        except (ConnectionError, TimeoutError, OSError) as exc:
            self._log.error("%s: %s", cmd.value, exc)
            return
        if response and response.type == ResponseType.ERROR:
            self._log.warning("%s bị từ chối [%s]: %s", cmd.value, response.data.get("code"),
                              response.data.get("message"))
        else:
            self._log.info("%s OK", cmd.value)

    def enable(self) -> None: self.command(CommandType.ENABLE)
    def disable(self) -> None: self.command(CommandType.DISABLE)
    def stand_up(self) -> None: self.command(CommandType.STAND_UP)
    def sit_down(self) -> None: self.command(CommandType.SIT_DOWN)
    def reset(self) -> None: self.command(CommandType.RESET)
    def get_status(self) -> None: self.command(CommandType.GET_STATUS)
    def run_action(self, name: str) -> None: self.command(CommandType.ACTION, name=name)
    def set_gait(self, gait: str) -> None: self.command(CommandType.SET_GAIT, gait=gait)

    def stop(self) -> None:
        self.set_direction(0.0, 0.0, 0.0)

    def emergency_stop(self) -> None:
        """Ưu tiên cao nhất: gửi thẳng trên luồng gọi, không chờ hàng đợi."""
        self._vector = (0.0, 0.0, 0.0)
        try:
            self._client.send(CommandType.EMERGENCY_STOP, wait=False)
            self._log.warning("ĐÃ GỬI DỪNG KHẨN CẤP")
        except (ConnectionError, OSError) as exc:
            self._log.error("Không gửi được dừng khẩn cấp: %s", exc)

    def set_speed(self, speed: float) -> None:
        self._speed = speed
        self.command(CommandType.SET_SPEED, speed=speed)

    def set_pose(self, z: float, roll: float, pitch: float, yaw: float) -> None:
        self.command(CommandType.SET_POSE, z=z, roll=roll, pitch=pitch, yaw=yaw)

    # ------------------------------------------------------------------ di chuyển liên tục
    def set_direction(self, vx: float, vy: float, wz: float) -> None:
        """Đặt hướng đi hiện tại (giữ nút/phím). (0,0,0) = thả nút -> STOP."""
        self._vector = (vx, vy, wz)
        self._vector_changed.set()

    def _start_repeater(self) -> None:
        self._stop_repeater.clear()
        if self._repeater is None or not self._repeater.is_alive():
            self._repeater = threading.Thread(target=self._repeat_loop, daemon=True)
            self._repeater.start()

    def _repeat_loop(self) -> None:
        """MOVE gửi lặp định kỳ khi giữ nút; STOP một lần khi thả."""
        interval = float(self._cfg.get("move_repeat_interval_s", 0.1))
        was_moving = False
        while not self._stop_repeater.is_set():
            vx, vy, wz = self._vector
            moving = (vx, vy, wz) != (0.0, 0.0, 0.0)
            try:
                if moving:
                    self._client.send(CommandType.MOVE, {"vx": vx, "vy": vy, "wz": wz, "speed": self._speed},
                                      wait=False)
                elif was_moving:
                    self._client.send(CommandType.STOP, wait=False)
            except (ConnectionError, OSError):
                return
            was_moving = moving
            self._vector_changed.wait(interval)
            self._vector_changed.clear()

    def shutdown(self) -> None:
        self._stop_repeater.set()
        self._client.disconnect()
        self._pool.shutdown(wait=False)
