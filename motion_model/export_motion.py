"""Xuất đúng JointFrame của bộ điều khiển chung, không phát PWM."""
import argparse
import csv
import math
from pathlib import Path
from .motion import Command, DT, GaitEngine


def tick_count(value, label):
    if not math.isfinite(value) or value <= 0 or abs(round(value/DT)*DT-value)>1e-9:
        raise ValueError(label+" phai > 0 va la boi so 0.02 s")
    return round(value/DT)


def export(path, seconds=8., dt=DT, vx=0., vy=1., wz=0., gait="tripod", speed=.6, config_dir=None):
    total=tick_count(seconds,"seconds")
    stride=tick_count(dt,"dt")
    if seconds>3600 or dt>10 or total%stride:
        raise ValueError("seconds <= 3600, dt <= 10 va seconds phai chia het cho dt")
    engine=GaitEngine(Command(vx,vy,wz),gait,speed,config_dir)
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+".tmp")
    header=["time_s","state","pose_z_offset_mm","roll_deg","pitch_deg","yaw_deg","phase_support_margin_mm"]
    for name in engine.frame()["legs"]:
        header += [name+"_stance_phase"]+[f"{name}_q{i}_deg" for i in (1,2,3)]+[f"{name}_foot_{a}_ground_local_mm" for a in "xyz"]
    count,minimum=0,math.inf
    try:
        with temp.open("w",newline="",encoding="utf-8") as f:
            writer=csv.writer(f);writer.writerow(header)
            for index in range(total//stride+1):
                frame=engine.frame() if index==0 else engine.step(dt)
                pose=frame["pose"]
                row=[frame["t"],frame["state"],pose.z,pose.roll,pose.pitch,pose.yaw,frame["support_margin"]]
                for leg in frame["legs"].values():
                    row += [int(leg["contact"])]+list(leg["q_deg"])+list(leg["ground"])
                writer.writerow(row);count+=1;minimum=min(minimum,frame["support_margin"])
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return count,minimum


def main(argv=None):
    parser=argparse.ArgumentParser(description="Xuat 18 goc JointFrame 54/45/77 mm, dung loi dieu khien chung")
    parser.add_argument("--out",default=str(Path(__file__).parent/"output/motion.csv"))
    parser.add_argument("--seconds",type=float,default=8.)
    parser.add_argument("--dt",type=float,default=DT)
    parser.add_argument("--vx",type=float,default=0.,help="Lenh chuan hoa [-1,1], duong sang phai")
    parser.add_argument("--vy",type=float,default=1.,help="Lenh chuan hoa [-1,1], duong di tien")
    parser.add_argument("--wz",type=float,default=0.,help="Lenh chuan hoa [-1,1], quay CCW")
    parser.add_argument("--speed",type=float,default=.6)
    parser.add_argument("--gait",choices=["tripod","wave","ripple"],default="tripod")
    parser.add_argument("--config-dir")
    a=parser.parse_args(argv)
    try:
        count,margin=export(a.out,a.seconds,a.dt,a.vx,a.vy,a.wz,a.gait,a.speed,a.config_dir)
    except (ValueError,OSError) as exc:
        parser.exit(1,f"KHONG XUAT: {exc}\n")
    print(f"Da xuat {count} mau: {a.out}; bien chong theo lich pha = {margin:.3f} mm (COM gia dinh).")


if __name__=="__main__":main()
