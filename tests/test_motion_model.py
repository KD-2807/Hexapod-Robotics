"""Tính đúng hình học và hồi quy qua đường mô hình -> điều khiển -> CSV."""
import csv
import json
import math
from pathlib import Path
import random
import shutil
import tempfile
import unittest

from motion_model.motion import Command, GaitEngine, body_to_leg, fk, ik, leg_to_body, load_config, support_margin
from motion_model.export_motion import export
from shared.common.config_loader import ConfigLoader
from shared.common.enums import GaitType, RobotState
from shared.common.math_utils import Vec3
from shared.gait_core.trajectory import Trajectory
from shared.motion_core.factory import build_motion_controller
from shared.robot_core.leg_kinematics import LegKinematics
from simulation.sim_backend import SimBackend


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.cfg=load_config()
        self.lengths=(54.,45.,77.)

    def assertPoint(self,a,b):
        self.assertLess(math.dist(a,b),1e-8)

    def direct(self,command,gait,speed=.6):
        mc=build_motion_controller(SimBackend())
        mc.stand_up()
        for _ in range(500):
            if mc.state==RobotState.STANDING:break
            mc.update(.02)
        self.assertEqual(mc.state,RobotState.STANDING)
        mc.set_gait(GaitType(gait));mc.set_speed(speed)
        mc.move(command.vx,command.vy,command.wz,speed)
        return mc

    def test_canonical_dimensions_order_and_limits(self):
        self.assertEqual(tuple(self.cfg[k] for k in ('coxa','femur','tibia')),self.lengths)
        self.assertEqual([l['name'] for l in self.cfg['legs']],list('ijklmn'))
        self.assertEqual(self.cfg['joint_limits_deg'],[[-50,50],[-70,90],[-140,10]])
        self.assertFalse((Path(__file__).parents[1]/'motion_model/config.json').exists())

    def test_known_fk(self):
        self.assertPoint(fk((0,0,0),self.lengths),(176,0,0))
        self.assertPoint(fk((math.pi/2,0,0),self.lengths),(0,176,0))
        self.assertPoint(fk((0,math.pi/2,-math.pi/2),self.lengths),(131,0,45))

    def test_neutral_angles_and_fk(self):
        q=ik((110,0,-60),self.lengths,self.cfg['joint_limits_deg'])
        self.assertPoint(tuple(map(math.degrees,q)),(0,20.4807517124715,-100.12274734016066))
        self.assertPoint(fk(q,self.lengths),(110,0,-60))

    def test_random_fk_ik_uses_same_solver_as_controller(self):
        rng=random.Random(544577)
        solver=LegKinematics(*self.lengths)
        for _ in range(1000):
            p=(rng.uniform(90,125),rng.uniform(-20,20),rng.uniform(-70,-35))
            q=ik(p,self.lengths)
            self.assertPoint(fk(q,self.lengths),p)
            self.assertEqual(q,solver.inverse(Vec3(*p)).angles)

    def test_reject_invalid_ik(self):
        for p in [(1000,0,-60),(0,0,0),(110,0,math.nan),(54,0,0)]:
            with self.assertRaises(ValueError):ik(p,self.lengths)
        with self.assertRaises(ValueError):ik((110,0,-60),self.lengths,[(0,0)]*3)

    def test_transforms_match_controller_mounts_and_frames(self):
        e=GaitEngine(Command(0,0,0))
        for spec,leg in zip(self.cfg['legs'],e.controller.hexapod.legs):
            p=(110.,9.,-60.)
            body=leg_to_body(p,spec)
            b=leg.leg_to_body(Vec3(*p))
            self.assertPoint(body,(b.x,b.y,b.z))
            self.assertPoint(body_to_leg(body,spec),p)

    def test_command_units_and_finite(self):
        for args in [(30,0,0),(0,-2,0),(0,0,math.inf),(math.nan,0,0)]:
            with self.assertRaises(ValueError):Command(*args)
        for speed in [0,1.1,math.nan]:
            with self.assertRaises(ValueError):GaitEngine(speed=speed)

    def test_adapter_and_direct_controller_frames_identical(self):
        commands=[Command(0,1,0),Command(0,-1,0),Command(1,0,0),Command(-1,0,0),Command(0,0,.6),Command(.4,.7,.3)]
        for gait in ('tripod','wave','ripple'):
            for command in commands:
                e=GaitEngine(command,gait)
                mc=self.direct(command,gait)
                self.assertEqual(e.frame()['angles_deg'],mc.frame.angles)
                for _ in range(600):
                    f=e.step(.02);mc.update(.02)
                    self.assertEqual(f['angles_deg'],mc.frame.angles)
                    self.assertEqual(f['state'],mc.state.value)
                    self.assertNotEqual(mc.state,RobotState.ERROR)
                    self.assertGreater(f['support_margin'],0.,'COM gia dinh ngoai da giac theo lich pha')
                    self.assertEqual([l['contact'] for l in f['legs'].values()],mc.stance_phase_mask())

    def test_model_points_match_actual_applied_frame(self):
        e=GaitEngine(Command(.2,.8,.2))
        for _ in range(100):
            f=e.step(.02)
            self.assertEqual(f['angles_deg'],e.backend.last_frame.angles)
            for leg in e.controller.hexapod.legs:
                l=f['legs'][leg.id]
                q=tuple(math.radians(e.controller.frame.get(leg.index,j)) for j in range(3))
                self.assertPoint(fk(q,self.lengths),l['local'])
                p=leg.leg_to_body(Vec3(*l['local']))
                self.assertPoint(l['body'],(p.x,p.y,p.z))

    def test_zero_command_and_sample_clock(self):
        e=GaitEngine(Command(0,0,0));before=e.frame()['angles_deg']
        f=e.step(2.)
        self.assertEqual(f['state'],'STANDING')
        self.assertEqual(f['angles_deg'],before)
        self.assertEqual(sum(l['contact'] for l in f['legs'].values()),6)
        self.assertEqual(f['t'],2.)
        for dt in [-.02,.03,math.nan]:
            with self.assertRaises(ValueError):e.step(dt)

    def test_step_grouping_and_phase(self):
        for gait in ('tripod','wave','ripple'):
            a=GaitEngine(gait=gait);b=GaitEngine(gait=gait)
            fa=a.step(.4)
            for _ in range(20):fb=b.step(.02)
            self.assertEqual(fa['angles_deg'],fb['angles_deg'])
            self.assertEqual([l['contact'] for l in fa['legs'].values()],[l['contact'] for l in fb['legs'].values()])

    def test_csv_matches_controller_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run.csv'
            count,_=export(out,seconds=.4,vx=0,vy=1,gait='wave')
            self.assertEqual(count,21)
            with out.open() as stream:rows=list(csv.DictReader(stream))
            e=GaitEngine(Command(0,1,0),'wave')
            for index,row in enumerate(rows):
                f=e.frame() if index==0 else e.step(.02)
                values=[float(row[f'{name}_q{j}_deg']) for name in 'ijklmn' for j in (1,2,3)]
                self.assertEqual(values,e.controller.frame.angles)
                self.assertEqual(float(row['time_s']),f['t'])

    def test_alternate_config_changes_model_and_controller_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(ConfigLoader().directory)
            for p in src.glob('*.json'):shutil.copyfile(p,Path(tmp)/p.name)
            path=Path(tmp)/'robot_config.json';data=json.loads(path.read_text())
            data['link_lengths_mm']['coxa']=55.
            data['stance']['radius_mm']=111.
            path.write_text(json.dumps(data))
            e=GaitEngine(Command(0,0,0),config_dir=tmp)
            self.assertEqual(e.cfg['coxa'],55.)
            self.assertEqual(e.controller.hexapod.config.coxa,55.)
            for l in e.frame()['legs'].values():self.assertAlmostEqual(l['local'][0],111.)

    def test_shared_bezier_height_and_phase_endpoints(self):
        stride=Vec3(10,20,0)
        self.assertEqual(Trajectory.stance(1,stride),Trajectory.swing(0,stride,20))
        self.assertEqual(Trajectory.swing(1,stride,20),Trajectory.stance(0,stride))
        self.assertAlmostEqual(Trajectory.swing(.5,stride,20).z,20.)

    def test_support_polygon_sign(self):
        points=[(-1,-1),(1,-1),(1,1),(-1,1)]
        self.assertAlmostEqual(support_margin(points),1.)
        self.assertLess(support_margin(points,(2,0)),0.)

    def test_invalid_csv_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'run.csv';path.write_text('existing')
            with self.assertRaises(ValueError):export(path,dt=.03)
            self.assertEqual(path.read_text(),'existing')
            self.assertFalse(path.with_suffix('.csv.tmp').exists())


if __name__=='__main__':unittest.main()
