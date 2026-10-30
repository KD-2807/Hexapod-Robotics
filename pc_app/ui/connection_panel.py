import tkinter as tk
from tkinter import ttk
from typing import Any, Dict

from pc_app.app_controller import AppController


class ConnectionPanel:
    def __init__(self, parent, controller: AppController, config: Dict[str, Any]):
        self._controller = controller
        self.frame = ttk.LabelFrame(parent, text="Kết nối")
        self._host = tk.StringVar(value=config.get("host", "192.168.4.1"))
        self._port = tk.StringVar(value=str(config.get("port", 8888)))
        ttk.Label(self.frame, text="IP").grid(row=0, column=0, padx=4, pady=4)
        ttk.Entry(self.frame, textvariable=self._host, width=16).grid(row=0, column=1)
        ttk.Label(self.frame, text="Port").grid(row=0, column=2, padx=4)
        ttk.Entry(self.frame, textvariable=self._port, width=6).grid(row=0, column=3)
        self._connect_btn = ttk.Button(self.frame, text="Connect", command=self._connect)
        self._connect_btn.grid(row=0, column=4, padx=4)
        self._disconnect_btn = ttk.Button(self.frame, text="Disconnect", command=controller.disconnect,
                                          state="disabled")
        self._disconnect_btn.grid(row=0, column=5, padx=4)
        self._state = ttk.Label(self.frame, text="● Chưa kết nối", foreground="#b00020")
        self._state.grid(row=0, column=6, padx=8)

    def _connect(self) -> None:
        try:
            port = int(self._port.get())
        except ValueError:
            return
        self._controller.connect(self._host.get().strip(), port)

    def set_connected(self, connected: bool) -> None:
        self._connect_btn.config(state="disabled" if connected else "normal")
        self._disconnect_btn.config(state="normal" if connected else "disabled")
        self._state.config(text="● Đã kết nối" if connected else "● Chưa kết nối",
                           foreground="#0a7a0a" if connected else "#b00020")
