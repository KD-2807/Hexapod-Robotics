"""Chạy kịch bản văn bản (firmware_esp32/test/host/scenario.txt) trên bản Python của lõi điều khiển.

Định dạng đầu ra giống hệt chương trình test C++ để so sánh từng dòng.
"""
from typing import List

from shared.common.enums import GaitType
from shared.motion_core.errors import MotionError
from shared.motion_core.motion_controller import MotionController

DT = 0.02


def run_scenario(controller: MotionController, text: str) -> List[str]:
    out: List[str] = []
    for raw in text.splitlines():
        parts = raw.split()
        if not parts or parts[0].startswith("#"):
            continue
        cmd, args = parts[0], parts[1:]
        if cmd == "run":
            for _ in range(int(float(args[0]) / DT + 0.5)):
                controller.update(DT)
                out.append("S %s %s" % (controller.state.value, " ".join("%.4f" % a for a in controller.frame.angles)))
            continue
        try:
            _apply(controller, cmd, args)
        except MotionError as exc:
            out.append("ERR %s" % exc.code.value)
    return out


def _apply(mc: MotionController, cmd: str, args: List[str]) -> None:
    nums = [float(a) for a in args] if cmd in ("move", "speed", "pose") else []
    if cmd == "stand_up": mc.stand_up()
    elif cmd == "sit_down": mc.sit_down()
    elif cmd == "enable": mc.enable()
    elif cmd == "disable": mc.disable()
    elif cmd == "stop": mc.stop()
    elif cmd == "reset": mc.reset()
    elif cmd == "estop": mc.emergency_stop()
    elif cmd == "link_lost": mc.on_link_lost()
    elif cmd == "move": mc.move(nums[0], nums[1], nums[2], nums[3])
    elif cmd == "speed": mc.set_speed(nums[0])
    elif cmd == "pose": mc.set_pose(*nums[:4])
    elif cmd == "gait": mc.set_gait(GaitType(args[0]))
    elif cmd == "action": mc.run_action(args[0])
    else: raise ValueError("lệnh kịch bản không biết: %s" % cmd)
