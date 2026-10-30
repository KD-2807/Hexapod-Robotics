"""Đối chiếu firmware C++ với bản Python: cùng kịch bản, so sánh từng bước 20 ms.

  1. Biên dịch test C++ trên PC (cần g++ và make).
  2. Chạy kịch bản test/host/scenario.txt trên cả hai bản; so sánh trạng thái (chính xác) và 18 góc khớp (sai số cho phép).
  3. So sánh tick PWM của 18 kênh khi đứng (kiểm tra calibration + servo_map + công thức PCA9685).

    python -m tools.crosscheck_firmware
"""
import argparse
import os
import subprocess
import sys
from typing import List, Tuple

from shared.common.config_loader import ConfigLoader
from shared.common.enums import JointType
from shared.motion_core.factory import build_motion_controller
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.servo_calibration import CalibrationTable
from simulation.sim_backend import SimBackend
from tools.scenario_runner import run_scenario

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_DIR = os.path.join(ROOT, "firmware_esp32", "test", "host")
SCENARIO = os.path.join(HOST_DIR, "scenario.txt")


def build_cpp() -> str:
    subprocess.check_call(["make", "-s", "host_test"], cwd=HOST_DIR)
    return os.path.join(HOST_DIR, "host_test")


def compare_scenario(py: List[str], cpp: List[str], tolerance: float) -> Tuple[bool, str]:
    if len(py) != len(cpp):
        return False, "số dòng khác nhau: Python %d, C++ %d" % (len(py), len(cpp))
    worst, worst_at = 0.0, 0
    for index, (a, b) in enumerate(zip(py, cpp)):
        pa, pb = a.split(), b.split()
        if pa[0] != pb[0] or (pa[0] == "ERR" and pa != pb) or (pa[0] == "S" and pa[1] != pb[1]):
            return False, "dòng %d khác (trạng thái/lỗi):\n  python: %s\n  c++:    %s" % (index, a[:60], b[:60])
        if pa[0] == "S":
            diff = max(abs(float(x) - float(y)) for x, y in zip(pa[2:], pb[2:]))
            if diff > worst:
                worst, worst_at = diff, index
    if worst > tolerance:
        return False, "lệch góc lớn nhất %.4f° tại dòng %d (cho phép %.4f°)" % (worst, worst_at, tolerance)
    return True, "%d bước khớp nhau, lệch góc lớn nhất %.5f°" % (len(py), worst)


def python_ticks() -> List[Tuple[int, int, int]]:
    loader = ConfigLoader()
    robot = RobotConfig.from_dict(loader.load("robot_config"))
    table = CalibrationTable.from_dict(loader.load("servo_calibration"), robot)
    servo_map = loader.load("servo_map")
    hw = loader.load("hardware_config")["pca9685"]
    period_us = 1_000_000.0 / hw["pwm_hz"]
    mc = build_motion_controller(SimBackend())
    run_scenario(mc, "stand_up\nrun 1.8\n")
    result = []
    for leg, spec in enumerate(robot.legs):
        for joint in JointType:
            cal = table.get(leg, int(joint))
            pulse = cal.pulse_us(cal.servo_angle(mc.frame.get(leg, int(joint))))
            ticks = max(0, min(4095, int(pulse / period_us * 4096.0 + 0.5)))
            board, _channel = servo_map[spec.id][joint.name.lower()]
            result.append((leg * 3 + int(joint), board, ticks))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tolerance", type=float, default=0.05, help="sai số góc cho phép (độ)")
    args = parser.parse_args(argv)

    binary = build_cpp()
    scenario_text = open(SCENARIO, encoding="utf-8").read()
    cpp_lines = subprocess.check_output([binary, "dump", SCENARIO], text=True).splitlines()
    py_lines = run_scenario(build_motion_controller(SimBackend()), scenario_text)
    ok, message = compare_scenario(py_lines, cpp_lines, args.tolerance)
    print(("PASS" if ok else "FAIL"), "kịch bản:", message)

    cpp_ticks = [tuple(int(x) for x in line.split()[1:]) for line in
                 subprocess.check_output([binary, "ticks"], text=True).splitlines()]
    py_ticks = python_ticks()
    worst_tick = max(abs(a[2] - b[2]) for a, b in zip(py_ticks, cpp_ticks))
    tick_ok = len(py_ticks) == len(cpp_ticks) == 18 and all(a[:2] == b[:2] for a, b in zip(py_ticks, cpp_ticks)) \
        and worst_tick <= 1
    print(("PASS" if tick_ok else "FAIL"), "tick PWM 18 kênh: lệch lớn nhất %d tick" % worst_tick)
    return 0 if ok and tick_ok else 1


if __name__ == "__main__":
    sys.exit(main())
