"""MotionCoordinator: ghép (độ dịch bàn chân từ gait) + (tư thế thân) -> IK -> JointFrame."""
from dataclasses import dataclass
from typing import Sequence

from shared.common.math_utils import Vec3, rad2deg
from shared.common.types import BodyPose
from shared.robot_core.body_kinematics import BodyKinematics
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.joint_frame import JointFrame


@dataclass
class CoordinatorResult:
    frame: JointFrame
    reachable: bool


class MotionCoordinator:
    def __init__(self, hexapod: Hexapod, body_kinematics: BodyKinematics):
        self._hexapod = hexapod
        self._body_kin = body_kinematics

    def compute(self, foot_offsets: Sequence[Vec3], pose: BodyPose) -> CoordinatorResult:
        feet = [leg.neutral_foot + offset for leg, offset in zip(self._hexapod.legs, foot_offsets)]
        targets = self._body_kin.leg_targets(pose, feet)

        frame = JointFrame()
        reachable = True
        for leg, target in zip(self._hexapod.legs, targets):
            result = leg.kinematics.inverse(target)
            reachable = reachable and result.reachable
            for joint, angle in zip(leg.joints, result.angles):
                frame.set(leg.index, joint.type, rad2deg(angle))
        return CoordinatorResult(frame, reachable)
