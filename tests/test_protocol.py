import unittest

from shared.common.command_codec import CommandDecoder, CommandEncoder, ProtocolError
from shared.common.enums import CommandType, ErrorCode, ResponseType
from shared.common.protocol import Command, Response


class ProtocolTest(unittest.TestCase):
    def test_command_roundtrip(self):
        cmd = Command(7, CommandType.MOVE, {"vx": 0.0, "vy": 1.0, "wz": 0.0, "speed": 0.5})
        line = CommandEncoder.encode(cmd)
        self.assertNotIn("\n", line)
        self.assertEqual(CommandDecoder.decode_command(line), cmd)

    def test_response_roundtrip(self):
        for resp in (Response.ack(3), Response.error(4, ErrorCode.BAD_STATE, "x"),
                     Response.status(0, {"state": "IDLE", "angles": [0.0] * 18})):
            self.assertEqual(CommandDecoder.decode_response(CommandEncoder.encode(resp)), resp)

    def test_format_matches_document(self):
        line = CommandEncoder.encode(Command(1, CommandType.MOVE, {"vx": 0}))
        self.assertEqual(line, '{"seq":1,"cmd":"MOVE","params":{"vx":0}}')
        self.assertEqual(CommandEncoder.encode(Response.ack(1)), '{"seq":1,"type":"ACK","data":{}}')

    def test_bad_inputs(self):
        for line, code in (("not json", ErrorCode.BAD_FORMAT), ('{"cmd":"MOVE"}', ErrorCode.BAD_FORMAT),
                           ('{"seq":1,"cmd":"FLY"}', ErrorCode.BAD_COMMAND),
                           ('{"seq":1,"cmd":"MOVE","params":5}', ErrorCode.BAD_FORMAT)):
            with self.assertRaises(ProtocolError) as ctx:
                CommandDecoder.decode_command(line)
            self.assertEqual(ctx.exception.code, code)

    def test_missing_params_defaults_to_empty(self):
        self.assertEqual(CommandDecoder.decode_command('{"seq":2,"cmd":"STOP"}').params, {})


if __name__ == "__main__":
    unittest.main()
