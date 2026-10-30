"""Thử lần lượt cả 18 servo (mỗi servo quét nhẹ ±10°) để phát hiện servo/kênh đấu sai.

    python -m tools.test_all_servos
"""
import argparse
import sys

from shared.common.enums import JointType, LegId
from tools.common import add_connection_args, robot_session
from tools.test_single_servo import sweep


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    parser.add_argument("--range", type=float, default=10.0)
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            session.enable_for_test()
            for leg in LegId:
                for joint in JointType:
                    print("servo %2d: %s.%s" % (int(leg) * 3 + int(joint), leg.name, joint.name.lower()))
                    sweep(session, int(leg), int(joint), args.range, step=3.0, delay=0.02)
            session.finish_test()
        print("Xong 18 servo. Servo nào không động: kiểm tra servo_map.json và dây cắm kênh PCA9685.")
        return 0
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Lỗi:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
