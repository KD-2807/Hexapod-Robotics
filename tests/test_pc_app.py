import time
import unittest

from pc_app.app_controller import AppController
from pc_app.communication.tcp_client import TcpClient
from pc_app.robot_client import RobotClient
from shared.common.command_codec import CommandDecoder
from shared.common.enums import CommandType, RobotState
from simulation.server.sim_robot import SimRobot


def wait_for(predicate, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.02)
    return False


class PcAppIntegrationTest(unittest.TestCase):
    """PC app thật <-> SimRobot qua TCP localhost (toàn bộ đường truyền lệnh và trạng thái)."""

    def setUp(self):
        self.robot = SimRobot(port=0)
        self.robot.start()
        self.client = RobotClient(lambda h, p: TcpClient(h, p), response_timeout=1.0, heartbeat_interval=0.2)
        self.app = AppController(self.client, {"move_repeat_interval_s": 0.05, "default_speed": 0.8})
        self.statuses = []
        self.app.add_status_listener(self.statuses.append)
        self.client.connect("127.0.0.1", self.robot.port)

    def tearDown(self):
        self.app.shutdown()
        self.robot.stop()

    def test_full_control_flow(self):
        mc = self.robot.controller
        self.app.stand_up()
        self.assertTrue(wait_for(lambda: mc.state == RobotState.STANDING))
        self.app.set_direction(0, 1, 0)                  # giữ nút tiến
        self.assertTrue(wait_for(lambda: mc.state == RobotState.WALKING))
        self.app.stop()                                  # thả nút
        self.assertTrue(wait_for(lambda: mc.state == RobotState.STANDING))
        self.assertTrue(wait_for(lambda: len(self.statuses) > 0))
        self.assertEqual(len(self.statuses[-1].angles), 18)
        self.app.sit_down()
        self.assertTrue(wait_for(lambda: mc.state == RobotState.SITTING))

    def test_error_response_is_returned(self):
        response = self.client.send(CommandType.MOVE, {"vx": 0, "vy": 1, "wz": 0})
        self.assertEqual(response.data["code"], "BAD_STATE")

    def test_emergency_stop(self):
        self.app.stand_up()
        self.assertTrue(wait_for(lambda: self.robot.controller.state == RobotState.STANDING))
        self.app.emergency_stop()
        self.assertTrue(wait_for(lambda: self.robot.controller.state == RobotState.ERROR))
        self.assertTrue(wait_for(lambda: self.statuses and self.statuses[-1].state == "ERROR"))

    def test_heartbeat_keeps_robot_up_and_disconnect_sits_it_down(self):
        mc = self.robot.controller
        self.app.stand_up()
        self.assertTrue(wait_for(lambda: mc.state == RobotState.STANDING))
        time.sleep(2.0)                                   # > watchdog 1.5s, nhưng heartbeat vẫn gửi
        self.assertEqual(mc.state, RobotState.STANDING)
        self.client.disconnect()                          # mất kết nối -> dừng và ngồi
        self.assertTrue(wait_for(lambda: mc.state == RobotState.SITTING, timeout=8.0))

    def test_send_when_disconnected_raises(self):
        self.client.disconnect()
        with self.assertRaises(ConnectionError):
            self.client.send(CommandType.GET_STATUS)

    def test_connect_failure_reported(self):
        events = []
        self.app.add_connection_listener(lambda ok, msg: events.append((ok, msg)))
        self.app.connect("127.0.0.1", 1)                  # cổng đóng
        self.assertTrue(wait_for(lambda: any(not ok for ok, _ in events)))


if __name__ == "__main__":
    unittest.main()
