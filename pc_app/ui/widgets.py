"""Widget dùng lại: nút giữ-để-chạy, thanh trượt có nhãn, bộ gom lệnh trượt (throttle)."""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Tuple


def hold_button(parent, text: str, on_press: Callable[[], None], on_release: Callable[[], None],
                width: int = 7) -> ttk.Button:
    """Nút gửi on_press khi nhấn xuống và on_release khi thả (dùng cho điều khiển liên tục)."""
    button = ttk.Button(parent, text=text, width=width)
    button.bind("<ButtonPress-1>", lambda _e: on_press())
    button.bind("<ButtonRelease-1>", lambda _e: on_release())
    return button


def labeled_slider(parent, label: str, low: float, high: float, initial: float,
                   on_change: Callable[[float], None], resolution: float = 1.0) -> Tuple[ttk.Frame, tk.DoubleVar]:
    """Hàng gồm nhãn, thanh trượt và giá trị hiện tại. on_change nhận giá trị mới."""
    frame = ttk.Frame(parent)
    var = tk.DoubleVar(value=initial)
    value_label = ttk.Label(frame, width=7, anchor="e")

    def changed(_raw: str) -> None:
        value = round(var.get() / resolution) * resolution
        value_label.config(text="%g" % round(value, 3))
        on_change(value)

    ttk.Label(frame, text=label, width=8).pack(side="left")
    ttk.Scale(frame, from_=low, to=high, variable=var, orient="horizontal", command=changed,
              length=180).pack(side="left", fill="x", expand=True)
    value_label.config(text="%g" % initial)
    value_label.pack(side="left")
    return frame, var


class Debouncer:
    """Gom nhiều lần gọi liên tiếp (kéo slider) thành một lệnh sau `delay_ms`."""

    def __init__(self, widget, delay_ms: int, action: Callable[[], None]):
        self._widget, self._delay, self._action = widget, delay_ms, action
        self._job = None

    def trigger(self) -> None:
        if self._job is not None:
            self._widget.after_cancel(self._job)
        self._job = self._widget.after(self._delay, self._fire)

    def _fire(self) -> None:
        self._job = None
        self._action()
