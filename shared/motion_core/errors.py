from shared.common.enums import ErrorCode


class MotionError(Exception):
    """Lỗi nghiệp vụ khi xử lý lệnh; mang mã lỗi để trả về PC."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
