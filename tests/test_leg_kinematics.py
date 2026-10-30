import math
import unittest

from shared.common.math_utils import Vec3
from shared.robot_core.leg_kinematics import LegKinematics


class LegKinematicsTest(unittest.TestCase):
    def setUp(self):
        self.kin = LegKinematics(54.0, 45.0, 77.0)

    def test_forward_straight_leg(self):
        p = self.kin.forward(0, 0, 0)
        self.assertAlmostEqual(p.x, 54 + 45 + 77)
        self.assertAlmostEqual(p.z, 0)

    def test_inverse_forward_roundtrip(self):
        for target in (Vec3(110, 0, -60), Vec3(120, 30, -50), Vec3(90, -20, -30), Vec3(100, 10, -75)):
            result = self.kin.inverse(target)
            self.assertTrue(result.reachable)
            back = self.kin.forward(*result.angles)
            self.assertAlmostEqual(back.x, target.x, places=6)
            self.assertAlmostEqual(back.y, target.y, places=6)
            self.assertAlmostEqual(back.z, target.z, places=6)

    def test_standing_angles_match_report_formula(self):
        # (x, z) = (150, -60): r2 = 96, r1 = hypot(60, 96)
        result = self.kin.inverse(Vec3(150, 0, -60))
        r1 = math.hypot(60, 96)
        phi1 = math.acos((45 ** 2 + r1 ** 2 - 77 ** 2) / (2 * 45 * r1))
        self.assertAlmostEqual(result.angles[1], phi1 + math.atan2(-60, 96))

    def test_unreachable_is_flagged_and_finite(self):
        result = self.kin.inverse(Vec3(500, 0, -60))
        self.assertFalse(result.reachable)
        self.assertTrue(all(math.isfinite(a) for a in result.angles))

    def test_too_close_is_flagged_and_finite(self):
        result = self.kin.inverse(Vec3(54, 0, -5))
        self.assertFalse(result.reachable)
        self.assertTrue(all(math.isfinite(a) for a in result.angles))


if __name__ == "__main__":
    unittest.main()
