"""Kiểm tra kết nối PC <-> ESP32: đo thời gian phản hồi GET_STATUS.

    python -m tools.ping_robot --host 192.168.4.1
"""
import argparse
import statistics
import sys
import time

from shared.common.enums import CommandType
from tools.common import add_connection_args, robot_session


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    parser.add_argument("-n", "--count", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            times = []
            for i in range(args.count):
                start = time.perf_counter()
                data = session.status()
                times.append((time.perf_counter() - start) * 1000)
                print("#%d  state=%s  %.1f ms" % (i + 1, data["state"], times[-1]))
                time.sleep(0.1)
            print("RTT trung bình %.1f ms, lớn nhất %.1f ms" % (statistics.mean(times), max(times)))
        return 0
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Không ping được robot:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
