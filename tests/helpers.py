"""Tiện ích dựng đối tượng cho test."""
from shared.common.config_loader import ConfigLoader
from shared.motion_core.factory import build_motion_controller
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.safety_config import SafetyConfig
from simulation.sim_backend import SimBackend

DT = 0.02


def make_hexapod() -> Hexapod:
    loader = ConfigLoader()
    return Hexapod(RobotConfig.from_dict(loader.load("robot_config")),
                   SafetyConfig.from_dict(loader.load("safety_config")))


def make_controller():
    backend = SimBackend()
    return build_motion_controller(backend), backend


def run(controller, seconds: float) -> None:
    for _ in range(int(round(seconds / DT))):
        controller.update(DT)


def standing_controller():
    controller, backend = make_controller()
    controller.stand_up()
    run(controller, 1.6)
    return controller, backend
