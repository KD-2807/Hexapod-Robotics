"""Tiện ích dùng chung cho các công cụ dòng lệnh: tham số kết nối và phiên làm việc với robot."""
import argparse
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from pc_app.communication.tcp_client import TcpClient
from pc_app.robot_client import RobotClient
from shared.common.config_loader import ConfigLoader
from shared.common.enums import CommandType, ResponseType


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", help="IP của ESP32 (mặc định theo pc_config.json)")
    parser.add_argument("--port", type=int, help="Cổng TCP")
    parser.add_argument("--sim", action="store_true", help="Dùng robot giả lập cục bộ (không cần phần cứng)")


@contextmanager
def robot_session(args: argparse.Namespace) -> Iterator["Session"]:
    config = ConfigLoader().load("pc_config")
    host, port, sim = args.host or config["host"], args.port or config["port"], None
    if args.sim:
        from simulation.server.sim_robot import SimRobot
        sim = SimRobot(port=0)
        sim.start()
        host, port = "127.0.0.1", sim.port
    client = RobotClient(lambda h, p: TcpClient(h, p, config["connect_timeout_s"]),
                         config["response_timeout_s"], config["heartbeat_interval_s"])
    try:
        client.connect(host, port)
        yield Session(client)
    finally:
        client.disconnect()
        if sim:
            sim.stop()


class Session:
    """Bao RobotClient: gửi lệnh, ném RuntimeError nếu robot trả ERROR."""

    def __init__(self, client: RobotClient):
        self.client = client

    def call(self, cmd: CommandType, **params: Any) -> Dict[str, Any]:
        response = self.client.send(cmd, params)
        if response.type == ResponseType.ERROR:
            raise RuntimeError("%s -> %s: %s" % (cmd.value, response.data.get("code"), response.data.get("message")))
        return response.data

    def status(self) -> Dict[str, Any]:
        return self.call(CommandType.GET_STATUS)

    def enable_for_test(self) -> None:
        """ENABLE: servo bật ở tư thế ngồi (chế độ test dùng SET_SERVO)."""
        state = self.status()["state"]
        if state == "ERROR":
            self.call(CommandType.RESET)
        self.call(CommandType.ENABLE)

    def finish_test(self) -> None:
        try:
            self.call(CommandType.DISABLE)
        except RuntimeError:
            pass
