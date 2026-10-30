"""Điểm vào ứng dụng điều khiển PC.

    python -m pc_app.main                 # kết nối robot thật (IP trong config/pc_config.json)
    python -m pc_app.main --host 192.168.1.50 --port 8888
    python -m pc_app.main --sim           # tự chạy robot giả lập trên máy và kết nối vào đó
"""
import argparse
import sys

from pc_app.app_controller import AppController
from pc_app.communication.tcp_client import TcpClient
from pc_app.robot_client import RobotClient
from shared.common.config_loader import ConfigLoader


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Hexapod PC controller")
    parser.add_argument("--host", help="IP của ESP32 (mặc định theo pc_config.json)")
    parser.add_argument("--port", type=int, help="Cổng TCP")
    parser.add_argument("--sim", action="store_true", help="Chạy robot giả lập cục bộ")
    parser.add_argument("--config-dir", help="Thư mục chứa các file JSON cấu hình")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    loader = ConfigLoader(args.config_dir)
    config = dict(loader.load("pc_config"))
    if args.host:
        config["host"] = args.host
    if args.port:
        config["port"] = args.port

    sim = None
    if args.sim:
        from simulation.server.sim_robot import SimRobot
        sim = SimRobot(host="127.0.0.1", port=0, loader=loader)
        sim.start()
        config["host"], config["port"] = "127.0.0.1", sim.port

    import tkinter as tk
    from pc_app.ui.main_window import MainWindow

    client = RobotClient(lambda h, p: TcpClient(h, p, config["connect_timeout_s"]),
                         config["response_timeout_s"], config["heartbeat_interval_s"])
    controller = AppController(client, config)
    root = tk.Tk()
    MainWindow(root, controller, config)
    try:
        root.mainloop()
    finally:
        if sim:
            sim.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
