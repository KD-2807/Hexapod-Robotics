import unittest

from shared.common.math_utils import Vec3
from shared.common.types import BodyPose
from shared.robot_core.body_kinematics import BodyKinematics
from shared.robot_core.motion_coordinator import MotionCoordinator
from tests.helpers import make_hexapod


class BodyKinematicsTest(unittest.TestCase):
    def setUp(self):
        self.hexapod = make_hexapod()
        self.body_kin = BodyKinematics(self.hexapod)
        self.coordinator = MotionCoordinator(self.hexapod, self.body_kin)
        self.zero = [Vec3()] * 6

    def test_neutral_targets_identical_for_all_legs(self):
        targets = self.body_kin.leg_targets(BodyPose(), self.hexapod.neutral_feet())
        cfg = self.hexapod.config
        for t in targets:
            self.assertAlmostEqual(t.x, cfg.stance_radius, places=6)
            self.assertAlmostEqual(t.y, 0.0, places=6)
            self.assertAlmostEqual(t.z, -cfg.stand_height, places=6)

    def test_left_right_symmetry_of_joint_angles(self):
        frame = self.coordinator.compute(self.zero, BodyPose()).frame
        for leg in range(1, 6):
            self.assertEqual([round(a, 6) for a in frame.angles[:3]],
                             [round(a, 6) for a in frame.angles[leg * 3:leg * 3 + 3]])

    def test_raise_body_lowers_foot_in_leg_frame(self):
        up = self.body_kin.leg_targets(BodyPose(z=10), self.hexapod.neutral_feet())
        self.assertAlmostEqual(up[0].z, -self.hexapod.config.stand_height - 10, places=6)

    def test_roll_right_side_down_extends_right_legs(self):
        # roll dương: bên phải thấp xuống -> bàn chân bên phải gần thân hơn theo trục z (bớt xuống)
        t = self.body_kin.leg_targets(BodyPose(roll=10), self.hexapod.neutral_feet())
        right, left = t[0], t[3]
        self.assertGreater(right.z, left.z)

    def test_pitch_up_raises_front_feet_distance(self):
        t = self.body_kin.leg_targets(BodyPose(pitch=10), self.hexapod.neutral_feet())
        front, rear = t[4], t[1]                 # LEFT_FRONT, RIGHT_REAR
        self.assertLess(front.z, rear.z)         # đầu ngẩng: chân trước xa thân hơn (z âm hơn)

    def test_yaw_rotates_feet_around_body(self):
        t0 = self.body_kin.leg_targets(BodyPose(), self.hexapod.neutral_feet())[0]
        t1 = self.body_kin.leg_targets(BodyPose(yaw=10), self.hexapod.neutral_feet())[0]
        self.assertNotAlmostEqual(t0.y, t1.y, places=3)

    def test_single_axis_pose_extremes_reachable(self):
        cfg_poses = [BodyPose(z=30), BodyPose(z=-25), BodyPose(roll=15), BodyPose(roll=-15),
                     BodyPose(pitch=15), BodyPose(pitch=-15), BodyPose(yaw=20), BodyPose(yaw=-20)]
        for pose in cfg_poses:
            self.assertTrue(self.coordinator.compute(self.zero, pose).reachable, pose)


if __name__ == "__main__":
    unittest.main()
