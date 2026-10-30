"""Hexapod = 1 Body + 6 Leg (mỗi Leg 3 Joint)."""
from typing import List

from shared.common.enums import JointType
from shared.common.constants import NUM_LEGS
from shared.common.math_utils import Vec3
from shared.robot_core.body import Body
from shared.robot_core.joint import Joint
from shared.robot_core.joint_frame import JointFrame
from shared.robot_core.leg import Leg
from shared.robot_core.leg_kinematics import LegKinematics
from shared.robot_core.robot_config import RobotConfig
from shared.robot_core.safety_config import SafetyConfig


class Hexapod:
    def __init__(self, config: RobotConfig, safety: SafetyConfig):
        if len(config.legs) != NUM_LEGS:
            raise ValueError("robot_config phải có đúng %d chân" % NUM_LEGS)
        self.config = config
        self.body = Body()
        self.legs: List[Leg] = []
        for index, spec in enumerate(config.legs):
            joints = [Joint(jt, *safety.joint_limits[jt]) for jt in JointType]
            kin = LegKinematics(config.coxa, config.femur, config.tibia)
            self.legs.append(Leg(index, spec, kin, joints, config.stance_radius, config.stand_height))

    def neutral_feet(self) -> List[Vec3]:
        return [leg.neutral_foot for leg in self.legs]

    def load_frame(self, frame: JointFrame) -> None:
        for leg in self.legs:
            for joint in leg.joints:
                joint.set_angle(frame.get(leg.index, joint.type))

    def read_frame(self) -> JointFrame:
        frame = JointFrame()
        for leg in self.legs:
            for joint in leg.joints:
                frame.set(leg.index, joint.type, joint.angle_deg)
        return frame
