"""Định nghĩa gói tin PC <-> robot: Command và Response (mỗi gói là một dòng JSON)."""
from dataclasses import dataclass, field
from typing import Any, Dict

from shared.common.enums import CommandType, ErrorCode, ResponseType


@dataclass
class Command:
    seq: int
    cmd: CommandType
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    seq: int
    type: ResponseType
    data: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def ack(seq: int) -> "Response":
        return Response(seq, ResponseType.ACK)

    @staticmethod
    def error(seq: int, code: ErrorCode, message: str) -> "Response":
        return Response(seq, ResponseType.ERROR, {"code": code.value, "message": message})

    @staticmethod
    def status(seq: int, data: Dict[str, Any]) -> "Response":
        return Response(seq, ResponseType.STATUS, data)
