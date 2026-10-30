"""Động học thuận/nghịch dùng chung cho chân ba khâu.

Chiều dài theo mm, góc theo radian. Hệ chân: x hướng ra ngoài, z hướng lên.
Hình học lấy từ config/robot_config.json. Góc toán học dùng radian.
"""
import math


def inverse_kinematics(point, lengths, reach_margin=1e-3):
    """Trả về (ba góc radian, reachable), nhánh gối âm.

    Giữ chính sách biên của lõi điều khiển: báo không tới được, đồng thời
    tạo nghiệm hữu hạn tại biên. Không dùng nghiệm khi reachable=False.
    """
    x, y, z = point
    l1, l2, l3 = lengths
    t1 = math.atan2(y, x)
    horizontal = math.hypot(x, y) - l1
    distance = math.hypot(z, horizontal)
    low = abs(l2-l3) + reach_margin
    high = l2+l3 - reach_margin
    reachable = low <= distance <= high
    distance = max(low, min(high, distance))
    clamp = lambda v: max(-1.0, min(1.0, v))
    phi1 = math.acos(clamp((l2*l2+distance*distance-l3*l3)/(2*l2*distance)))
    t2 = phi1 + math.atan2(z, horizontal)
    t3 = -math.pi + math.acos(clamp((l2*l2+l3*l3-distance*distance)/(2*l2*l3)))
    return (t1, t2, t3), reachable


def forward_kinematics(angles, lengths):
    q1, q2, q3 = angles
    l1, l2, l3 = lengths
    radius = l1 + l2 * math.cos(q2) + l3 * math.cos(q2 + q3)
    z = l2 * math.sin(q2) + l3 * math.sin(q2 + q3)
    return radius * math.cos(q1), radius * math.sin(q1), z


def joint_chain(angles, lengths):
    """Trả về gốc coxa, cuối coxa, đầu gối và bàn chân trong hệ chân."""
    q1, q2, _ = angles
    l1, l2, _ = lengths
    c, s = math.cos(q1), math.sin(q1)
    knee_radius = l1 + l2 * math.cos(q2)
    return [(0.0, 0.0, 0.0), (l1 * c, l1 * s, 0.0),
            (knee_radius * c, knee_radius * s, l2 * math.sin(q2)),
            forward_kinematics(angles, lengths)]
