"""Các kiểu liệt kê dùng chung PC <-> robot."""
from enum import Enum, IntEnum


class LegId(IntEnum):
    """6 chân theo chiều kim đồng hồ, bắt đầu từ chân giữa bên phải (i, j, k, l, m, n)."""
    RIGHT_MIDDLE = 0
    RIGHT_REAR = 1
    LEFT_REAR = 2
    LEFT_MIDDLE = 3
    LEFT_FRONT = 4
    RIGHT_FRONT = 5


class JointType(IntEnum):
    COXA = 0
    FEMUR = 1
    TIBIA = 2


class GaitType(str, Enum):
    TRIPOD = "tripod"
    WAVE = "wave"
    RIPPLE = "ripple"
    ROTATION = "rotation"


class RobotState(str, Enum):
    IDLE = "IDLE"
    STANDING = "STANDING"
    WALKING = "WALKING"
    SITTING = "SITTING"
    ERROR = "ERROR"


class CommandType(str, Enum):
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    STAND_UP = "STAND_UP"
    SIT_DOWN = "SIT_DOWN"
    MOVE = "MOVE"
    STOP = "STOP"
    SET_GAIT = "SET_GAIT"
    SET_SPEED = "SET_SPEED"
    SET_POSE = "SET_POSE"
    ACTION = "ACTION"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    RESET = "RESET"
    HEARTBEAT = "HEARTBEAT"
    GET_STATUS = "GET_STATUS"
    SET_SERVO = "SET_SERVO"


class ResponseType(str, Enum):
    ACK = "ACK"
    ERROR = "ERROR"
    STATUS = "STATUS"


class ErrorCode(str, Enum):
    BAD_FORMAT = "BAD_FORMAT"        # JSON hỏng / thiếu trường
    BAD_COMMAND = "BAD_COMMAND"      # lệnh không tồn tại
    BAD_PARAMS = "BAD_PARAMS"        # tham số sai / vượt giới hạn
    BAD_STATE = "BAD_STATE"          # lệnh không hợp lệ ở trạng thái hiện tại
    LIMIT = "LIMIT"                  # góc khớp vượt giới hạn / không với tới
    HARDWARE = "HARDWARE"            # lỗi I2C / PCA9685
    ESTOP = "ESTOP"                  # dừng khẩn cấp
