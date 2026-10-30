import unittest

from shared.common.config_loader import ConfigLoader
from shared.common.enums import GaitType
from shared.common.types import Velocity
from shared.gait_core.gait_config import GaitConfig
from shared.gait_core.gait_factory import GaitFactory
from shared.gait_core.rotation_gait import RotationGait
from tests.helpers import make_hexapod


class GaitTest(unittest.TestCase):
    def setUp(self):
        self.hexapod = make_hexapod()
        self.config = GaitConfig.from_dict(ConfigLoader().load("gait_config"))
        self.factory = GaitFactory(self.config, self.hexapod.legs)

    def _min_legs_on_ground(self, gait_type):
        gait = self.factory.create(gait_type)
        worst = 6
        for k in range(1200):
            gait.t = k / 1200.0
            swinging = sum(1 for leg in range(6) if gait._phase.locate(gait.t, leg)[0])
            worst = min(worst, 6 - swinging)
        return worst

    def test_ground_contact_matches_report(self):
        self.assertEqual(self._min_legs_on_ground(GaitType.TRIPOD), 3)
        self.assertEqual(self._min_legs_on_ground(GaitType.WAVE), 5)
        self.assertEqual(self._min_legs_on_ground(GaitType.RIPPLE), 4)

    def test_tripod_groups_alternate(self):
        gait = self.factory.create(GaitType.TRIPOD)
        gait.t = 0.1
        swing = [gait._phase.locate(gait.t, i)[0] for i in range(6)]
        self.assertEqual(swing, [True, False, True, False, True, False])   # i,k,m nhấc; j,l,n chống

    def test_zero_velocity_gives_zero_offsets(self):
        gait = self.factory.create(GaitType.TRIPOD)
        for k in range(50):
            gait.advance(0.02, 1.0)
            for o in gait.foot_offsets(Velocity()):
                self.assertEqual((o.x, o.y, o.z), (0.0, 0.0, 0.0))

    def test_trajectory_is_continuous(self):
        for gait_type in (GaitType.TRIPOD, GaitType.WAVE, GaitType.RIPPLE):
            gait = self.factory.create(gait_type)
            prev = gait.foot_offsets(Velocity(0, 1, 0))
            for _ in range(400):
                gait.advance(0.01, 1.0)
                cur = gait.foot_offsets(Velocity(0, 1, 0))
                for a, b in zip(prev, cur):
                    self.assertLess(((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5, 3.0)
                prev = cur

    def test_forward_stance_moves_backward_swing_forward(self):
        gait = self.factory.create(GaitType.TRIPOD)
        gait.t = 0.25                          # chân i (nhóm A) đang vung giữa chừng
        o = gait.foot_offsets(Velocity(0, 1, 0))
        self.assertGreater(o[0].z, 5.0)        # đang nhấc
        gait.t = 0.55
        a = gait.foot_offsets(Velocity(0, 1, 0))[0].y
        gait.t = 0.85
        b = gait.foot_offsets(Velocity(0, 1, 0))[0].y
        self.assertLess(b, a)                  # pha đứng: bàn chân lùi về phía sau thân

    def test_rotation_gait_ignores_translation(self):
        gait = RotationGait(self.config, self.config.profiles[GaitType.ROTATION], self.hexapod.legs)
        gait.t = 0.1
        a = gait.foot_offsets(Velocity(1, 1, 0.5))
        b = gait.foot_offsets(Velocity(0, 0, 0.5))
        self.assertEqual(a, b)

    def test_turn_strides_are_tangential(self):
        gait = self.factory.create(GaitType.TRIPOD)
        for leg in self.hexapod.legs:
            s = gait.stride_for(leg, Velocity(0, 0, 1))
            f = leg.neutral_foot
            self.assertAlmostEqual(s.x * f.x + s.y * f.y, 0.0, places=6)   # vuông góc bán kính

    def test_stride_is_clamped(self):
        gait = self.factory.create(GaitType.TRIPOD)
        for leg in self.hexapod.legs:
            self.assertLessEqual(gait.stride_for(leg, Velocity(1, 1, 1)).norm_xy(), self.config.max_stride + 1e-9)


if __name__ == "__main__":
    unittest.main()
