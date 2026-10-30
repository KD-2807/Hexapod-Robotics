"""Hằng số dùng chung."""

NUM_LEGS = 6
JOINTS_PER_LEG = 3
NUM_SERVOS = NUM_LEGS * JOINTS_PER_LEG

DEFAULT_TCP_PORT = 8888
MAX_COMMAND_BYTES = 256       # lệnh PC -> robot (firmware đệm nhận 256 byte)
MAX_LINE_BYTES = 1024         # phản hồi/STATUS robot -> PC

STATUS_SEQ = 0                # seq dành cho gói STATUS do robot chủ động đẩy
EPSILON = 1e-6
