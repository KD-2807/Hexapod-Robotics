"""Quét thử 1 servo quanh vị trí 0° của khớp (dùng góc khớp đã qua calibration).

    python -m tools.test_single_servo --leg 0 --joint femur --range 20
"""
import argparse
import sys
import time

from shared.common.enums import CommandType, JointType, LegId
from tools.common import add_connection_args, robot_session


def sweep(session, leg: int, joint: int, amplitude: float, step: float = 2.0, delay: float = 0.03) -> None:
    angles = []
    a = 0.0
    while a <= amplitude:
        angles.append(a); a += step
    path = angles + angles[::-1][1:] + [-x for x in angles[1:]] + [-x for x in angles[::-1][1:-1]] + [0.0]
    for angle in path:
        session.call(CommandType.SET_SERVO, leg=leg, joint=joint, angle=angle)
        time.sleep(delay)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    parser.add_argument("--leg", type=int, required=True, choices=range(6), help="0..5 = i,j,k,l,m,n")
    parser.add_argument("--joint", required=True, choices=[j.name.lower() for j in JointType])
    parser.add_argument("--range", type=float, default=20.0, help="Biên độ (độ)")
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            session.enable_for_test()
            print("Quét %s.%s ±%.0f°" % (LegId(args.leg).name, args.joint, args.range))
            sweep(session, args.leg, int(JointType[args.joint.upper()]), args.range)
            session.finish_test()
        return 0
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Lỗi:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
