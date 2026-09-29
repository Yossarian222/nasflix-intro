"""NASFLIX intro v5 - builds the scene and the whole animation (24 fps, 420 frames).
Story (same as v4): bookcase -> they sit down (beer, popcorn) -> cheek kiss with hearts ->
camera moves over them to behind -> TV (the app shows a live clip in the screen quad)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from lib import *
import scene5, pose5
HERE = os.path.dirname(os.path.abspath(__file__))
R = math.radians
FPS = 24; END = 420
S1, S1B, S2, S3, S4, S5 = 1, 45, 85, 205, 301, 349

info, A, B, husky, pint, bowl = scene5.build()
sc = bpy.context.scene; sc.frame_start = 1; sc.frame_end = END; sc.render.fps = FPS
cy = info['couch_y']; st = info['seat_top']; NN = info['north']; TVZ = info['tvz']
TV = Vector((0, NN - 0.15, TVZ))


def upd():
    bpy.context.view_layer.update()


def M(*ds):
    r = {}
    for d in ds: r.update(d)
    return r


# ------------------------------------------------------------------ poses (armature space, character faces -Y)
REL_L = {'upperarm_l': (0.13, 0.02, -1), 'lowerarm_l': (0.06, -0.12, -1), 'hand_l': (0.03, -0.14, -1)}
REL_R = {'upperarm_r': (-0.13, 0.02, -1), 'lowerarm_r': (-0.06, -0.12, -1), 'hand_r': (-0.03, -0.14, -1)}
A_HOLD_STAND = {'upperarm_r': (-0.1, 0.06, -1), 'lowerarm_r': (-0.04, -1, 0.3), 'hand_r': (-0.02, -1, 0.25)}
A_HOLD = scene5.ARMS_A_HOLD
A_SIP = {'upperarm_r': (-0.32, -0.55, -0.45), 'lowerarm_r': (0.42, -0.35, 0.85), 'hand_r': (0.2, -0.25, 1)}
A_AROUND = {'upperarm_l': (0.7, 0.35, -0.05), 'lowerarm_l': (0.55, 0.3, -0.55), 'hand_l': (0.25, 0.1, -1)}
B_BOWL_STAND = {'upperarm_l': (0.1, -0.12, -1), 'lowerarm_l': (-0.35, -1, 0.18), 'hand_l': (-0.5, -1, 0.05),
                'upperarm_r': (-0.1, -0.12, -1), 'lowerarm_r': (0.35, -1, 0.18), 'hand_r': (0.5, -1, 0.05)}
B_BOWL = scene5.ARMS_B_BOWL
B_EAT = {'upperarm_r': (-0.3, -0.55, -0.55), 'lowerarm_r': (0.38, -0.32, 1), 'hand_r': (0.2, -0.25, 1)}
STAND = dict(neck_01=(0, -0.08, 1), head=(0, -0.02, 1))
MID = dict(pelvis=(0, -0.15, 1), spine_01=(0, -0.2, 1), spine_02=(0, -0.12, 1), spine_03=(0, -0.05, 1),
           neck_01=(0, -0.12, 1), head=(0, -0.02, 1))
SEAT = scene5.SEAT


def root_seat(P):
    return scene5.seat_root(P, st)


def root_stand():
    return (0, -0.5, 0.0)


def root_mid(P):
    s = root_seat(P)
    return (0, -0.2, s[2] * 0.55)


FEET_STAND = (0.17, -0.52, 0.08)
FEET_SEAT = (0.15, -0.44, 0.085)


def P_(C, dirs, root, frame, feet, curls, post=None):
    pose5.pose(C.rig, dirs, root=root, curls=curls)
    fx, fy, fz = feet
    for side, sx in (('l', 1), ('r', -1)):
        pose5.leg_ik(C.rig, side, Vector((sx * fx, fy, fz)), pole=Vector((0, -1, 0.45)))
        pose5.set_dir(C.rig.pose.bones['foot_' + side], (0, -1, -0.5 if fz > 0.06 else -0.3)); upd()
    if post: post(C)
    pose5.key(C.rig, frame)


def sip(C):
    rg = C.rig
    m = pose5.mouth(rg)
    pose5.arm_ik(rg, 'r', m + Vector((-0.075, -0.07, -0.12)), pole=Vector((-1, 0.2, -0.7)))
    pose5.set_dir(rg.pose.bones['hand_r'], (0.25, -0.6, 0.75)); upd()


def eat(C):
    rg = C.rig
    m = pose5.mouth(rg)
    pose5.arm_ik(rg, 'r', m + Vector((0.02, -0.04, -0.085)), pole=Vector((-1, 0.1, -0.8)))
    pose5.set_dir(rg.pose.bones['hand_r'], (0.25, -0.3, 1)); upd()


CA = {'r': 70, 'l': 18}
CB = {'l': 30, 'r': 30}

# ---------------- him
r = A.rig
P_(A, M(STAND, REL_L, A_HOLD_STAND), root_stand(), 1, FEET_STAND, CA)
P_(A, M(STAND, REL_L, A_HOLD_STAND, dict(neck_01=(0.08, -0.08, 1), head=(0.12, -0.02, 1))), root_stand(), 40, FEET_STAND, CA)
P_(A, M(STAND, REL_L, A_HOLD_STAND, dict(head=(0.05, -0.04, 1))), root_stand(), 96, FEET_STAND, CA)
P_(A, M(MID, REL_L, A_HOLD_STAND), root_mid(A), 112, ((FEET_STAND[0] + FEET_SEAT[0]) / 2, -0.48, 0.082), CA)
P_(A, M(SEAT, A_HOLD, dict(spine_01=(0, 0.25, 1))), (0, 0.06, root_seat(A)[2] + 0.02), 126, FEET_SEAT, CA)
P_(A, M(SEAT, A_HOLD), root_seat(A), 136, FEET_SEAT, CA)
P_(A, M(SEAT, A_HOLD), root_seat(A), 148, FEET_SEAT, CA)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0, -0.1, 1), head=(0, 0.1, 1))), root_seat(A), 162, FEET_SEAT, CA, post=sip)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0, -0.08, 1), head=(0, 0.14, 1))), root_seat(A), 172, FEET_SEAT, CA, post=sip)
P_(A, M(SEAT, A_HOLD), root_seat(A), 188, FEET_SEAT, CA)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0.12, -0.2, 1), head=((0.16, -0.05, 1), 42))), root_seat(A), 202, FEET_SEAT, CA)
KA = M(SEAT, A_HOLD, dict(spine_02=(0.1, 0.22, 1), spine_03=(0.32, 0.06, 1), neck_01=(0.55, -0.12, 1)))
P_(A, M(SEAT, A_HOLD, dict(spine_03=(0.12, 0.08, 1), neck_01=(0.25, -0.15, 1))), root_seat(A), 222, FEET_SEAT, CA)
P_(A, KA, root_seat(A), 246, FEET_SEAT, CA)
P_(A, KA, root_seat(A), 280, FEET_SEAT, CA)
P_(A, M(SEAT, A_HOLD, dict(spine_03=(0.14, 0.08, 1), neck_01=(0.25, -0.15, 1))), root_seat(A), 298, FEET_SEAT, CA)
AR = M(SEAT, A_HOLD, A_AROUND, dict(spine_03=(0.08, 0.12, 1), neck_01=(0.08, -0.18, 1), head=(0.08, -0.03, 1)))
P_(A, AR, root_seat(A), 336, FEET_SEAT, CA)
P_(A, M(AR, dict(head=(0.12, -0.03, 1))), root_seat(A), 392, FEET_SEAT, CA)
P_(A, M(AR, dict(head=(0.1, -0.05, 1))), root_seat(A), 420, FEET_SEAT, CA)

# ---------------- her
l = B.rig
P_(B, M(STAND, B_BOWL_STAND), root_stand(), 1, FEET_STAND, CB)
P_(B, M(STAND, B_BOWL_STAND, dict(neck_01=(-0.1, -0.08, 1), head=(-0.14, -0.02, 1))), root_stand(), 46, FEET_STAND, CB)
P_(B, M(STAND, B_BOWL_STAND, dict(head=(-0.05, -0.03, 1))), root_stand(), 90, FEET_STAND, CB)
P_(B, M(MID, B_BOWL_STAND), root_mid(B), 106, ((FEET_STAND[0] + FEET_SEAT[0]) / 2, -0.48, 0.082), CB)
P_(B, M(SEAT, B_BOWL, dict(spine_01=(0, 0.25, 1))), (0, 0.06, root_seat(B)[2] + 0.02), 120, FEET_SEAT, CB)
P_(B, M(SEAT, B_BOWL), root_seat(B), 130, FEET_SEAT, CB)
P_(B, M(SEAT, B_BOWL), root_seat(B), 150, FEET_SEAT, CB)
P_(B, M(SEAT, B_BOWL, dict(head=(0.02, -0.1, 1))), root_seat(B), 164, FEET_SEAT, CB, post=eat)
P_(B, M(SEAT, B_BOWL, dict(head=(0.04, -0.12, 1))), root_seat(B), 172, FEET_SEAT, CB, post=eat)
P_(B, M(SEAT, B_BOWL, dict(neck_01=(-0.12, -0.2, 1), head=((-0.16, -0.05, 1), -36))), root_seat(B), 192, FEET_SEAT, CB)
KB = M(SEAT, B_BOWL, dict(spine_02=(-0.08, 0.2, 1), spine_03=(-0.28, 0.06, 1), neck_01=(-0.48, -0.1, 1)))
P_(B, M(SEAT, B_BOWL, dict(spine_03=(-0.1, 0.08, 1), neck_01=(-0.2, -0.15, 1))), root_seat(B), 220, FEET_SEAT, CB)
P_(B, KB, root_seat(B), 244, FEET_SEAT, CB)
P_(B, KB, root_seat(B), 282, FEET_SEAT, CB)
P_(B, M(SEAT, B_BOWL, dict(spine_03=(-0.12, 0.08, 1), neck_01=(-0.2, -0.12, 1))), root_seat(B), 300, FEET_SEAT, CB)
HB = M(SEAT, B_BOWL, dict(spine_02=(-0.2, 0.22, 1), spine_03=(-0.44, 0.1, 1), neck_01=(-0.66, 0.02, 1), head=(-0.55, 0.08, 1)))
P_(B, HB, root_seat(B), 346, FEET_SEAT, CB)
P_(B, M(HB, dict(head=(-0.55, 0.05, 1))), root_seat(B), 392, FEET_SEAT, CB)
P_(B, HB, root_seat(B), 420, FEET_SEAT, CB)


# ---------------- kiss: aim the heads at each other on top of the base poses
def kiss_heads(f, amount):
    sc.frame_set(f)
    fwd = Vector((0, 1, 0))                      # both face +Y (towards the TV / camera)
    hb = l.matrix_world @ l.pose.bones['head'].head
    hb_c = hb + Vector((0, 0, 0.09))
    cheek = hb_c + fwd * 0.06 + Vector((0.055, 0, -0.035))
    pose5.aim_head(r, cheek, blend=amount)
    pose5.aim_head(l, hb_c + fwd * 1.0 + Vector((0.3, 0, -0.05)), blend=amount * 0.6)
    pose5.roll_head(r, 9 * amount)
    pose5.roll_head(l, -15 * amount)
    for rg in (r, l):
        rg.pose.bones['head'].keyframe_insert('rotation_quaternion', frame=f)
for f, a in ((222, 0.35), (246, 1.0), (280, 1.0), (298, 0.25)):
    kiss_heads(f, a)
for C in (A, B):
    pose5.smooth(C.rig)


# ---------------- faces: gaze, blinks, smiles, closed eyes, blush
def look(C, f, target):
    C.look.location = target; C.look.keyframe_insert('location', frame=f)


def sk(C, name, f, v):
    kb = C.body.data.shape_keys.key_blocks[name]; kb.value = v; kb.keyframe_insert('value', frame=f)


def blink(C, f):
    for side in ('l', 'r'):
        for ff, v in ((f - 1, 0.0), (f + 1, 1.0), (f + 3, 0.0)):
            sk(C, 'blink_' + side, ff, v)


def eyes_closed(C, f0, f1):
    for side in ('l', 'r'):
        for ff, v in ((f0 - 3, 0.0), (f0, 1.0), (f1, 1.0), (f1 + 4, 0.0)):
            sk(C, 'blink_' + side, ff, v)


ha0 = r.matrix_world @ r.pose.bones['head'].head
hb0 = l.matrix_world @ l.pose.bones['head'].head
look(A, 1, Vector((0.3, 0.5, 1.4))); look(B, 1, Vector((-0.2, 0.6, 1.3)))
look(A, 36, hb0 + Vector((0, 0.1, 0))); look(B, 42, ha0 + Vector((0, 0.1, 0)))      # glance at each other
look(A, 70, Vector((0.2, 0.8, 0.6))); look(B, 76, Vector((-0.2, 0.8, 0.6)))
look(A, 140, TV); look(B, 136, TV)
look(A, 196, Vector((-0.4, cy + 0.1, 1.15))); look(B, 190, Vector((0.4, cy + 0.1, 1.2)))
look(A, 300, TV); look(B, 300, TV); look(A, 420, TV); look(B, 420, TV)
for f in (28, 118, 188, 330, 396): blink(A, f)
for f in (20, 100, 178, 360, 406): blink(B, f)
for C in (A, B): eyes_closed(C, 250, 282)
for C, base, kiss in ((A, 0.35, 0.65), (B, 0.8, 1.0)):
    for f, v in ((1, base), (200, base), (230, kiss), (300, kiss), (340, base + 0.1), (420, base + 0.1)):
        sk(C, 'smile', f, v)
    for f, v in ((1, 0.1 if C is A else 0.3), (420, 0.1 if C is A else 0.3)):
        sk(C, 'smile_up', f, v)
bl = B.skin_mat.node_tree.nodes['BlushAmt'].outputs[0]
for f, v in ((1, 0.6), (228, 0.6), (262, 0.95), (340, 0.9), (420, 0.8)):
    bl.default_value = v; bl.keyframe_insert('default_value', frame=f)

# ---------------- props
upd(); sc.frame_set(1)
pbh = r.pose.bones['hand_r']
w = r.matrix_world @ pbh.head; t = r.matrix_world @ pbh.tail; hd = (t - w).normalized()
side = (r.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()     # his left, towards the palm of the right hand
grip = w + hd * 0.055 + side * 0.03
pint.matrix_world = Matrix.Translation(grip - Vector((0, 0, 0.055)))
scene5.attach(pint, r, 'hand_r', pint.matrix_world.copy())
bowl.rotation_mode = 'XYZ'
for f in range(1, END + 1):
    sc.frame_set(f)
    bw_ = l.matrix_world
    hl = bw_ @ l.pose.bones['hand_l'].tail; hr = bw_ @ l.pose.bones['hand_r'].tail
    hips = (bw_ @ l.pose.bones['thigh_l'].head + bw_ @ l.pose.bones['thigh_r'].head) / 2
    knees = (bw_ @ l.pose.bones['thigh_l'].tail + bw_ @ l.pose.bones['thigh_r'].tail) / 2
    lap = hips.lerp(knees, 0.5) + Vector((0, 0, 0.065))
    held = (hl + hr) / 2 + Vector((0, 0, -0.055))
    seated = max(0.0, min(1.0, (f - 108) / 16.0))
    eating = 1.0 if 152 <= f <= 186 else 0.0
    if eating:
        held = hl + Vector((0.06, 0, -0.05))
    pos = held.lerp(lap, seated * 0.85)
    bowl.location = pos
    bowl.rotation_euler = (0, 0, l.matrix_world.to_euler().z)
    bowl.keyframe_insert('location', frame=f); bowl.keyframe_insert('rotation_euler', frame=f)
piece = sphere('pc_hand', 0.011, bpy.data.materials['pop1'], loc=(0, 0, -5), seg=10)
for f in range(1, END + 1):
    sc.frame_set(f)
    if 154 <= f <= 170:
        piece.location = l.matrix_world @ l.pose.bones['hand_r'].tail + Vector((0, 0, 0.012))
    else:
        piece.location = (0, 0, -5)
    piece.keyframe_insert('location', frame=f)

# ---------------- hearts above the kiss
import bmesh


def heart_mesh(name, mat, size):
    pts = []
    for i in range(48):
        tt = i / 48 * 2 * math.pi
        x = 16 * math.sin(tt) ** 3; y = 13 * math.cos(tt) - 5 * math.cos(2 * tt) - 2 * math.cos(3 * tt) - math.cos(4 * tt)
        pts.append((x / 17 * size, 0, y / 17 * size))
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]; bm.faces.new(vs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob)
    so = ob.modifiers.new('s', 'SOLIDIFY'); so.thickness = size * 0.45; so.offset = 0
    bv = ob.modifiers.new('b', 'BEVEL'); bv.width = size * 0.2; bv.segments = 4; bv.limit_method = 'NONE'
    sd = ob.modifiers.new('sd', 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
    for pgn in me.polygons: pgn.use_smooth = True
    me.materials.append(mat); return ob


hm = [bead('heart_red', '#d8303d', speck_color='#ff8a92', speck=0.2, bead=0.004),
      bead('heart_pink', '#ee8a98', speck_color='#ffd6dc', speck=0.25, bead=0.004)]
sc.frame_set(264)
kc = ((r.matrix_world @ r.pose.bones['head'].tail) + (l.matrix_world @ l.pose.bones['head'].tail)) / 2
rh = random.Random(9)
for k in range(6):
    h = heart_mesh(f'heart{k}', hm[k % 2], rh.uniform(0.03, 0.05))
    base = kc + Vector((rh.uniform(-0.22, 0.22), rh.uniform(-0.05, 0.12), 0.06 + rh.uniform(0, 0.08)))
    f0 = 254 + k * 6
    h.rotation_euler = (0, rh.uniform(-0.3, 0.3), 0)
    h.scale = (0.001,) * 3; h.location = base
    h.keyframe_insert('scale', frame=f0 - 1); h.keyframe_insert('location', frame=f0 - 1)
    h.scale = (1.15,) * 3; h.keyframe_insert('scale', frame=f0 + 4)
    h.scale = (1,) * 3; h.keyframe_insert('scale', frame=f0 + 8)
    h.location = base + Vector((rh.uniform(-0.04, 0.04), 0, 0.16)); h.rotation_euler = (0, rh.uniform(-0.4, 0.4), 0)
    h.keyframe_insert('location', frame=S4 - 2); h.keyframe_insert('rotation_euler', frame=S4 - 2); h.keyframe_insert('scale', frame=S4 - 5)
    h.scale = (0.001,) * 3; h.keyframe_insert('scale', frame=S4 - 1)

# ---------------- husky: looks around, tilts its head during the kiss
hr_ = bpy.data.objects[husky['rig']]
hb = hr_.pose.bones['head']
for f, rot in ((1, (0, 0, 0)), (40, (0, 0, R(18))), (90, (0, 0, R(-10))), (140, (R(-6), 0, R(-25))),
               (210, (R(-4), 0, R(-35))), (250, (R(-4), R(16), R(-38))), (290, (R(-4), R(18), R(-36))),
               (330, (R(4), 0, R(-8))), (420, (R(6), 0, R(-4)))):
    hb.rotation_euler = rot; hb.keyframe_insert('rotation_euler', frame=f)
pose5.smooth(hr_)

# ---------------- robot vacuum, candle, TV
rv = info['robovac']
for f, (x, y, a) in ((1, (-1.4, 0.95, R(10))), (84, (0.9, 1.35, R(20))), (200, (2.0, 1.9, R(40))), (349, (-0.9, -0.2, R(200))),
                     (420, (0.4, 0.45, R(208)))):
    rv.location = (x, y, 0); rv.rotation_euler = (0, 0, a); rv.keyframe_insert('location', frame=f); rv.keyframe_insert('rotation_euler', frame=f)
rnd = random.Random(3)
cl = info['candle'].data
for f in range(1, END + 1, 3):
    cl.energy = 5 * rnd.uniform(0.8, 1.15); cl.keyframe_insert('energy', frame=f)
scr = info['tv_screen']; E = scr.data.materials[0].node_tree.nodes['E']
for f, v in ((1, 0.0), (304, 0.0), (312, 1.6)):
    E.inputs['Strength'].default_value = v; E.inputs['Strength'].keyframe_insert('default_value', frame=f)
tvl = info['tv_light']
for f in range(1, END + 1, 6):
    tvl.data.energy = 0 if f < 304 else rnd.uniform(40, 75); tvl.data.keyframe_insert('energy', frame=f)


# ---------------- cameras
def cam(name, keys, lens, fstop, focus_keys):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
    c = bpy.data.objects.new(name, cd); link(c)
    tgt = bpy.data.objects.new(name + '_t', None); link(tgt)
    tc = c.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    foc = bpy.data.objects.new(name + '_f', None); link(foc)
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop; cd.dof.focus_object = foc; cd.dof.aperture_blades = 7
    for f, loc, t in keys:
        c.location = loc; c.keyframe_insert('location', frame=f); tgt.location = t; tgt.keyframe_insert('location', frame=f)
    for f, p in focus_keys:
        foc.location = p; foc.keyframe_insert('location', frame=f)
    for ob in (c, tgt, foc):
        pose5.smooth(ob)
    return c


mid = Vector(((scene5.AX + scene5.BX) / 2, cy, 1.18))
c1 = cam('Cam1', [(S1, (-1.2, 2.12, 1.14), (-1.86, 2.95, 1.0)), (S1B - 1, (-1.02, 1.98, 1.2), (-1.8, 2.95, 1.06))], 40, 0.5,
         [(S1, (-1.8, 2.86, 1.02)), (S1B - 1, (-1.78, 2.86, 1.06))])
c1b = cam('Cam1b', [(S1B, (-1.55, 1.25, 1.42), (0.12, cy + 0.45, 1.05)), (S2 - 1, (-1.4, 1.05, 1.38), (0.12, cy + 0.45, 1.02))], 32, 0.7,
          [(S1B, (0.0, cy + 0.52, 1.2)), (S2 - 1, (0.0, cy + 0.5, 1.15))])
c2 = cam('Cam2', [(S2, (0.2, 1.55, 1.34), (0, cy + 0.2, 1.1)), (100, (0.2, 1.45, 1.3), (0, cy + 0.15, 1.05)),
                  (136, (0.18, 1.1, 1.1), (0, cy, 0.9)), (S3 - 1, (0.16, 0.95, 1.05), (0, cy, 0.88))], 36, 0.55,
         [(S2, (0, cy + 0.5, 1.3)), (100, (0, cy + 0.45, 1.25)), (136, (0, cy + 0.06, 1.05)), (S3 - 1, (0, cy + 0.06, 1.02))])
c3 = cam('Cam3', [(S3, (mid.x - 0.02, cy + 1.45, 1.26), mid + Vector((0, 0, 0.0))), (S4 - 1, (mid.x - 0.06, cy + 1.25, 1.28), mid + Vector((0, 0, 0.02)))],
         55, 0.9, [(S3, mid + Vector((0, 0.1, 0))), (S4 - 1, mid + Vector((0, 0.1, 0.02)))])
FINAL = ((0.05, cy - 1.12, 1.66), (0, NN, TVZ - 0.42))
crane = []
for i, f in enumerate(range(S4, S5 + 1, 3)):
    tt = (f - S4) / (S5 - S4); e = tt * tt * (3 - 2 * tt)
    ang = R(8) + e * R(172)                       # in front -> over the heads -> behind
    rad = 1.3
    pos = Vector((0.12 * (1 - e) + 0.05 * e + 0.3 * math.sin(math.pi * e), cy + math.cos(ang) * rad, 1.3 + 0.55 * math.sin(math.pi * e) + (1.66 - 1.3) * e))
    k = max(0.0, min(1.0, (e - 0.55) / 0.45)); k = k * k * (3 - 2 * k)
    look_t = mid.lerp(Vector((0, NN, TVZ - 0.42)), k)
    crane.append((f, tuple(pos), tuple(look_t)))
crane[-1] = (S5, FINAL[0], FINAL[1])
c4 = cam('Cam4', crane, 30, 1.2, [(S4, mid + Vector((0, 0.1, 0))), (S4 + 30, mid), (S5, (0, NN, TVZ))])
c5 = cam('Cam5', [(S5, FINAL[0], FINAL[1]), (END, FINAL[0], FINAL[1])], 30, 2.8, [(S5, (0, NN, TVZ)), (END, (0, NN, TVZ))])
for f, c in ((S1, c1), (S1B, c1b), (S2, c2), (S3, c3), (S4, c4), (S5, c5)):
    m = sc.timeline_markers.new(c.name, frame=f); m.camera = c
sc.camera = c1

# ---------------- TV quad for the app overlay (normalised, top-left origin)
from bpy_extras.object_utils import world_to_camera_view


def tv_quad():
    sc.frame_set(S5 + 2); sc.camera = c5
    w, h = info['tvw'], info['tvh']
    corners = [Vector((sx * w / 2, NN - 0.148, TVZ + sy * h / 2)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    pts = []
    for p in corners:
        v = world_to_camera_view(sc, c5, p); pts.append((round(v.x, 5), round(1 - v.y, 5)))
    pts.sort(key=lambda q: (q[1], q[0]))
    top = sorted(pts[:2]); bot = sorted(pts[2:])
    return dict(tl=top[0], tr=top[1], br=bot[1], bl=bot[0], start=round((S5 - 1) / FPS + 0.15, 3), end=END / FPS)


Q = tv_quad(); os.makedirs(f'{HERE}/out', exist_ok=True)
json.dump(Q, open(f'{HERE}/out/tv_quad.json', 'w'), indent=1); print('TVQUAD', Q)
sc.frame_set(1)
sc.render.use_motion_blur = False
