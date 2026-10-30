"""Chạy thử gait/IK trên PC, không cần robot thật.

    python -m simulation.run_sim            # cửa sổ 3D tương tác
        phím: U đứng | J ngồi | W A S D tiến/lùi/ngang | Q E xoay | G đổi dáng | Esc dừng khẩn | R reset
    python -m simulation.run_sim --headless --seconds 8 --save walk.png   # chạy kịch bản, lưu ảnh
"""
import argparse
import sys
from typing import List, Optional, Tuple

from pc_app.keyboard_mapper import KeyboardMapper
from shared.common.config_loader import ConfigLoader
from shared.common.enums import GaitType
from shared.motion_core.errors import MotionError
from shared.motion_core.factory import build_motion_controller
from shared.motion_core.motion_controller import MotionController
from simulation.sim_backend import SimBackend

DT = 0.02
_GAIT_CYCLE = [GaitType.TRIPOD, GaitType.RIPPLE, GaitType.WAVE]


class SimSession:
    """Một robot giả lập + bàn phím ảo. Tách khỏi matplotlib để dùng được ở chế độ headless."""

    def __init__(self, loader: Optional[ConfigLoader] = None):
        self.backend = SimBackend()
        self.controller: MotionController = build_motion_controller(self.backend, loader)
        self._keys = KeyboardMapper()
        self._gait_index = 0
        self.message = ""

    def run(self, seconds: float) -> None:
        for _ in range(int(round(seconds / DT))):
            self.controller.update(DT)

    def key_press(self, key: str) -> None:
        self._call(self._press, key)

    def key_release(self, key: str) -> None:
        self._call(lambda k: self._move(self._keys.release(k)), key)

    def _press(self, key: str) -> None:
        mc = self.controller
        if key == "u":
            mc.stand_up()
        elif key == "j":
            mc.sit_down()
        elif key == "r":
            mc.reset()
        elif key == "escape":
            mc.emergency_stop()
        elif key == "g":
            self._gait_index = (self._gait_index + 1) % len(_GAIT_CYCLE)
            mc.set_gait(_GAIT_CYCLE[self._gait_index])
        else:
            self._move(self._keys.press(key))

    def _move(self, vector: Tuple[float, float, float]) -> None:
        if vector == (0.0, 0.0, 0.0):
            self.controller.stop()
        else:
            self.controller.move(*vector, 1.0)

    def _call(self, fn, key: str) -> None:
        try:
            fn(key)
            self.message = ""
        except MotionError as exc:
            self.message = "%s: %s" % (exc.code.value, exc.message)

    def title(self) -> str:
        snap = self.controller.snapshot()
        return "%s | gait=%s | %s" % (snap["state"], snap["gait"], self.message or "OK")


def run_demo_script(session: SimSession, snapshots: Optional[List] = None) -> None:
    """Kịch bản: đứng lên -> đi tiến -> đi ngang -> xoay -> chào -> ngồi."""
    mc = session.controller
    steps = [(lambda: mc.stand_up(), 2.0), (lambda: mc.move(0, 1, 0, 0.8), 4.0),
             (lambda: mc.move(1, 0, 0, 0.8), 3.0), (lambda: mc.move(0, 0, 1, 0.8), 3.0),
             (lambda: mc.stop(), 1.5), (lambda: mc.run_action("wave"), 5.0), (lambda: mc.sit_down(), 2.5)]
    for action, seconds in steps:
        action()
        session.run(seconds)
        if snapshots is not None:
            snapshots.append((session.controller.frame.copy(), session.controller._ctx.posture.current))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hexapod simulator")
    parser.add_argument("--headless", action="store_true", help="Chạy kịch bản mẫu, không mở cửa sổ")
    parser.add_argument("--seconds", type=float, default=0.0, help="(headless) chỉ chạy N giây sau khi đứng")
    parser.add_argument("--save", help="(headless) lưu ảnh khung cuối vào file PNG")
    parser.add_argument("--config-dir", help="Thư mục config JSON")
    args = parser.parse_args(argv)

    session = SimSession(ConfigLoader(args.config_dir))
    if args.headless:
        import matplotlib
        matplotlib.use("Agg")
        from simulation.visualizer import Visualizer
        if args.seconds > 0:
            session.controller.stand_up()
            session.run(2.0)
            session.controller.move(0, 1, 0, 0.8)
            session.run(args.seconds)
        else:
            run_demo_script(session)
        print("trạng thái cuối:", session.controller.snapshot()["state"])
        if args.save:
            vis = Visualizer(session.controller.hexapod)
            vis.draw(session.controller.frame, session.controller._ctx.posture.current, session.title())
            vis.figure.savefig(args.save, dpi=110)
            print("đã lưu", args.save)
        return 0

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from simulation.visualizer import Visualizer
    vis = Visualizer(session.controller.hexapod)
    session.controller.stand_up()
    vis.figure.canvas.mpl_connect("key_press_event", lambda e: session.key_press((e.key or "").lower()))
    vis.figure.canvas.mpl_connect("key_release_event", lambda e: session.key_release((e.key or "").lower()))

    def frame(_i):
        session.run(2 * DT)
        vis.draw(session.controller.frame, session.controller._ctx.posture.current, session.title())

    animation = FuncAnimation(vis.figure, frame, interval=int(2 * DT * 1000), cache_frame_data=False)
    plt.show()
    del animation
    return 0


if __name__ == "__main__":
    sys.exit(main())
