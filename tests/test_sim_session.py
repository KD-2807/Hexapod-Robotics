import unittest

from shared.common.enums import RobotState as S
from simulation.run_sim import SimSession, run_demo_script


class SimSessionTest(unittest.TestCase):
    def test_keyboard_flow(self):
        s = SimSession()
        s.key_press("u")
        s.run(1.6)
        self.assertEqual(s.controller.state, S.STANDING)
        s.key_press("w")
        s.run(0.5)
        self.assertEqual(s.controller.state, S.WALKING)
        s.key_press("d")                                  # tiến + sang phải cùng lúc
        s.run(0.3)
        s.key_release("w")
        s.key_release("d")
        s.run(1.5)
        self.assertEqual(s.controller.state, S.STANDING)
        s.key_press("g")
        self.assertEqual(s.controller.snapshot()["gait"], "ripple")
        s.key_press("j")
        s.run(1.6)
        self.assertEqual(s.controller.state, S.SITTING)

    def test_invalid_key_action_is_reported_not_raised(self):
        s = SimSession()
        s.key_press("w")                                  # chưa đứng -> BAD_STATE
        self.assertIn("BAD_STATE", s.message)
        self.assertIn("BAD_STATE", s.title())

    def test_escape_and_reset(self):
        s = SimSession()
        s.key_press("u"); s.run(1.6)
        s.key_press("escape")
        self.assertEqual(s.controller.state, S.ERROR)
        s.key_press("r")
        self.assertEqual(s.controller.state, S.IDLE)

    def test_demo_script_completes_without_error(self):
        s = SimSession()
        shots = []
        run_demo_script(s, shots)
        self.assertEqual(s.controller.state, S.SITTING)
        self.assertEqual(len(shots), 7)


if __name__ == "__main__":
    unittest.main()
