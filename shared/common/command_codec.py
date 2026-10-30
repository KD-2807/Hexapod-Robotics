"""Mã hóa/giải mã Command, Response <-> một dòng JSON."""
import json
from typing import Any, Dict

from shared.common.constants import MAX_COMMAND_BYTES, MAX_LINE_BYTES
from shared.common.enums import CommandType, ErrorCode, ResponseType
from shared.common.protocol import Command, Response


class ProtocolError(ValueError):
    def __init__(self, code: ErrorCode, message: str, seq: int = 0):
        super().__init__(message)
        self.code = code
        self.message = message
        self.seq = seq


class CommandEncoder:
    @staticmethod
    def encode(packet) -> str:
        if isinstance(packet, Command):
            body: Dict[str, Any] = {"seq": packet.seq, "cmd": packet.cmd.value, "params": packet.params}
            limit = MAX_COMMAND_BYTES
        else:
            body = {"seq": packet.seq, "type": packet.type.value, "data": packet.data}
            limit = MAX_LINE_BYTES
        line = json.dumps(body, separators=(",", ":"))
        if len(line.encode("utf-8")) > limit:
            raise ProtocolError(ErrorCode.BAD_FORMAT, "Gói tin quá dài")
        return line


class CommandDecoder:
    @staticmethod
    def _parse(line: str) -> Dict[str, Any]:
        try:
            body = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProtocolError(ErrorCode.BAD_FORMAT, "JSON hỏng: %s" % exc) from exc
        if not isinstance(body, dict) or not isinstance(body.get("seq"), int):
            raise ProtocolError(ErrorCode.BAD_FORMAT, "Thiếu trường seq")
        return body

    @classmethod
    def decode_command(cls, line: str) -> Command:
        body = cls._parse(line)
        seq = body["seq"]
        try:
            cmd = CommandType(body.get("cmd"))
        except ValueError:
            raise ProtocolError(ErrorCode.BAD_COMMAND, "Lệnh không tồn tại: %s" % body.get("cmd"), seq)
        params = body.get("params", {})
        if not isinstance(params, dict):
            raise ProtocolError(ErrorCode.BAD_FORMAT, "params phải là object", seq)
        return Command(seq, cmd, params)

    @classmethod
    def decode_response(cls, line: str) -> Response:
        body = cls._parse(line)
        try:
            rtype = ResponseType(body.get("type"))
        except ValueError:
            raise ProtocolError(ErrorCode.BAD_FORMAT, "Loại phản hồi không hợp lệ", body["seq"])
        return Response(body["seq"], rtype, body.get("data", {}))
