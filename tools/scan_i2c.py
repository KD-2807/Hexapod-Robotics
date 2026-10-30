"""Kiểm tra ESP32 thấy đủ thiết bị I2C: 2 PCA9685 (0x40, 0x41) và MPU6050 (0x68).

    python -m tools.scan_i2c --host 192.168.4.1
"""
import argparse
import sys

from tools.common import add_connection_args, robot_session

EXPECTED = {0x40: "PCA9685 #0 (chân i, j, k)", 0x41: "PCA9685 #1 (chân l, m, n)", 0x68: "MPU6050 (tùy chọn)"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser)
    args = parser.parse_args(argv)
    try:
        with robot_session(args) as session:
            found = set(session.status().get("i2c", []))
    except (OSError, TimeoutError, RuntimeError) as exc:
        print("Lỗi:", exc)
        return 1
    print("Thiết bị I2C tìm thấy:", ", ".join("0x%02X" % a for a in sorted(found)) or "(không có)")
    ok = True
    for address, name in EXPECTED.items():
        present = address in found
        print("  0x%02X %-28s %s" % (address, name, "OK" if present else "KHÔNG THẤY"))
        ok = ok and (present or address == 0x68)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
