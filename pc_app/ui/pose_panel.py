import tkinter as tk
from tkinter import ttk
from typing import Dict

from pc_app.app_controller import AppController
from pc_app.ui.widgets import Debouncer, labeled_slider

# (khóa, nhãn, min, max) - lấy theo vùng tư thế khi đứng yên trong pose_config.json
_SLIDERS = [("z", "Nâng (mm)", -25, 30), ("roll", "Roll (°)", -15, 15),
            ("pitch", "Pitch (°)", -15, 15), ("yaw", "Yaw (°)", -20, 20)]


class PosePanel:
    def __init__(self, parent, controller: AppController):
        self._controller = controller
        self.frame = ttk.LabelFrame(parent, text="Tư thế thân (khi đứng yên)")
        self._values: Dict[str, float] = {key: 0.0 for key, *_ in _SLIDERS}
        self._vars: Dict[str, tk.DoubleVar] = {}
        self._debounce = Debouncer(self.frame, 120, self._send)
        for key, label, low, high in _SLIDERS:
            row, var = labeled_slider(self.frame, label, low, high, 0.0, lambda v, k=key: self._changed(k, v))
            row.pack(fill="x", padx=6)
            self._vars[key] = var
        ttk.Button(self.frame, text="Về tư thế chuẩn", command=self._reset).pack(pady=4)

    def _changed(self, key: str, value: float) -> None:
        self._values[key] = value
        self._debounce.trigger()

    def _send(self) -> None:
        v = self._values
        self._controller.set_pose(v["z"], v["roll"], v["pitch"], v["yaw"])

    def _reset(self) -> None:
        for key, var in self._vars.items():
            var.set(0.0)
            self._values[key] = 0.0
        self._send()
