import unittest

from shared.common.enums import CommandType as C, ErrorCode, RobotState as S
from shared.motion_core.errors import MotionError
from shared.motion_core.state_machine import StateMachine


class StateMachineTest(unittest.TestCase):
    def test_happy_path(self):
        m = StateMachine()
        for state in (S.SITTING, S.STANDING, S.WALKING, S.STANDING, S.SITTING, S.IDLE):
            m.transition(state)
        self.assertEqual(m.state, S.IDLE)

    def test_invalid_transition_raises(self):
        m = StateMachine()
        with self.assertRaises(MotionError) as ctx:
            m.transition(S.WALKING)
        self.assertEqual(ctx.exception.code, ErrorCode.BAD_STATE)

    def test_any_state_can_fail_and_only_reset_recovers(self):
        m = StateMachine()
        m.transition(S.SITTING)
        m.fail()
        self.assertEqual(m.state, S.ERROR)
        self.assertFalse(m.accepts(C.STAND_UP))
        self.assertFalse(m.accepts(C.SIT_DOWN))
        self.assertTrue(m.accepts(C.RESET))
        m.transition(S.IDLE)

    def test_move_only_when_standing_or_walking(self):
        m = StateMachine()
        self.assertFalse(m.accepts(C.MOVE))
        m.transition(S.SITTING)
        self.assertFalse(m.accepts(C.MOVE))
        m.transition(S.STANDING)
        self.assertTrue(m.accepts(C.MOVE))
        m.transition(S.WALKING)
        self.assertTrue(m.accepts(C.MOVE))

    def test_emergency_stop_and_heartbeat_always_accepted(self):
        m = StateMachine()
        for state in S:
            m.state = state
            self.assertTrue(m.accepts(C.EMERGENCY_STOP))
            self.assertTrue(m.accepts(C.HEARTBEAT))


if __name__ == "__main__":
    unittest.main()
