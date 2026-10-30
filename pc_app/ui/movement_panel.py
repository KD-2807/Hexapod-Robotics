from tkinter import ttk
from pc_app.app_controller import AppController
from pc_app.keyboard_mapper import KeyboardMapper
from pc_app.ui.widgets import hold_button

# (nhãn, (vx, vy, wz), hàng, cột) - vx: sang phải, vy: tiến, wz: xoay ngược chiều kim đồng hồ
_BUTTONS = [
    ("⟲ Q", (0.0, 0.0, 1.0), 0, 0), ("▲ W", (0.0, 1.0, 0.0), 0, 1), ("E ⟳", (0.0, 0.0, -1.0), 0, 2),
    ("◀ A", (-1.0, 0.0, 0.0), 1, 0), ("■", (0.0, 0.0, 0.0), 1, 1), ("D ▶", (1.0, 0.0, 0.0), 1, 2),
    ("▼ S", (0.0, -1.0, 0.0), 2, 1),
]

class MovementPanel:
    def __init__(self, parent, controller: AppController):
        self._controller = controller
        self._keys = KeyboardMapper()
        self.frame = ttk.LabelFrame(parent, text="Di chuyển (giữ nút hoặc phím W A S D Q E)")
        for text, vector, row, col in _BUTTONS:
            if vector == (0.0, 0.0, 0.0):
                button = ttk.Button(self.frame, text=text, width=7, command=controller.stop)
            else:
                button = hold_button(self.frame, text, lambda v=vector: controller.set_direction(*v),
                                     controller.stop)
            button.grid(row=row, column=col, padx=3, pady=3)

    def bind_keys(self, root) -> None:
        root.bind("<KeyPress>", self._on_press)
        root.bind("<KeyRelease>", self._on_release)
        root.bind("<space>", lambda _e: self._controller.stop())
        root.bind("<Escape>", lambda _e: self._controller.emergency_stop())

    def _on_press(self, event) -> None:
        if self._is_typing(event):
            return
        self._controller.set_direction(*self._keys.press(event.keysym.lower()))

    def _on_release(self, event) -> None:
        if self._is_typing(event):
            return
        self._controller.set_direction(*self._keys.release(event.keysym.lower()))

    @staticmethod
    def _is_typing(event) -> bool:
        return event.widget.winfo_class() in ("Entry", "TEntry")
