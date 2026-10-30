import tkinter as tk
from tkinter import ttk


class LogPanel:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Nhật ký")
        self._text = tk.Text(self.frame, height=9, state="disabled", wrap="none")
        scroll = ttk.Scrollbar(self.frame, command=self._text.yview)
        self._text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._text.pack(side="left", fill="both", expand=True)

    def append(self, line: str) -> None:
        self._text.config(state="normal")
        self._text.insert("end", line + "\n")
        if int(self._text.index("end-1c").split(".")[0]) > 500:     # giữ tối đa ~500 dòng
            self._text.delete("1.0", "50.0")
        self._text.see("end")
        self._text.config(state="disabled")
