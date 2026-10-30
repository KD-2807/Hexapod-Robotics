"""SimRobot: robot giả lập chạy trên PC, nói đúng giao thức TCP như ESP32 (không cần phần cứng)."""
import threading
import time
from typing import Optional

from shared.common.command_codec import CommandDecoder, CommandEncoder, ProtocolError
from shared.common.config_loader import ConfigLoader
from shared.common.enums import CommandType, RobotState
from shared.common.logger import Logger
from shared.common.protocol import Response
from shared.motion_core.factory import build_motion_controller
from shared.robot_core.safety_config import SafetyConfig
from shared.robot_core.servo_calibration import CalibrationTable
from shared.robot_core.robot_config import RobotConfig
from simulation.sim_backend import SimBackend
from simulation.server.command_handler import CommandHandler
from simulation.server.status_reporter import StatusReporter
from simulation.server.tcp_server import TcpServer
from simulation.server.watchdog import Watchdog


class SimRobot:
    """Vòng lặp: nhận dòng -> CommandHandler -> phản hồi; controller.update(dt); watchdog; đẩy STATUS."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8888, loader: Optional[ConfigLoader] = None,
                 loop_hz: float = 50.0, status_hz: float = 5.0):
        loader = loader or ConfigLoader()
        robot = RobotConfig.from_dict(loader.load("robot_config"))
        self.backend = SimBackend(CalibrationTable.from_dict(loader.load("servo_calibration"), robot))
        self.controller = build_motion_controller(self.backend, loader)
        self.server = TcpServer(host, port)
        self._dt = 1.0 / loop_hz
        self._log = Logger("sim_robot")
        timeout = SafetyConfig.from_dict(loader.load("safety_config")).watchdog_timeout_s
        self.watchdog = Watchdog(timeout, self._on_link_lost)
        self.reporter = StatusReporter(self.controller, status_hz, lambda: {"i2c": [64, 65, 104]})
        self.handler = CommandHandler(self.controller, lambda: self.reporter.build(self.server.is_connected))
        self._thread: Optional[threading.Thread] = None
        self._running = False

    @property
    def port(self) -> int:
        return self.server.port

    def start(self) -> None:
        self.server.connect()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log.info("SimRobot lắng nghe tại cổng %d", self.server.port)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.server.close()

    def _on_link_lost(self) -> None:
        self._log.warning("Mất heartbeat -> dừng và ngồi xuống")
        self.controller.on_link_lost()

    def step(self) -> None:
        """Một chu kỳ điều khiển (tách riêng để kiểm thử được)."""
        for _ in range(8):                               # xử lý tối đa 8 gói mỗi chu kỳ
            line = self.server.receive_line(0)
            if line is None:
                break
            self._handle_line(line)
        if self.server.client_dropped:
            self.server.client_dropped = False
            self.watchdog.trigger()
        self.watchdog.update(self._dt)
        self.controller.update(self._dt)
        if self.server.is_connected and self.reporter.due(self._dt):
            self.server.send_line(CommandEncoder.encode(self.reporter.packet(True)))

    def _handle_line(self, line: str) -> None:
        try:
            command = CommandDecoder.decode_command(line)
        except ProtocolError as exc:
            self.server.send_line(CommandEncoder.encode(Response.error(exc.seq, exc.code, exc.message)))
            return
        self.watchdog.feed()
        self.server.send_line(CommandEncoder.encode(self.handler.handle(command)))

    def _loop(self) -> None:
        next_tick = time.monotonic()
        while self._running:
            self.step()
            next_tick += self._dt
            time.sleep(max(0.0, next_tick - time.monotonic()))
