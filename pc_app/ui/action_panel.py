from tkinter import ttk

from pc_app.app_controller import AppController


class ActionPanel:
    def __init__(self, parent, controller: AppController):
        self.frame = ttk.LabelFrame(parent, text="Hành động")
        buttons = [("Enable", controller.enable), ("Đứng lên", controller.stand_up),
                   ("Ngồi xuống", controller.sit_down), ("Disable", controller.disable),
                   ("Chào", lambda: controller.run_action("wave")),
                   ("Nhún", lambda: controller.run_action("bob")),
                   ("Múa", lambda: controller.run_action("dance")),
                   ("Reset lỗi", controller.reset)]
        for index, (text, command) in enumerate(buttons):
            ttk.Button(self.frame, text=text, command=command, width=11).grid(
                row=index // 4, column=index % 4, padx=3, pady=3)
        stop = ttk.Button(self.frame, text="DỪNG KHẨN CẤP (Esc)", command=controller.emergency_stop)
        stop.grid(row=2, column=0, columnspan=4, sticky="ew", padx=3, pady=(6, 3))
