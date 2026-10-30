"""Giữ Python và firmware C++ đồng bộ: header sinh tự động còn mới, và hai bản cho kết quả giống nhau."""
import os
import shutil
import subprocess
import unittest

from shared.common.config_loader import ConfigLoader
from tools import gen_firmware_config
from tools.crosscheck_firmware import SCENARIO, build_cpp, compare_scenario, python_ticks
from tools.scenario_runner import run_scenario
from shared.motion_core.factory import build_motion_controller
from simulation.sim_backend import SimBackend


class GeneratedConfigTest(unittest.TestCase):
    def test_header_matches_json(self):
        expected = gen_firmware_config.generate(ConfigLoader())
        with open(gen_firmware_config.OUTPUT, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), expected,
                             "generated_config.h đã cũ: chạy python -m tools.gen_firmware_config")

    def test_every_gait_leg_has_a_slot(self):
        text = gen_firmware_config.generate(ConfigLoader())
        self.assertNotIn("-1", text.split("kGaits")[1].split("};")[0])


@unittest.skipUnless(shutil.which("g++") and shutil.which("make"), "cần g++ và make")
class FirmwareCrossCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = build_cpp()

    def test_cpp_unit_tests_pass(self):
        result = subprocess.run([self.binary, "unit"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:])

    def test_scenario_identical_between_python_and_cpp(self):
        cpp = subprocess.check_output([self.binary, "dump", SCENARIO], text=True).splitlines()
        with open(SCENARIO, encoding="utf-8") as handle:
            py = run_scenario(build_motion_controller(SimBackend()), handle.read())
        ok, message = compare_scenario(py, cpp, 0.05)
        self.assertTrue(ok, message)
        self.assertTrue(any(line.startswith("ERR") for line in py))     # kịch bản có cả nhánh lỗi

    def test_pwm_ticks_identical(self):
        cpp = [tuple(int(x) for x in line.split()[1:])
               for line in subprocess.check_output([self.binary, "ticks"], text=True).splitlines()]
        for a, b in zip(python_ticks(), cpp):
            self.assertEqual(a[:2], b[:2])
            self.assertLessEqual(abs(a[2] - b[2]), 1)


if __name__ == "__main__":
    unittest.main()
