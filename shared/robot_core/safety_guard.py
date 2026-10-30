"""SafetyGuard: kiểm tra JointFrame (NaN, giới hạn góc, tốc độ) trước khi xuất ra servo."""
from dataclasses import dataclass
from typing import Optional

from shared.common.math_utils import clamp
from shared.robot_core.hexapod import Hexapod
from shared.robot_core.joint_frame import JointFrame
from shared.robot_core.safety_config import SafetyConfig


@dataclass
class SafetyResult:
    ok: bool
    frame: JointFrame
    reason: str = ""


class SafetyGuard:
    def __init__(self, hexapod: Hexapod, config: SafetyConfig):
        self._hexapod = hexapod
        self._config = config
        self._previous: Optional[JointFrame] = None

    def reset(self, frame: Optional[JointFrame] = None) -> None:
        self._previous = frame.copy() if frame is not None else None

    def filter(self, frame: JointFrame, dt: float) -> SafetyResult:
        """Trả về frame đã kẹp giới hạn + giới hạn tốc độ; ok=False nếu vi phạm nghiêm trọng."""
        if not frame.is_finite():
            return SafetyResult(False, self._fallback(frame), "NaN trong JointFrame")

        safe = frame.copy()
        margin = self._config.angle_margin_deg
        reason = ""
        for leg in self._hexapod.legs:
            for joint in leg.joints:
                angle = safe.get(leg.index, joint.type)
                if not reason and not (joint.min_deg - margin <= angle <= joint.max_deg + margin):
                    reason = "%s.%s=%.1f ngoài [%.0f, %.0f]" % (
                        leg.name, joint.type.name.lower(), angle, joint.min_deg, joint.max_deg)
                safe.set(leg.index, joint.type, joint.clamped(angle))

        if self._previous is not None:
            max_step = self._config.max_joint_speed_dps * dt
            for i, (new, old) in enumerate(zip(safe.angles, self._previous.angles)):
                safe.angles[i] = clamp(new, old - max_step, old + max_step)

        if reason:
            return SafetyResult(False, self._fallback(safe), reason)
        self._previous = safe.copy()
        return SafetyResult(True, safe)

    def _fallback(self, frame: JointFrame) -> JointFrame:
        return self._previous.copy() if self._previous is not None else frame
