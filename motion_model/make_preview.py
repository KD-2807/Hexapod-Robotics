"""Tuy chon: tao anh/GIF bang matplotlib va Pillow. Khong can de chay GUI."""
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon
from .motion import GaitEngine, Command, load_config, convex_hull, leg_chain, fk

ROOT=Path(__file__).parent
BG="#101a2b"
PANEL="#142239"
INK="#e3ecf5"
GREEN="#3fd4b2"
AMBER="#ffbb65"


def frames(seconds=4.,dt=.04):
    engine=GaitEngine(command=Command(0,1,0))
    result=[engine.frame()]
    for _ in range(round(seconds/dt)):result.append(engine.step(dt))
    return engine,result


def draw_frame(fig,frame,engine):
    fig.clear()
    fig.patch.set_facecolor(BG)
    ax=fig.add_axes([.06,.18,.40,.61])
    ax2=fig.add_axes([.54,.18,.39,.61],projection="3d")
    for a in [ax,ax2]:
        a.set_facecolor(PANEL)
        a.tick_params(colors="#a4b5cc",labelsize=8)
    ax.set_title("TOP VIEW / BODY FRAME",loc="left",color=INK,fontsize=12,pad=14)
    support=convex_hull([l["body"][:2] for l in frame["legs"].values() if l["contact"]])
    ax.add_patch(Polygon(support,color=GREEN,alpha=.13))
    ax.plot(*zip(*(support+support[:1])),color=GREEN,lw=1,ls="--")
    mounts=convex_hull([l["mount"] for l in engine.cfg["legs"]])
    ax.add_patch(Polygon(mounts,facecolor="#2a4263",edgecolor="#81a2ce"))
    for name,l in frame["legs"].items():
        color=GREEN if l["contact"] else AMBER
        chain=l["chain"]
        ax.plot([p[0] for p in chain],[p[1] for p in chain],"o-",color=color,lw=3,ms=3)
        ax.scatter([l["body"][0]],[l["body"][1]],s=75,color=color,zorder=10)
        ax.text(l["body"][0]+7,l["body"][1]+9,name,color=INK,fontsize=9)
        ax2.plot([p[0] for p in chain],[p[1] for p in chain],
                 [p[2]+engine.cfg["body_height"] for p in chain],"o-",color=color,lw=3,ms=3)
    ax.scatter([0],[0],color="#fb7185",s=40,zorder=20)
    ax.annotate("+Y forward",xy=(0,80),xytext=(25,0),color=INK,fontsize=8,
                arrowprops=dict(arrowstyle="->",color=INK))
    ax.set(xlim=(-285,285),ylim=(-285,285),xlabel="X (mm)",ylabel="Y (mm)")
    ax.set_aspect("equal");ax.grid(alpha=.10,color=INK)
    ax.xaxis.label.set_color(INK);ax.yaxis.label.set_color(INK)
    for sp in ax.spines.values():sp.set_color("#344963")
    ax2.set_title("3D KINEMATICS / LEVEL GROUND",loc="left",color=INK,fontsize=12,pad=14)
    bx,by=zip(*(mounts+mounts[:1]));ax2.plot(bx,by,[engine.cfg["shoulder_z"]+engine.cfg["body_height"]]*len(bx),color="#81a2ce",lw=2)
    ax2.set(xlim=(-280,280),ylim=(-280,280),zlim=(0,200),xlabel="X (mm)",ylabel="Y (mm)",zlabel="Z (mm)")
    ax2.set_box_aspect((1,1,.55));ax2.view_init(elev=24,azim=-55)
    for axis in [ax2.xaxis,ax2.yaxis,ax2.zaxis]:
        axis.label.set_color(INK)
        axis.pane.set_facecolor(PANEL)
        axis.pane.set_edgecolor("#344963")
        axis._axinfo["grid"]["color"]="#344963"
    fig.text(.055,.94,"HEXAPOD / MOTION LAB",color=INK,fontsize=22,weight="bold")
    fig.text(.055,.88,"54 / 45 / 77 mm   |   TRIPOD   |   vy = 1 (normalized), speed = 0.6",color="#9db3d1",fontsize=10)
    fig.text(.70,.92,f"t = {frame['t']:4.2f} s",color=GREEN,fontsize=20,weight="bold")
    fig.text(.055,.055,"GREEN: scheduled stance     AMBER: scheduled swing     PINK: assumed COM",color=INK,fontsize=10)
    fig.text(.055,.022,"Geometry simulation only. Servo calibration and physical validation are separate.",color="#91a6c4",fontsize=9)


