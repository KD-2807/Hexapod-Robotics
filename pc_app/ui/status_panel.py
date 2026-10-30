from tkinter import ttk

from pc_app.models.robot_status import RobotStatus

_STATE_COLORS = {"IDLE": "#666666", "SITTING": "#b36b00", "STANDING": "#0a7a0a",
                 "WALKING": "#0050b3", "ERROR": "#b00020"}
_LEGS = ["RM (i)", "RR (j)", "LR (k)", "LM (l)", "LF (m)", "RF (n)"]


class StatusPanel:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Trạng thái robot")
        self._summary = ttk.Label(self.frame, text="Chưa có dữ liệu", font=("TkDefaultFont", 11, "bold"))
        self._summary.grid(row=0, column=0, columnspan=4, sticky="w", padx=6, pady=2)
        self._detail = ttk.Label(self.frame, text="")
        self._detail.grid(row=1, column=0, columnspan=4, sticky="w", padx=6)
        for col, name in enumerate(("Coxa", "Femur", "Tibia")):
            ttk.Label(self.frame, text=name).grid(row=2, column=col + 1)
        self._cells = []
        for row, leg in enumerate(_LEGS):
            ttk.Label(self.frame, text=leg).grid(row=row + 3, column=0, sticky="w", padx=6)
            cells = []
            for col in range(3):
                label = ttk.Label(self.frame, text="--", width=8, anchor="e")
                label.grid(row=row + 3, column=col + 1)
                cells.append(label)
            self._cells.append(cells)

    def show(self, status: RobotStatus) -> None:
        self._summary.config(text="● %s   gait: %s   speed: %.2f" % (status.state, status.gait, status.speed),
                             foreground=_STATE_COLORS.get(status.state, "black"))
        parts = ["thân z=%.0f roll=%.0f pitch=%.0f yaw=%.0f" % (
            status.pose.get("z", 0), status.pose.get("roll", 0), status.pose.get("pitch", 0), status.pose.get("yaw", 0))]
        if status.battery_v is not None:
            parts.append("pin %.2f V" % status.battery_v)
        if status.imu_roll is not None:
            parts.append("IMU roll %.1f° pitch %.1f°" % (status.imu_roll, status.imu_pitch or 0.0))
        if status.error:
            parts.append("LỖI: %s - %s" % (status.error.get("code"), status.error.get("message")))
        self._detail.config(text="   |   ".join(parts))
        for leg in range(6):
            for joint in range(3):
                self._cells[leg][joint].config(text="%.1f°" % status.angles[leg * 3 + joint])

    def clear(self) -> None:
        self._summary.config(text="Chưa có dữ liệu", foreground="black")
        self._detail.config(text="")
