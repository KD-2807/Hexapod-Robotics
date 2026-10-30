"""Thân robot: giữ tư thế hiện tại."""
from shared.common.types import BodyPose


class Body:
    def __init__(self):
        self.pose = BodyPose()
