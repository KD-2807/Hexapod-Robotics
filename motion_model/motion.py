"""Mô hình toán và adapter cho lõi điều khiển chung 54/45/77 mm.

GaitEngine dùng build_motion_controller, cùng nguồn với PC, mô phỏng 3D
và đối chiếu firmware C++. Thân: +X phải, +Y tiến, +Z lên.
ID chân: i,j,k,l,m,n. Chiều dài mm; fk/ik dùng radian; JointFrame dùng độ.
"""
import math
from dataclasses import dataclass

from shared.common.config_loader import ConfigLoader
from shared.common.enums import GaitType, RobotState
from shared.common.leg_geometry import forward_kinematics, inverse_kinematics, joint_chain
from shared.common.math_utils import Vec3
from shared.motion_core.factory import build_motion_controller
from shared.robot_core.transforms import rotate_rpy
from simulation.sim_backend import SimBackend

DT = 0.02


def finite(*values):
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Du lieu phai la so huu han")


def load_config(config_dir=None):
    """Bản đọc hiển thị suy ra từ config/; không lưu bản sao JSON."""
    loader = ConfigLoader(config_dir)
    robot = loader.load("robot_config")
    gait = loader.load("gait_config")
    safety = loader.load("safety_config")
    lengths = robot["link_lengths_mm"]
    return {"coxa":lengths["coxa"], "femur":lengths["femur"], "tibia":lengths["tibia"],
            "body_height":robot["stance"]["height_mm"], "shoulder_z":0.,
            "home_local_x":robot["stance"]["radius_mm"],
            "period":gait["gaits"][gait["default_gait"]]["cycle_time_s"],
            "lift_height":gait["step_height_mm"],
            "joint_limits_deg":[safety["joint_limits_deg"][n] for n in ("coxa","femur","tibia")],
            "legs":[{"name":l["id"], "label":l["name"], "mount":[l["x"],l["y"]],
                     "heading_deg":l["yaw_deg"], "group":l["group"]} for l in robot["legs"]]}


def fk(q, lengths):
    finite(*q,*lengths)
    return forward_kinematics(q,lengths)


def ik(point, lengths, limits_deg=None):
    finite(*point,*lengths)
    if min(lengths) <= 0:
        raise ValueError("Chieu dai khau phai > 0")
    if math.hypot(point[0],point[1]) < 1e-10:
        raise ValueError("Truc coxa suy bien: x=y=0")
    q, reachable = inverse_kinematics(point,lengths)
    if not reachable:
        raise ValueError("Ban chan ngoai vung voi toi (co bien 0.001 mm)")
    if limits_deg is not None:
        for index,(angle,(lo,hi)) in enumerate(zip(q,limits_deg)):
            if not lo-1e-8 <= math.degrees(angle) <= hi+1e-8:
                raise ValueError(f"q{index+1} vuot gioi han [{lo},{hi}] deg")
    return q


def leg_chain(q,lengths):
    finite(*q,*lengths)
    return joint_chain(q,lengths)


def leg_to_body(point,leg,cfg=None):
    x,y,z = point
    a = math.radians(leg["heading_deg"])
    c,s = math.cos(a),math.sin(a)
    return leg["mount"][0]+c*x-s*y,leg["mount"][1]+s*x+c*y,z


def body_to_leg(point,leg,cfg=None):
    x,y,z = point
    dx,dy = x-leg["mount"][0],y-leg["mount"][1]
    a = math.radians(leg["heading_deg"])
    c,s = math.cos(a),math.sin(a)
    return c*dx+s*dy,-s*dx+c*dy,z


