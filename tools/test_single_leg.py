"""Thử cả 3 khớp của 1 chân lần lượt, rồi thử đồng thời (vẽ vòng tròn nhỏ bằng bàn chân).

    python -m tools.test_single_leg --leg 0
"""
import argparse
import sys

from shared.common.enums import JointType, LegId
from tools.common import add_connection_args, robot_session
from tools.test_single_servo import sweep


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    parser.add_argument("--leg", type=int, required=True, choices=range(6))
    parser.add_argument("--range", type=float, default=15.0)
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            session.enable_for_test()
            for joint in JointType:
                print("%s.%s" % (LegId(args.leg).name, joint.name.lower()))
                sweep(session, args.leg, int(joint), args.range)
            session.finish_test()
        return 0
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Lỗi:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
