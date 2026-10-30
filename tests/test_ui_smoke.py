"""Kiểm tra UI không cần màn hình: thay tkinter bằng MagicMock để chạy qua toàn bộ code dựng giao diện."""
import importlib
import sys
import unittest
from unittest import mock

from pc_app.keyboard_mapper import KeyboardMapper


class KeyboardMapperTest(unittest.TestCase):
    def test_combination_and_release(self):
        k = KeyboardMapper()
        self.assertEqual(k.press("w"), (0.0, 1.0, 0.0))
        self.assertEqual(k.press("d"), (1.0, 1.0, 0.0))
        self.assertEqual(k.press("q"), (1.0, 1.0, 1.0))
        self.assertEqual(k.release("w"), (1.0, 0.0, 1.0))
        k.release("d"); k.release("q")
        self.assertEqual(k.vector(), (0.0, 0.0, 0.0))

    def test_opposite_keys_cancel_and_unknown_ignored(self):
        k = KeyboardMapper()
        k.press("a"); k.press("d")
        self.assertEqual(k.vector(), (0.0, 0.0, 0.0))
        self.assertEqual(k.press("x"), (0.0, 0.0, 0.0))


class UiBuildSmokeTest(unittest.TestCase):
    def test_main_window_builds_and_handles_events(self):
        fake_tk = mock.MagicMock()
        modules = {"tkinter": fake_tk, "tkinter.ttk": fake_tk.ttk}
        with mock.patch.dict(sys.modules, modules):
            for name in [m for m in sys.modules if m.startswith("pc_app.ui.")]:
                del sys.modules[name]
            main_window = importlib.import_module("pc_app.ui.main_window")
            from pc_app.models.robot_status import RobotStatus
            controller = mock.MagicMock()
            listeners = {}
            controller.add_status_listener.side_effect = lambda fn: listeners.setdefault("status", fn)
            controller.add_connection_listener.side_effect = lambda fn: listeners.setdefault("conn", fn)
            window = main_window.MainWindow(mock.MagicMock(), controller, {"default_speed": 0.6})
            listeners["status"](RobotStatus(state="WALKING"))
            listeners["conn"](True, "ok")
            window._poll()
            listeners["conn"](False, "bye")
            window._poll()
        for name in [m for m in sys.modules if m.startswith("pc_app.ui.")]:
            del sys.modules[name]          # tránh lưu bản dựng bằng mock cho test khác


if __name__ == "__main__":
    unittest.main()
