"""Hiệu chỉnh vị trí 0° của từng servo trên robot thật, rồi ghi vào config/servo_calibration.json.

Quy trình cho mỗi servo (khớp ở 0° nghĩa là: coxa hướng thẳng ra ngoài thân, femur nằm ngang,
tibia duỗi thẳng hàng với femur - xem docs/hardware-setup.md):
  1. Nhập góc servo thô (0..180) để di chuyển servo, hoặc +/- để tinh chỉnh 1°, ++/-- để 5°.
  2. Khi khớp đúng tư thế 0°, gõ  s  để lưu offset_deg = góc servo hiện tại.
  3. Gõ  d  để đảo chiều quay (direction = +1/-1) nếu khớp quay ngược.
  4. Gõ  n  sang servo kế tiếp, q để thoát.
Sau khi lưu, chạy:  python -m tools.gen_firmware_config  rồi nạp lại firmware.

    python -m tools.calibrate_servo --host 192.168.4.1
"""
import argparse
import sys
from typing import Optional

from shared.common.config_loader import ConfigLoader
from shared.common.enums import CommandType, JointType
from shared.robot_core.robot_config import RobotConfig
from tools.common import Session, add_connection_args, robot_session


class CalibrationEditor:
    """Sửa bảng calibration trong bộ nhớ và ghi lại file JSON (tách khỏi I/O để test được)."""

    def __init__(self, loader: ConfigLoader):
        self._loader = loader
        self._data = loader.load("servo_calibration")
        robot = RobotConfig.from_dict(loader.load("robot_config"))
        self.leg_ids = [spec.id for spec in robot.legs]

    def entry(self, leg: int, joint: int) -> dict:
        leg_id, joint_name = self.leg_ids[leg], JointType(joint).name.lower()
        return next(e for e in self._data["servos"] if e["leg"] == leg_id and e["joint"] == joint_name)

    def set_offset(self, leg: int, joint: int, servo_deg: float) -> None:
        self.entry(leg, joint)["offset_deg"] = round(servo_deg, 1)

    def flip_direction(self, leg: int, joint: int) -> int:
        entry = self.entry(leg, joint)
        entry["direction"] = -entry["direction"]
        return entry["direction"]

    def save(self) -> None:
        self._loader.save("servo_calibration", self._data)


def run_interactive(session: Session, editor: CalibrationEditor, read=input, write=print) -> None:
    session.enable_for_test()
    leg_joint = [(l, j) for l in range(6) for j in range(3)]
    index, angle = 0, 90.0
    while index < len(leg_joint):
        leg, joint = leg_joint[index]
        entry = editor.entry(leg, joint)
        write("\n== %s.%s  (offset=%.1f, direction=%+d)" % (editor.leg_ids[leg], JointType(joint).name.lower(),
                                                              entry["offset_deg"], entry["direction"]))
        session.call(CommandType.SET_SERVO, leg=leg, joint=joint, angle=angle, raw=True)
        text = read("góc servo [%.1f] (số / + - ++ -- / s lưu / d đảo chiều / n kế tiếp / q thoát): " % angle).strip().lower()
        if text == "q":
            break
        if text == "n":
            index, angle = index + 1, 90.0
            continue
        if text == "s":
            editor.set_offset(leg, joint, angle)
            editor.save()
            write("  đã lưu offset_deg = %.1f" % angle)
            continue
        if text == "d":
            write("  direction = %+d" % editor.flip_direction(leg, joint))
            editor.save()
            continue
        deltas = {"+": 1.0, "-": -1.0, "++": 5.0, "--": -5.0}
        try:
            angle = max(0.0, min(180.0, angle + deltas[text] if text in deltas else float(text)))
        except ValueError:
            write("  không hiểu lệnh: %r" % text)
    session.finish_test()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            run_interactive(session, CalibrationEditor(ConfigLoader()))
        print("Nhớ chạy: python -m tools.gen_firmware_config  và nạp lại firmware.")
        return 0
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Lỗi:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
