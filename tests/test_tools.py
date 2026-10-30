import json
import os
import shutil
import tempfile
import unittest

from shared.common.config_loader import DEFAULT_CONFIG_DIR, ConfigLoader
from shared.common.enums import CommandType
from pc_app.communication.tcp_client import TcpClient
from pc_app.robot_client import RobotClient
from simulation.server.sim_robot import SimRobot
from tools.calibrate_servo import CalibrationEditor, run_interactive
from tools.common import Session


class CalibrateToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for name in os.listdir(DEFAULT_CONFIG_DIR):
            shutil.copy(os.path.join(DEFAULT_CONFIG_DIR, name), self.tmp)
        self.loader = ConfigLoader(self.tmp)
        self.robot = SimRobot(port=0, loader=self.loader)
        self.robot.start()
        self.client = RobotClient(lambda h, p: TcpClient(h, p), 1.0, 0.2)
        self.client.connect("127.0.0.1", self.robot.port)

    def tearDown(self):
        self.client.disconnect()
        self.robot.stop()
        shutil.rmtree(self.tmp)

    def test_editor_changes_and_persists(self):
        editor = CalibrationEditor(self.loader)
        editor.set_offset(0, 1, 93.46)
        self.assertEqual(editor.flip_direction(0, 1), -1)
        editor.save()
        with open(os.path.join(self.tmp, "servo_calibration.json"), encoding="utf-8") as f:
            saved = json.load(f)
        entry = next(e for e in saved["servos"] if e["leg"] == "i" and e["joint"] == "femur")
        self.assertEqual((entry["offset_deg"], entry["direction"]), (93.5, -1))

    def test_interactive_session(self):
        editor = CalibrationEditor(self.loader)
        inputs = iter(["120", "+", "++", "s", "n", "q"])      # servo 0: 120 -> 121 -> 126, lưu; sang servo 1; thoát
        outputs = []
        run_interactive(Session(self.client), editor, read=lambda prompt: next(inputs), write=outputs.append)
        self.assertEqual(editor.entry(0, 0)["offset_deg"], 126.0)
        self.assertEqual(self.robot.backend.raw_servo_deg[(0, 0)], 126.0)
        self.assertEqual(self.robot.controller.state.value, "IDLE")   # finish_test đã DISABLE
        with open(os.path.join(self.tmp, "servo_calibration.json"), encoding="utf-8") as f:
            self.assertIn("126.0", f.read())


if __name__ == "__main__":
    unittest.main()