def diagrams():
    out=ROOT/"examples";out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})
    cfg=load_config()
    # Coordinate diagram: top and one leg, light for printing.
    fig,(ax,side)=plt.subplots(1,2,figsize=(10,4.6),gridspec_kw={"width_ratios":[1.15,1]})
    e=GaitEngine(Command(0,0,0));f=e.frame()
    mounts=convex_hull([l["mount"] for l in cfg["legs"]])
    ax.add_patch(Polygon(mounts,facecolor="#e4edf8",edgecolor="#375b85"))
    for leg in cfg["legs"]:
        l=f["legs"][leg["name"]]
        # Plot forward up; left left, a physical top-view orientation.
        pts=l["chain"]
        ax.plot([p[0] for p in pts],[p[1] for p in pts],"o-",lw=2,color="#087c72")
        p=pts[-1];ax.text(p[0],p[1]+13,leg["name"],ha="center",weight="bold")
    ax.annotate("",xy=(0,80),xytext=(0,0),arrowprops=dict(arrowstyle="->",color="#9b3a69"))
    ax.text(9,82,"+Y",color="#9b3a69",fontsize=9)
    ax.annotate("",xy=(80,0),xytext=(0,0),arrowprops=dict(arrowstyle="->",color="#9b3a69"))
    ax.text(85,-16,"+X",color="#9b3a69",fontsize=9)
    ax.set_aspect("equal");ax.set_xlim(-290,290);ax.set_ylim(-260,280);ax.axis("off")
    ax.set_title("Body frame / leg names",weight="bold")
    q=f["legs"]["m"]["q"]
    chain=leg_chain(q,e.lengths)
    side.plot([p[0] for p in chain],[p[2] for p in chain],"o-",color="#087c72",lw=3)
    for i,(a,b,label) in enumerate(zip(chain,chain[1:],["L1 = 54","L2 = 45","L3 = 77"])):
        side.text((a[0]+b[0])/2+3,(a[2]+b[2])/2+8,label,color="#233c5a",fontsize=9)
    side.scatter([110],[-60],s=50,color="#bd6a1b");side.text(113,-65,"P(110, 0, -60)",fontsize=9)
    side.axhline(0,lw=.8,color="#abb9c9");side.axvline(0,lw=.8,color="#abb9c9")
    side.set(xlim=(-15,225),ylim=(-115,95),xlabel="Leg-local x (mm)",ylabel="Leg-local z (mm)")
    side.set_aspect("equal");side.grid(alpha=.15);side.set_title("One leg / neutral example",weight="bold")
    fig.tight_layout();fig.savefig(out/"coordinate_and_leg.png",dpi=180,bbox_inches="tight");plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(9,6.5),sharex=True)
    from shared.common.config_loader import ConfigLoader
    from shared.gait_core.gait_config import GaitConfig
    from shared.gait_core.gait_phase import GaitPhase
    from shared.common.enums import GaitType
    gcfg=GaitConfig.from_dict(ConfigLoader().load("gait_config"))
    names=[leg["name"] for leg in cfg["legs"]]
    for ax,gait in zip(axes,["tripod","wave","ripple"]):
        profile=gcfg.profiles[GaitType(gait)]
        phase=GaitPhase.from_profile(profile,names)
        for i,name in enumerate(names):
            for j in range(120):
                t=j/60
                swinging,_=phase.locate(t%1,i)
                ax.broken_barh([(t,1/60)],(i-.32,.64),facecolors="#e8a34a" if swinging else "#087c72")
        ax.set_yticks(range(6),names);ax.set_ylim(5.7,-.7)
        ax.set_title(gait.upper()+"  |  scheduled stance / swing",loc="left",fontsize=10,weight="bold")
        ax.set_xlim(0,2);ax.grid(axis="x",alpha=.15)
    axes[-1].set_xlabel("Normalized time t / T (two cycles)")
    fig.tight_layout();fig.savefig(out/"gait_phases.png",dpi=180,bbox_inches="tight");plt.close(fig)


if __name__=="__main__":
    diagrams()
    engine,data=frames()
    fig=plt.figure(figsize=(10.8,6.1),dpi=100)
    draw_frame(fig,data[10],engine)
    fig.savefig(ROOT/"examples"/"preview.png",dpi=160,facecolor=BG)
    animation=FuncAnimation(fig,lambda i:draw_frame(fig,data[i],engine),frames=len(data),interval=40)
    animation.save(ROOT/"examples"/"tripod_demo.gif",writer=PillowWriter(fps=25))
    plt.close(fig)
    print("Created examples/preview.png, tripod_demo.gif, coordinate_and_leg.png, gait_phases.png")