def convex_hull(points):
    points=sorted(set((float(x),float(y)) for x,y in points))
    if len(points)<3:return points
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower,upper=[],[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def support_margin(points,com=(0.,0.)):
    hull=convex_hull(points)
    if len(hull)<3:return -math.inf
    x,y=com
    return min(((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/math.hypot(b[0]-a[0],b[1]-a[1])
               for a,b in zip(hull,hull[1:]+hull[:1]))


@dataclass(frozen=True)
class Command:
    """Lệnh chuẩn hóa [-1,1]: vx phải, vy tiến, wz quay CCW."""
    vx: float = 0.
    vy: float = 1.
    wz: float = 0.

    def __post_init__(self):
        finite(self.vx,self.vy,self.wz)
        if any(abs(v)>1 for v in (self.vx,self.vy,self.wz)):
            raise ValueError("vx/vy/wz phai trong [-1,1], khong phai mm/s hoac rad/s")


class GaitEngine:
    """Adapter quan sát MotionController, không tự tính một gait khác.

    Khởi tạo đứng ổn định trước khi đặt t=0; tăng tốc theo lõi điều khiển.
    step nhận bội số 20 ms, cùng chu kỳ firmware. Các điểm ground nằm
    trong hệ nền tham chiếu cục bộ, không phải odometry.
    """
    def __init__(self,command=None,gait="tripod",speed=.6,config_dir=None):
        self.command=command or Command()
        if gait not in ("tripod","wave","ripple"):
            raise ValueError("gait phai la tripod/wave/ripple")
        finite(speed)
        if not .1<=speed<=1.:
            raise ValueError("speed phai trong [0.1,1]")
        self.gait,self.speed,self.config_dir=gait,speed,config_dir
        self.cfg=load_config(config_dir)
        self.lengths=tuple(self.cfg[k] for k in ("coxa","femur","tibia"))
        self.backend=SimBackend()
        self.controller=build_motion_controller(self.backend,ConfigLoader(config_dir))
        self.controller.stand_up()
        for _ in range(500):
            if self.controller.state==RobotState.STANDING:break
            self.controller.update(DT)
            self._check()
        else:raise ValueError("Robot khong dung len duoc trong 10 giay")
        self.controller.set_gait(GaitType(gait))
        self.controller.set_speed(speed)
        self.controller.move(self.command.vx,self.command.vy,self.command.wz,speed)
        self._ticks=0
        self.time=0.

    def _check(self):
        if self.controller.state==RobotState.ERROR:
            raise ValueError(str(self.controller.snapshot()["error"]))

    def step(self,dt=DT):
        finite(dt)
        count=round(dt/DT)
        if dt<0 or dt>10 or abs(count*DT-dt)>1e-9:
            raise ValueError("dt phai la boi so 0.02 s, trong [0,10]")
        for _ in range(count):
            self.controller.update(DT)
            self._ticks+=1
            self._check()
        self.time=self._ticks*DT
        return self.frame()

    def frame(self):
        pose=self.controller.body_pose
        phase=self.controller.stance_phase_mask()
        angles=self.controller.frame.angles[:]
        legs={}
        for leg in self.controller.hexapod.legs:
            degrees=angles[leg.index*3:leg.index*3+3]
            q=tuple(math.radians(a) for a in degrees)
            local=fk(q,self.lengths)
            chain=[]
            for p in leg_chain(q,self.lengths):
                b=leg.leg_to_body(Vec3(*p));chain.append((b.x,b.y,b.z))
            ground=rotate_rpy(Vec3(*chain[-1]),math.radians(pose.roll),math.radians(pose.pitch),math.radians(pose.yaw))
            ground=(ground.x+pose.x,ground.y+pose.y,ground.z+self.cfg["body_height"]+pose.z)
            legs[leg.id]={"q":q,"q_deg":tuple(degrees),"local":local,"body":chain[-1],
                          "ground":ground,"contact":phase[leg.index],"chain":chain,"label":leg.name}
        support=[l["ground"][:2] for l in legs.values() if l["contact"]]
        return {"t":self.time,"state":self.controller.state.value,"pose":pose,"angles_deg":angles,
                "legs":legs,"support_margin":support_margin(support,(pose.x,pose.y))}
