"""Composition root: lắp ráp MotionController từ thư mục config + một ActuatorBackend."""
from typing import Optional

from shared.common.config_loader import ConfigLoader
from shared.common.types import BodyPose
from shared.gait_core.gait_config import GaitConfig
from shared.gait_core.gait_factory import GaitFactory
from shared.interfaces.actuator_backend import ActuatorBackend
from shared.motion_core.context import MotionContext
from shared.motion_core.motion_controller import MotionController
from shared.posture_core.pose_config import PoseConfig
from shared.posture_core.posture_generator import PostureGenerator
from shared.robot_core.body_kinematics import BodyKinematics
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.motion_coordinator import MotionCoordinator
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.safety_config import SafetyConfig
from shared.robot_core.safety_guard import SafetyGuard


def build_motion_controller(backend: ActuatorBackend, loader: Optional[ConfigLoader] = None) -> MotionController:
    loader = loader or ConfigLoader()
    robot = RobotConfig.from_dict(loader.load("robot_config"))
    safety = SafetyConfig.from_dict(loader.load("safety_config"))
    gait_cfg = GaitConfig.from_dict(loader.load("gait_config"))
    pose_cfg = PoseConfig.from_dict(loader.load("pose_config"))

    hexapod = Hexapod(robot, safety)
    ctx = MotionContext(posture=PostureGenerator(pose_cfg),
                        gait_factory=GaitFactory(gait_cfg, hexapod.legs),
                        stand_pose=BodyPose(),
                        sit_pose=BodyPose(z=robot.sit_offset_z),
                        speed=gait_cfg.default_speed,
                        gait_type=gait_cfg.default_gait)
    return MotionController(hexapod, MotionCoordinator(hexapod, BodyKinematics(hexapod)),
                            SafetyGuard(hexapod, safety), backend, ctx, gait_cfg, pose_cfg.check_margin_deg)
