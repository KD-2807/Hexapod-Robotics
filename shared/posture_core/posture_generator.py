"""PostureGenerator: nội suy mượt tư thế thân về tư thế đích (giới hạn tốc độ từng bậc tự do)."""
from typing import Optional

from shared.common.math_utils import clamp, move_towards
from shared.common.types import BodyPose
from shared.posture_core.elevation import Elevation
from shared.posture_core.pitch import Pitch
from shared.posture_core.pose_config import PoseConfig
from shared.posture_core.roll import Roll
from shared.posture_core.yaw import Yaw


class PostureGenerator:
    def __init__(self, config: PoseConfig):
        self._config = config
        self.elevation = Elevation(*config.z_limits)
        self.roll = Roll(-config.roll_limit, config.roll_limit)
        self.pitch = Pitch(-config.pitch_limit, config.pitch_limit)
        self.yaw = Yaw(-config.yaw_limit, config.yaw_limit)
        self.walking = False        # True: tư thế đích bị kẹp vào vùng cho phép khi bước
        self._current = BodyPose()
        self._target = BodyPose()

    @property
    def current(self) -> BodyPose:
        return self._current

    @property
    def target(self) -> BodyPose:
        return self._target

    def _effective_target(self) -> BodyPose:
        if not self.walking:
            return self._target
        c, t = self._config, self._target
        return BodyPose(x=t.x, y=t.y,
                        z=clamp(t.z, *c.walk_z_limits),
                        roll=clamp(t.roll, -c.walk_roll_limit, c.walk_roll_limit),
                        pitch=clamp(t.pitch, -c.walk_pitch_limit, c.walk_pitch_limit),
                        yaw=clamp(t.yaw, -c.walk_yaw_limit, c.walk_yaw_limit))

    @property
    def reached(self) -> bool:
        return self._current == self._effective_target()

    def in_walking_envelope(self) -> bool:
        c, p = self._config, self._current
        return (c.walk_z_limits[0] <= p.z <= c.walk_z_limits[1] and abs(p.roll) <= c.walk_roll_limit
                and abs(p.pitch) <= c.walk_pitch_limit and abs(p.yaw) <= c.walk_yaw_limit)

    def validate(self, z: float, roll: float, pitch: float, yaw: float) -> Optional[str]:
        """None nếu hợp lệ, ngược lại là tên bậc tự do vượt giới hạn."""
        for name, posture, value in (("z", self.elevation, z), ("roll", self.roll, roll),
                                     ("pitch", self.pitch, pitch), ("yaw", self.yaw, yaw)):
            if not posture.in_range(value):
                return name
        return None

    def compose(self, z: float, roll: float, pitch: float, yaw: float) -> BodyPose:
        pose = BodyPose()
        for posture, value in ((self.elevation, z), (self.roll, roll), (self.pitch, pitch), (self.yaw, yaw)):
            pose = posture.apply(pose, posture.clamp(value))
        return pose

    def set_target(self, pose: BodyPose) -> None:
        self._target = pose

    def reset(self, pose: BodyPose) -> None:
        self._current = self._target = pose
        self.walking = False

    def update(self, dt: float) -> BodyPose:
        cur, tgt = self._current, self._effective_target()
        dz = self._config.z_rate * dt
        da = self._config.angle_rate * dt
        self._current = BodyPose(
            x=cur.x, y=cur.y,
            z=move_towards(cur.z, tgt.z, dz),
            roll=move_towards(cur.roll, tgt.roll, da),
            pitch=move_towards(cur.pitch, tgt.pitch, da),
            yaw=move_towards(cur.yaw, tgt.yaw, da))
        return self._current
