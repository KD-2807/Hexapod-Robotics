import unittest

from shared.common.config_loader import ConfigLoader
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.safety_config import SafetyConfig
from shared.robot_core.servo_calibration import CalibrationTable, ServoCalibration


class ServoCalibrationTest(unittest.TestCase):
    def test_angle_and_pulse_mapping(self):
        cal = ServoCalibration(offset_deg=90, direction=-1, pulse_min_us=500, pulse_max_us=2400)
        self.assertEqual(cal.servo_angle(0), 90)
        self.assertEqual(cal.servo_angle(30), 60)
        self.assertEqual(cal.servo_angle(500), 0)             # kẹp 0..180
        self.assertEqual(cal.pulse_us(0), 500)
        self.assertEqual(cal.pulse_us(180), 2400)
        self.assertAlmostEqual(cal.pulse_us(90), 1450)
        self.assertAlmostEqual(cal.joint_angle(cal.servo_angle(25)), 25)

    def test_default_table_covers_all_joint_limits_within_servo_range(self):
        loader = ConfigLoader()
        robot = RobotConfig.from_dict(loader.load("robot_config"))
        safety = SafetyConfig.from_dict(loader.load("safety_config"))
        table = CalibrationTable.from_dict(loader.load("servo_calibration"), robot)
        for leg in range(6):
            for joint, (lo, hi) in enumerate(safety.joint_limits[j] for j in sorted(safety.joint_limits)):
                cal = table.get(leg, joint)
                for angle in (lo, hi):
                    raw = cal.offset_deg + cal.direction * angle
                    self.assertTrue(0.0 <= raw <= 180.0, (leg, joint, angle, raw))

    def test_left_right_mirrored(self):
        loader = ConfigLoader()
        robot = RobotConfig.from_dict(loader.load("robot_config"))
        table = CalibrationTable.from_dict(loader.load("servo_calibration"), robot)
        right, left = table.get(0, 1), table.get(3, 1)
        self.assertEqual(right.servo_angle(20) + left.servo_angle(20), 180)


if __name__ == "__main__":
    unittest.main()
