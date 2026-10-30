import tkinter as tk
from tkinter import ttk
from typing import Any, Dict

from pc_app.app_controller import AppController
from pc_app.ui.widgets import labeled_slider

_GAITS = [("Tripod (nhanh)", "tripod"), ("Ripple (trung bình)", "ripple"), ("Wave (ổn định)", "wave")]


class GaitPanel:
    def __init__(self, parent, controller: AppController, config: Dict[str, Any]):
        self.frame = ttk.LabelFrame(parent, text="Dáng đi")
        self._gait = tk.StringVar(value=config.get("default_gait", "tripod"))
        for text, value in _GAITS:
            ttk.Radiobutton(self.frame, text=text, value=value, variable=self._gait,
                            command=lambda: controller.set_gait(self._gait.get())).pack(anchor="w", padx=6)
        row, self._speed = labeled_slider(self.frame, "Tốc độ", 0.1, 1.0, config.get("default_speed", 0.6),
                                          controller.set_speed, resolution=0.05)
        row.pack(fill="x", padx=6, pady=4)
