"""MainWindow: lắp các panel; nhận sự kiện từ luồng nền qua hàng đợi rồi cập nhật UI trên luồng Tk."""
import queue
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict

from pc_app.app_controller import AppController
from pc_app.models.robot_status import RobotStatus
from pc_app.ui.action_panel import ActionPanel
from pc_app.ui.connection_panel import ConnectionPanel
from pc_app.ui.gait_panel import GaitPanel
from pc_app.ui.log_panel import LogPanel
from pc_app.ui.movement_panel import MovementPanel
from pc_app.ui.pose_panel import PosePanel
from pc_app.ui.status_panel import StatusPanel
from shared.common.logger import Logger

_POLL_MS = 40


class MainWindow:
    def __init__(self, root: tk.Tk, controller: AppController, config: Dict[str, Any]):
        self._root = root
        self._controller = controller
        self._events: "queue.Queue" = queue.Queue()
        root.title("Hexapod Controller")

        self._connection = ConnectionPanel(root, controller, config)
        self._movement = MovementPanel(root, controller)
        self._actions = ActionPanel(root, controller)
        self._gait = GaitPanel(root, controller, config)
        self._pose = PosePanel(root, controller)
        self._status = StatusPanel(root)
        self._log = LogPanel(root)

        self._connection.frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
        self._movement.frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        self._actions.frame.grid(row=1, column=1, sticky="nsew", padx=6, pady=4)
        self._gait.frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=4)
        self._pose.frame.grid(row=2, column=1, sticky="nsew", padx=6, pady=4)
        self._status.frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
        self._log.frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=6, pady=4)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(4, weight=1)

        self._movement.bind_keys(root)
        controller.add_status_listener(lambda s: self._events.put(("status", s)))
        controller.add_connection_listener(lambda ok, msg: self._events.put(("connection", ok)))
        Logger.add_listener(lambda line: self._events.put(("log", line)))
        for line in Logger.history():
            self._log.append(line)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.after(_POLL_MS, self._poll)

    def _poll(self) -> None:
        """Chạy trên luồng Tk: lấy hết sự kiện đang chờ."""
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "status":
                    self._status.show(payload)
                elif kind == "connection":
                    self._connection.set_connected(payload)
                    if not payload:
                        self._status.clear()
                elif kind == "log":
                    self._log.append(payload)
        except queue.Empty:
            pass
        self._root.after(_POLL_MS, self._poll)

    def _close(self) -> None:
        self._controller.shutdown()
        self._root.destroy()
