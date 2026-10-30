"""Mo phong 2D Tkinter: chay python -m motion_model.simulator, khong can thu vien pip.

Moi lan bam Chay lai tao mot demo voi lenh khong doi. Day la trinh xem
loi dieu khien chung. Lenh vx/vy/wz chuan hoa; speed mac dinh 0.6.
"""
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from .motion import GaitEngine, Command, load_config, convex_hull
from .export_motion import export

BG="#101a2b"
INK="#dce7f4"
GROUND="#48d3b3"
SWING="#ffbf69"


class Simulator:
    def __init__(self,root):
        self.root=root
        root.title("Hexapod | Mo hinh toan & thuat toan chuyen dong")
        root.geometry("1160x790")
        root.minsize(1000,700)
        self.cfg=load_config()
        panel=ttk.Frame(root,padding=12)
        panel.pack(fill="x")
        ttk.Label(panel,text="HEXAPOD / MÔ PHỎNG THUẬT TOÁN",font=("Segoe UI",15,"bold")).grid(row=0,column=0,columnspan=10,sticky="w",pady=(0,12))
        self.gait=tk.StringVar(value="tripod")
        ttk.Label(panel,text="Dáng đi").grid(row=1,column=0,padx=4)
        ttk.Combobox(panel,textvariable=self.gait,values=["tripod","wave","ripple"],state="readonly",width=9).grid(row=1,column=1)
        self.values=[]
        for i,(label,default) in enumerate([("vx [-1,1]","0"),("vy [-1,1]","1"),("wz [-1,1]","0")]):
            ttk.Label(panel,text=label).grid(row=1,column=2+i*2,padx=(12,4))
            var=tk.StringVar(value=default)
            ttk.Entry(panel,textvariable=var,width=8).grid(row=1,column=3+i*2)
            self.values.append(var)
        ttk.Button(panel,text="Chạy lại",command=self.restart).grid(row=1,column=8,padx=12)
        self.pause_button=ttk.Button(panel,text="Tạm dừng",command=self.pause)
        self.pause_button.grid(row=1,column=9)
        ttk.Button(panel,text="Xuất CSV 8 giây",command=self.save).grid(row=1,column=10,padx=8)
        ttk.Label(panel,text="54 / 45 / 77 mm   |   +vx: sang phải   |   +vy: tiến   |   +wz: quay CCW   •   Thay thông số rồi bấm Chạy lại.").grid(row=2,column=0,columnspan=11,sticky="w",pady=(10,0))
        self.canvas=tk.Canvas(root,bg=BG,highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        self.status=tk.StringVar()
        ttk.Label(root,textvariable=self.status,padding=8).pack(fill="x")
        self.paused=False
        self.engine=None
        self.restart()
        self.tick()

    def restart(self):
        try:
            command=Command(*(float(v.get()) for v in self.values))
            # Kiem tra truoc 3 chu ky, tranh bat dau demo loi ngay sau do.
            probe=GaitEngine(command,gait=self.gait.get())
            for _ in range(math.ceil(3*self.cfg["period"]/.02)):
                probe.step(.02)
            self.engine=GaitEngine(command,gait=self.gait.get())
        except (ValueError,OverflowError) as exc:
            messagebox.showerror("Thông số chưa hợp lệ",str(exc))
            return
        self.paused=False
        self.pause_button.config(text="Tạm dừng")
        self.draw(self.engine.frame())

    def pause(self):
        self.paused=not self.paused
        self.pause_button.config(text="Tiếp tục" if self.paused else "Tạm dừng")

    def save(self):
        if self.engine is None:return
        try:
            c=self.engine.command
            path=Path(__file__).parent/"output"/"motion.csv"
            count,margin=export(path,8.,.02,c.vx,c.vy,c.wz,self.engine.gait)
            messagebox.showinfo("Đã xuất",f"{count} mẫu, 18 góc mỗi mẫu.\n{path}\nBiên chống nhỏ nhất: {margin:.2f} mm")
        except (OSError,ValueError) as exc:
            messagebox.showerror("Chưa xuất được",str(exc))

    def tick(self):
        if self.engine and not self.paused:
            try:self.draw(self.engine.step(.02))
            except ValueError as exc:
                self.paused=True
                self.status.set("DỪNG MÔ PHỎNG: "+str(exc))
        self.root.after(20,self.tick)

    def draw(self,frame):
        c=self.canvas
        c.delete("all")
        width=max(c.winfo_width(),1000)
        height=max(c.winfo_height(),490)
        left=width*.39
        cy=height*.49
        scale=min((width*.61-50)/650,(height-130)/650)
        def top(p):return (left+p[0]*scale,cy-p[1]*scale)
        def text(x,y,s,**kw):c.create_text(x,y,text=s,fill=INK,font=("Segoe UI",11),**kw)
        text(25,28,"NHÌN TỪ TRÊN • TỌA ĐỘ THEO THÂN",anchor="w")
        contacts=[l["body"][:2] for l in frame["legs"].values() if l["contact"]]
        hull=convex_hull(contacts)
        if len(hull)>=3:
            coords=[v for p in hull for v in top(p)]
            c.create_polygon(*coords,fill="#153c43",outline=GROUND,dash=(4,4))
                # Lay toa do tu config de hinh than theo thay doi cua nhom.
        mounts=[tuple(l["mount"]) for l in self.cfg["legs"]]
        hull_body=convex_hull(mounts)
        c.create_polygon(*[v for p in hull_body for v in top(p)],fill="#243a58",outline="#6f90b9",width=2)
        x0,y0=top((0,0));x1,y1=top((0,65))
        c.create_line(x0,y0,x1,y1,fill="#aabfff",width=2,arrow="last")
        text(x1+12,y1,"+Y tiến")
        c.create_oval(x0-5,y0-5,x0+5,y0+5,fill="#fb7185",outline="")
        for name,leg in frame["legs"].items():
            color=GROUND if leg["contact"] else SWING
            pts=[top(p) for p in leg["chain"]]
            c.create_line(*[v for p in pts for v in p],fill=color,width=5)
            for x,y in pts:c.create_oval(x-3,y-3,x+3,y+3,fill=INK,outline="")
            x,y=pts[-1]
            c.create_oval(x-7,y-7,x+7,y+7,fill=color,outline=BG,width=2)
            text(x+13,y-12,name,anchor="w")
        text(25,height-53,"● Xanh: lịch chống    ● Cam: lịch vung    ● Hồng: COM giả định",anchor="w")
        text(25,height-28,"Đa giác theo lịch pha; chưa mô phỏng lực tiếp xúc hoặc đo trượt chân.",anchor="w")
        tx=width*.70
        text(tx,28,f"{self.engine.gait.upper()} / {frame['state']} / t={frame['t']:.2f}s",anchor="w")
        text(tx,62,"GÓC KHỚP TOÁN HỌC (độ)",anchor="w")
        text(tx,91,"Chân       q1          q2          q3",anchor="w")
        for i,(name,leg) in enumerate(frame["legs"].items()):
            q=[math.degrees(v) for v in leg["q"]]
            c.create_text(tx,122+i*29,text=f"{name:2s}   {q[0]:7.2f}   {q[1]:7.2f}   {q[2]:7.2f}",anchor="w",fill=GROUND if leg["contact"] else SWING,font=("Consolas",11))
        text(tx,327,"NHÌN NGANG • CHÂN m (TRƯỚC TRÁI)",anchor="w")
        ground_y=height-80
        origin_x=tx+90
        side_scale=min(1.0,(height-390)/200)
        c.create_line(tx,ground_y,width-25,ground_y,fill="#6f90b9",dash=(4,4))
        chain=frame["legs"]["m"]["chain"]
        # Hinh chieu XZ trong he chan, khong phai XZ cua than.
        from .motion import leg_chain
        chain=leg_chain(frame["legs"]["m"]["q"],self.engine.lengths)
        pts=[(origin_x+p[0]*side_scale,ground_y-(p[2]+self.cfg["body_height"]+self.cfg["shoulder_z"])*side_scale) for p in chain]
        c.create_line(*[v for p in pts for v in p],fill=SWING,width=5)
        for x,y in pts:c.create_oval(x-4,y-4,x+4,y+4,fill=INK,outline="")
        margin=frame["support_margin"]
        count=sum(l["contact"] for l in frame["legs"].values())
        self.status.set(f"Chân chống: {count}/6  |  Biên theo lịch pha (COM giả định): {margin:.2f} mm  |  Mô phỏng hình học; chưa kiểm tra tải trọng, va chạm và hiệu chỉnh servo.")


if __name__=="__main__":
    root=tk.Tk()
    Simulator(root)
    root.mainloop()
