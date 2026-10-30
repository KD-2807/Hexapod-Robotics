import math
import unittest

from shared.common.enums import CommandType, ErrorCode, GaitType, RobotState as S
from shared.motion_core.errors import MotionError
from tests.helpers import DT, make_controller, run, standing_controller


class MotionControllerTest(unittest.TestCase):
    def test_lifecycle(self):
        mc, backend = make_controller()
        self.assertEqual(mc.state, S.IDLE)
        mc.stand_up()                               # IDLE: tự ENABLE
        self.assertEqual(mc.state, S.SITTING)
        self.assertTrue(backend.enabled)
        run(mc, 1.6)
        self.assertEqual(mc.state, S.STANDING)
        mc.move(0, 1, 0)
        run(mc, 0.3)
        self.assertEqual(mc.state, S.WALKING)
        mc.stop()
        run(mc, 1.0)
        self.assertEqual(mc.state, S.STANDING)
        mc.sit_down()
        run(mc, 1.6)
        self.assertEqual(mc.state, S.SITTING)
        mc.disable()
        self.assertEqual(mc.state, S.IDLE)
        self.assertFalse(backend.enabled)

    def test_stand_pose_joint_angles(self):
        mc, _ = standing_controller()
        coxa, femur, tibia = mc.frame.angles[:3]
        self.assertAlmostEqual(coxa, 0.0, places=3)
        self.assertGreater(femur, 0.0)
        self.assertLess(tibia, -45.0)

    def test_move_rejected_unless_standing(self):
        mc, _ = make_controller()
        with self.assertRaises(MotionError) as ctx:
            mc.move(0, 1, 0)
        self.assertEqual(ctx.exception.code, ErrorCode.BAD_STATE)

    def test_move_param_validation(self):
        mc, _ = standing_controller()
        with self.assertRaises(MotionError) as ctx:
            mc.move(0, 1.5, 0)
        self.assertEqual(ctx.exception.code, ErrorCode.BAD_PARAMS)
        with self.assertRaises(MotionError):
            mc.set_speed(5.0)
        with self.assertRaises(MotionError):
            mc.set_pose(99, 0, 0, 0)

    def test_set_gait_applies_after_stop(self):
        mc, _ = standing_controller()
        mc.move(0, 1, 0)
        run(mc, 0.5)
        mc.set_gait(GaitType.WAVE)
        self.assertEqual(mc.snapshot()["gait"], "wave")
        mc.stop()
        run(mc, 1.0)
        self.assertEqual(mc._ctx.gait_type, GaitType.WAVE)
        with self.assertRaises(MotionError):
            mc.set_gait(GaitType.ROTATION)

    def test_all_gaits_and_motions_stay_within_limits(self):
        for gait in (GaitType.TRIPOD, GaitType.WAVE, GaitType.RIPPLE):
            mc, _ = standing_controller()
            mc.set_gait(gait)
            for v in ((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (1, 1, 0), (0, 0, 1), (0, 0, -1), (0, 1, 1), (-1, -1, -1)):
                mc.move(*v, 1.0)
                run(mc, 5.0)
                self.assertNotEqual(mc.state, S.ERROR, (gait, v, mc.snapshot()["error"]))
                mc.stop()
                run(mc, 1.5)

    def test_joint_speed_never_exceeds_guard(self):
        mc, _ = standing_controller()
        mc.move(0, 1, 0.5, 1.0)
        prev = mc.frame.copy()
        for _ in range(400):
            mc.update(DT)
            self.assertLessEqual(mc.frame.max_abs_diff(prev) / DT, 360.0 + 1e-6)
            prev = mc.frame.copy()

    def test_random_velocities_never_error_at_neutral_pose(self):
        import random
        rng = random.Random(11)
        for gait in (GaitType.TRIPOD, GaitType.WAVE, GaitType.RIPPLE):
            mc, _ = standing_controller()
            mc.set_gait(gait)
            for _ in range(6):
                mc.move(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1), 1.0)
                run(mc, 3.0)
                self.assertNotEqual(mc.state, S.ERROR, mc.snapshot()["error"])

    def test_robot_actually_translates_feet_relative_to_body(self):
        mc, _ = standing_controller()
        start = list(mc.frame.angles)
        mc.move(0, 1, 0)
        run(mc, 0.7)
        self.assertGreater(max(abs(a - b) for a, b in zip(start, mc.frame.angles)), 5.0)

    def test_turn_to_translate_switch_decelerates_first(self):
        mc, _ = standing_controller()
        mc.move(0, 0, 1)
        run(mc, 1.0)
        self.assertIsNotNone(mc._action.name == "turn" or None)
        mc.move(0, 1, 0)
        seen_stop = False
        for _ in range(100):
            mc.update(DT)
            seen_stop = seen_stop or mc._ctx.velocity.is_zero()
        self.assertTrue(seen_stop)
        self.assertEqual(mc._action.name, "walk")
        self.assertNotEqual(mc.state, S.ERROR)

    def test_emergency_stop_and_reset(self):
        mc, backend = standing_controller()
        mc.move(0, 1, 0)
        run(mc, 0.5)
        mc.emergency_stop()
        self.assertEqual(mc.state, S.ERROR)
        self.assertFalse(backend.enabled)
        self.assertEqual(mc.snapshot()["error"]["code"], "ESTOP")
        with self.assertRaises(MotionError):
            mc.stand_up()
        with self.assertRaises(MotionError):
            mc.sit_down()
        mc.reset()
        self.assertEqual(mc.state, S.IDLE)
        self.assertIsNone(mc.snapshot()["error"])

    def test_hardware_failure_moves_to_error(self):
        mc, backend = standing_controller()
        backend.fail_next_apply = True
        mc.update(DT)
        self.assertEqual(mc.state, S.ERROR)
        self.assertEqual(mc.snapshot()["error"]["code"], "HARDWARE")

    def test_link_lost_stops_then_sits(self):
        mc, _ = standing_controller()
        mc.move(0, 1, 0)
        run(mc, 1.0)
        mc.on_link_lost()
        run(mc, 3.0)
        self.assertEqual(mc.state, S.SITTING)
        self.assertTrue(mc._ctx.velocity.is_zero())

    def test_sit_while_walking_stops_first(self):
        mc, _ = standing_controller()
        mc.move(0, 1, 0)
        run(mc, 0.5)
        mc.sit_down()
        run(mc, 3.0)
        self.assertEqual(mc.state, S.SITTING)

    def test_special_actions(self):
        for name in ("wave", "bob", "dance"):
            mc, _ = standing_controller()
            mc.run_action(name)
            with self.assertRaises(MotionError):
                mc.move(0, 1, 0)                    # đang bận
            run(mc, 7.0)
            self.assertEqual(mc.state, S.STANDING, name)
            self.assertAlmostEqual(mc._ctx.posture.current.z, 0.0)
        with self.assertRaises(MotionError):
            mc.run_action("fly")

    def test_stop_cancels_special(self):
        mc, _ = standing_controller()
        mc.run_action("dance")
        run(mc, 1.0)
        mc.stop()
        run(mc, 0.2)
        mc.move(0, 1, 0)                            # không còn bận

    def test_set_pose_changes_frame_smoothly(self):
        mc, _ = standing_controller()
        before = list(mc.frame.angles)
        mc.set_pose(15, 5, -5, 10)
        run(mc, 1.5)
        self.assertGreater(max(abs(a - b) for a, b in zip(before, mc.frame.angles)), 3.0)
        self.assertEqual(mc.state, S.STANDING)

    def test_infeasible_combined_pose_is_rejected(self):
        mc, _ = standing_controller()
        with self.assertRaises(MotionError) as ctx:
            mc.set_pose(-25, 15, 15, 20)               # từng trục hợp lệ nhưng tổ hợp vượt tầm
        self.assertEqual(ctx.exception.code, ErrorCode.LIMIT)
        mc.set_pose(10, 5, -5, 10)                      # tổ hợp vừa phải được chấp nhận

    def test_walking_clamps_pose_to_walk_envelope_and_restores(self):
        mc, _ = standing_controller()
        mc.set_pose(25, 10, 0, 0)
        run(mc, 2.0)
        mc.move(0, 1, 0)
        run(mc, 4.0)
        self.assertNotEqual(mc.state, S.ERROR)
        pose = mc._ctx.posture.current
        self.assertLessEqual(pose.z, 10.0 + 1e-6)
        self.assertLessEqual(pose.roll, 2.0 + 1e-6)
        mc.stop()
        run(mc, 3.0)
        self.assertAlmostEqual(mc._ctx.posture.current.z, 25.0)      # khôi phục tư thế người dùng đặt

    def test_walking_at_walk_envelope_corners(self):
        import itertools
        corners = itertools.product((-2, 10), (-2, 2), (-2, 2), (-5, 5))
        for k, (z, roll, pitch, yaw) in enumerate(corners):
            mc, _ = standing_controller()
            mc.set_gait((GaitType.TRIPOD, GaitType.WAVE, GaitType.RIPPLE)[k % 3])
            mc.set_pose(z, roll, pitch, yaw)
            run(mc, 1.5)
            for v in ((0, 1, 0), (1, 0, 0), (0, 0, 1), (-1, -1, 0)):
                mc.move(*v, 1.0)
                run(mc, 3.0)
                self.assertNotEqual(mc.state, S.ERROR, ((z, roll, pitch, yaw), v, mc.snapshot()["error"]))
                mc.stop()
                run(mc, 1.5)

    def test_servo_test_mode_only_when_sitting(self):
        mc, backend = make_controller()
        mc.enable()
        mc.set_servo(0, 1, 20.0)
        mc.set_servo(0, 1, 100.0, raw=True)
        self.assertEqual(backend.raw_servo_deg[(0, 1)], 100.0)
        with self.assertRaises(MotionError):
            mc.set_servo(0, 1, 500.0)
        with self.assertRaises(MotionError):
            mc.set_servo(9, 1, 0.0)
        mc.stand_up()
        run(mc, 1.6)
        with self.assertRaises(MotionError):
            mc.set_servo(0, 1, 20.0)


if __name__ == "__main__":
    unittest.main()
