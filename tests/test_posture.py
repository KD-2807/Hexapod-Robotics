import unittest

from shared.common.config_loader import ConfigLoader
from shared.common.types import BodyPose
from shared.posture_core.pose_config import PoseConfig
from shared.posture_core.posture_generator import PostureGenerator


class PostureTest(unittest.TestCase):
    def setUp(self):
        self.gen = PostureGenerator(PoseConfig.from_dict(ConfigLoader().load("pose_config")))

    def test_validate(self):
        self.assertIsNone(self.gen.validate(0, 0, 0, 0))
        self.assertEqual(self.gen.validate(100, 0, 0, 0), "z")
        self.assertEqual(self.gen.validate(0, 0, 99, 0), "pitch")

    def test_compose_clamps(self):
        pose = self.gen.compose(100, -99, 99, -99)
        self.assertEqual((pose.z, pose.roll, pose.pitch, pose.yaw), (30.0, -15.0, 15.0, -20.0))

    def test_interpolation_is_rate_limited_and_reaches_target(self):
        self.gen.set_target(BodyPose(z=20, roll=10))
        first = self.gen.update(0.1)
        self.assertAlmostEqual(first.z, 4.0)           # 40 mm/s * 0.1 s
        self.assertAlmostEqual(first.roll, 4.0)        # 40 deg/s * 0.1 s
        for _ in range(20):
            self.gen.update(0.1)
        self.assertTrue(self.gen.reached)
        self.assertEqual(self.gen.current, BodyPose(z=20, roll=10))


if __name__ == "__main__":
    unittest.main()
