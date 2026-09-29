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
REL_L = {'upperarm_l': (0.12, 0.03, -1), 'lowerarm_l': (0.05, -0.16, -1), 'hand_l': (0.02, -0.2, -1)}
A_HOLD_STAND = {'upperarm_r': (-0.1, 0.06, -1), 'lowerarm_r': (-0.04, -1, 0.3), 'hand_r': (-0.02, -1, 0.25)}
A_TOAST = {'upperarm_r': (-0.18, -0.3, -1), 'lowerarm_r': (-0.06, -1, 0.8), 'hand_r': (-0.04, -1, 0.65)}
A_HOLD = scene5.ARMS_A_HOLD
A_REACH = {'upperarm_l': (0.32, 0.5, -1), 'lowerarm_l': (0.12, 0.4, -1), 'hand_l': (0.05, 0.25, -1)}
A_AROUND = {'upperarm_l': (0.7, 0.35, -0.05), 'lowerarm_l': (0.55, 0.3, -0.55), 'hand_l': (0.25, 0.1, -1)}
B_BOWL_STAND = {'upperarm_l': (0.1, -0.12, -1), 'lowerarm_l': (-0.35, -1, 0.18), 'hand_l': (-0.5, -1, 0.05),
                'upperarm_r': (-0.1, -0.12, -1), 'lowerarm_r': (0.35, -1, 0.18), 'hand_r': (0.5, -1, 0.05)}
B_OFFER = {'upperarm_l': (0.05, -0.35, -1), 'lowerarm_l': (-0.45, -1, 0.3), 'hand_l': (-0.55, -1, 0.15),
           'upperarm_r': (-0.2, -0.3, -1), 'lowerarm_r': (0.2, -1, 0.35), 'hand_r': (0.4, -1, 0.2)}
B_BOWL = scene5.ARMS_B_BOWL
SEAT = scene5.SEAT
UP = dict(neck_01=(0, -0.08, 1), head=(0, -0.02, 1))


def turn(sp, nk, hd, tilt=0.0, nod=0.0):
    """Upper body turned by absolute yaw angles (deg, + = to the character's left)."""
    return dict(spine_02=((0, 0.02, 1), sp * 0.5), spine_03=((0, 0.0, 1), sp),
                neck_01=((tilt * 0.3, -0.08 - nod * 0.3, 1), nk), head=((tilt, -0.02 - nod, 1), hd))


MID1 = dict(pelvis=(0, -0.35, 1), spine_01=(0, -0.3, 1), spine_02=(0, -0.25, 1), spine_03=(0, -0.18, 1),
            neck_01=(0, -0.22, 1), head=(0, -0.06, 1))
MID2 = dict(pelvis=(0, -0.1, 1), spine_01=(0, -0.16, 1), spine_02=(0, -0.12, 1), spine_03=(0, -0.06, 1),
            neck_01=(0, -0.16, 1), head=(0, -0.03, 1))
LAND = dict(pelvis=(0, 0.35, 1), spine_01=(0, 0.14, 1), spine_02=(0, 0.1, 1), spine_03=(0, 0.04, 1),
            neck_01=(0, -0.16, 1), head=(0, -0.03, 1))
SEAT_Z = {'a': 0.52, 'b': 0.54}          # validated with seat_check.py: no couch penetration
SEAT_Y = {'a': -0.062, 'b': -0.143}


def hipz(C):
    return C.rig.data.bones['thigh_l'].head_local.z


def rt(C, kind, dx=0.0):
    zs = SEAT_Z[C.key] - hipz(C); ys = SEAT_Y[C.key]
    return {'stand': (0, -0.5, 0.0), 'antic': (0, -0.5, -0.03), 'mid1': (0, -0.34, -0.2),
            'mid2': (0, min(-0.13, ys - 0.07), zs + 0.05), 'land': (0, ys, zs - 0.012), 'seat': (dx, ys, zs)}[kind]


FEET = {'stand': (0.11, -0.56, 0.08), 'a': (0.14, -0.68, 0.085), 'b': (0.13, -0.66, 0.082)}
FEET_KEYS = {}      # character -> [(frame, (x, y, z), dx)]


def P_(C, dirs, root, frame, curls, post=None):
    pose5.pose(C.rig, dirs, root=root, curls=curls)
    ft = feet_at(C, frame)
    for side, sx in (('l', 1), ('r', -1)):
        pose5.leg_ik(C.rig, side, Vector((sx * ft[0] + ft[3], ft[1], ft[2])), pole=Vector((sx * 0.12, -1, 0.4)))
        pose5.set_dir(C.rig.pose.bones['foot_' + side], (0, -1, -0.5)); upd()
    if post: post(C)
    pose5.key(C.rig, frame)


def feet_at(C, f):
    keys = FEET_KEYS[C.key]
    if f <= keys[0][0]: k = keys[0]; return (*k[1], k[2])
    for (f0, p0, d0), (f1, p1, d1) in zip(keys, keys[1:]):
        if f <= f1:
            t = (f - f0) / (f1 - f0); t = t * t * (3 - 2 * t)
            return tuple(a + (b - a) * t for a, b in zip(p0, p1)) + (d0 + (d1 - d0) * t,)
    k = keys[-1]; return (*k[1], k[2])


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
FA, FB = 100, 96            # frames where he / she starts to sit down
FEET_KEYS['a'] = [(1, FEET['stand'], 0.0), (FA + 28, FEET['stand'], 0.0), (FA + 42, FEET['a'], 0.0)]
FEET_KEYS['b'] = [(1, FEET['stand'], 0.0), (FB + 26, FEET['stand'], 0.0), (FB + 40, FEET['b'], 0.0),
                  (306, FEET['b'], 0.0), (330, FEET['b'], -0.02)]

# ---------------- him
r = A.rig
P_(A, M(UP, REL_L, A_HOLD_STAND), rt(A, 'stand'), 1, CA)
P_(A, M(turn(3, 6, 10), REL_L, A_HOLD_STAND), rt(A, 'stand'), 44, CA)
P_(A, M(turn(8, 14, 24, tilt=0.03), REL_L, A_HOLD_STAND), rt(A, 'stand'), 56, CA)
P_(A, M(turn(8, 14, 22), REL_L, A_TOAST), rt(A, 'stand'), 66, CA)
P_(A, M(turn(8, 12, 18, nod=0.04), REL_L, A_TOAST), rt(A, 'stand'), 74, CA)
P_(A, M(turn(4, 6, 8), REL_L, A_HOLD_STAND), rt(A, 'stand'), 86, CA)
P_(A, M(UP, REL_L, A_HOLD_STAND, dict(neck_01=((-0.04, 0.02, 1), -10), head=((-0.06, 0.06, 1), -28))), rt(A, 'stand'), 96, CA)
P_(A, M(UP, REL_L, A_HOLD_STAND), rt(A, 'antic'), FA, CA)
def reach(target):
    """His left hand reaches for the seat cushion while he sits down (planted on its surface)."""
    def post(C):
        rg = C.rig; inv = rg.matrix_world.inverted()
        pose5.arm_ik(rg, 'l', inv @ Vector(target), pole=Vector((0.6, 1, 0)))
        pose5.set_dir(rg.pose.bones['hand_l'], (0.3, -1, -0.3)); upd()
    return post


PLANT = (scene5.AX - 0.22, cy + 0.02, st + 0.09)
P_(A, M(MID1, A_REACH, A_HOLD_STAND), rt(A, 'mid1'), FA + 8, CA, post=reach((scene5.AX - 0.24, cy + 0.2, st + 0.24)))
P_(A, M(MID2, A_REACH, A_HOLD_STAND), rt(A, 'mid2'), FA + 16, CA, post=reach(PLANT))
P_(A, M(LAND, A_HOLD, A_REACH), rt(A, 'land'), FA + 22, CA, post=reach(PLANT))
P_(A, M(SEAT, A_HOLD), rt(A, 'seat'), FA + 32, CA)
P_(A, M(SEAT, A_HOLD, dict(head=((0.02, -0.03, 1), 6))), rt(A, 'seat'), 146, CA)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0, -0.1, 1), head=(0, 0.1, 1))), rt(A, 'seat'), 162, CA, post=sip)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0, -0.08, 1), head=(0, 0.14, 1))), rt(A, 'seat'), 172, CA, post=sip)
P_(A, M(SEAT, A_HOLD), rt(A, 'seat'), 188, CA)
P_(A, M(SEAT, A_HOLD, dict(neck_01=(0.12, -0.2, 1), head=((0.16, -0.05, 1), 42))), rt(A, 'seat'), 202, CA)
KA = M(SEAT, A_HOLD, dict(spine_02=(0.1, 0.22, 1), spine_03=(0.32, 0.06, 1), neck_01=(0.55, -0.12, 1)))
P_(A, M(SEAT, A_HOLD, dict(spine_03=(0.12, 0.08, 1), neck_01=(0.25, -0.15, 1))), rt(A, 'seat'), 222, CA)
P_(A, KA, rt(A, 'seat'), 246, CA)
P_(A, KA, rt(A, 'seat'), 280, CA)
P_(A, M(SEAT, A_HOLD, dict(spine_03=(0.14, 0.08, 1), neck_01=(0.25, -0.15, 1))), rt(A, 'seat'), 298, CA)
# (his left arm is keyed separately below: stretch, then around her shoulders - targets taken from her pose)
AR = M(SEAT, A_HOLD, dict(spine_03=(0.04, 0.08, 1), neck_01=(0.15, -0.16, 1), head=((0.28, -0.02, 1), 12)))
P_(A, AR, rt(A, 'seat'), 340, CA)
P_(A, M(AR, dict(head=((0.31, -0.02, 1), 12))), rt(A, 'seat'), 392, CA)
P_(A, M(AR, dict(head=((0.29, -0.04, 1), 10))), rt(A, 'seat'), 420, CA)

# ---------------- her
l = B.rig
P_(B, M(UP, B_BOWL_STAND), rt(B, 'stand'), 1, CB)
P_(B, M(turn(-3, -8, -12), B_BOWL_STAND), rt(B, 'stand'), 44, CB)
P_(B, M(turn(-8, -14, -26, tilt=-0.07), B_BOWL_STAND), rt(B, 'stand'), 54, CB)
P_(B, M(turn(-9, -15, -24, tilt=-0.05), B_OFFER), rt(B, 'stand'), 64, CB)
P_(B, M(turn(-7, -11, -20, tilt=-0.04, nod=0.03), B_BOWL_STAND), rt(B, 'stand'), 76, CB)
P_(B, M(turn(-2, -4, -6), B_BOWL_STAND), rt(B, 'stand'), 86, CB)
P_(B, M(UP, B_BOWL_STAND, dict(neck_01=((0.04, 0.02, 1), 10), head=((0.06, 0.06, 1), 26))), rt(B, 'stand'), 92, CB)
P_(B, M(UP, B_BOWL_STAND), rt(B, 'antic'), FB, CB)
P_(B, M(MID1, B_BOWL_STAND), rt(B, 'mid1'), FB + 8, CB)
P_(B, M(MID2, B_BOWL_STAND), rt(B, 'mid2'), FB + 16, CB)
P_(B, M(LAND, B_BOWL), rt(B, 'land'), FB + 22, CB)
P_(B, M(SEAT, B_BOWL), rt(B, 'seat'), FB + 32, CB)
P_(B, M(SEAT, B_BOWL), rt(B, 'seat'), 150, CB)
P_(B, M(SEAT, B_BOWL, dict(head=(0.02, -0.1, 1))), rt(B, 'seat'), 164, CB, post=eat)
P_(B, M(SEAT, B_BOWL, dict(head=(0.04, -0.12, 1))), rt(B, 'seat'), 172, CB, post=eat)
P_(B, M(SEAT, B_BOWL, dict(neck_01=(-0.12, -0.2, 1), head=((-0.16, -0.05, 1), -36))), rt(B, 'seat'), 192, CB)
KB = M(SEAT, B_BOWL, dict(spine_02=(-0.08, 0.2, 1), spine_03=(-0.28, 0.06, 1), neck_01=(-0.48, -0.1, 1)))
P_(B, M(SEAT, B_BOWL, dict(spine_03=(-0.1, 0.08, 1), neck_01=(-0.2, -0.15, 1))), rt(B, 'seat'), 220, CB)
P_(B, KB, rt(B, 'seat'), 244, CB)
P_(B, KB, rt(B, 'seat'), 282, CB)
P_(B, M(SEAT, B_BOWL, dict(spine_03=(-0.12, 0.08, 1), neck_01=(-0.2, -0.12, 1))), rt(B, 'seat'), 306, CB)
HB = M(SEAT, B_BOWL, dict(spine_02=(-0.1, 0.22, 1), spine_03=((-0.22, 0.1, 1), -6), neck_01=(-0.5, 0.0, 1),
                          head=((-0.5, 0.06, 1), -10)))
P_(B, HB, rt(B, 'seat', dx=-0.02), 342, CB)
P_(B, M(HB, dict(head=((-0.54, 0.05, 1), -10))), rt(B, 'seat', dx=-0.02), 392, CB)
P_(B, HB, rt(B, 'seat', dx=-0.02), 420, CB)


# ---------------- kiss: aim the heads on top of the base poses
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


# ---------------- the snuggle: he stretches, then lays his left arm around her shoulders
def arm_keys(f, ua_d, la_d, hd_d, world=False):
    sc.frame_set(f)
    ainv = r.matrix_world.inverted()
    ua, la, hd = (r.pose.bones[n] for n in ('upperarm_l', 'lowerarm_l', 'hand_l'))
    if world:          # ua_d = elbow target, la_d = wrist target, hd_d = hand direction (all world space)
        pose5.set_dir(ua, (ainv @ ua_d) - ua.head); upd()
        pose5.set_dir(la, (ainv @ la_d) - la.head); upd()
        pose5.set_dir(hd, ainv.to_3x3() @ Vector(hd_d)); upd()
    else:              # plain directions in armature space
        for pb, d in ((ua, ua_d), (la, la_d), (hd, hd_d)):
            pose5.set_dir(pb, d); upd()
    for pb in (ua, la, hd):
        pb.keyframe_insert('rotation_quaternion', frame=f)


def around(f, eoff, woff, hand):
    sc.frame_set(f)
    e = l.matrix_world @ l.pose.bones['neck_01'].head + Vector(eoff)       # elbow behind her neck
    w = l.matrix_world @ l.pose.bones['upperarm_l'].head + Vector(woff)    # wrist on her far shoulder
    arm_keys(f, e, w, hand, world=True)


arm_keys(306, (0.22, -0.95, 0.12), (0.18, -0.55, 0.85), (0.1, -0.3, 1))       # lifts the arm forward...
arm_keys(314, (0.3, -0.12, 1), (0.22, 0.18, 1), (0.15, 0.3, 1))               # ...stretches it up...
around(326, (0.03, -0.2, 0.2), (-0.06, -0.09, 0.2), (-0.3, 0.2, -0.6))        # ...over her head...
for f in (340, 392, 420):                                                       # ...and around her shoulders
    around(f, (0.03, -0.16, 0.06), (-0.087, -0.063, 0.061), (-0.35, 0.45, -1))
for C in (A, B):
    pose5.smooth(C.rig)


# ---------------- bake: breathing, weight shift, small head motion; feet re-solved on every frame
from mathutils import noise as mnoise


def _rot(pb, axis, deg):
    ax = (pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis)).normalized()
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg))


def bake(C, sit_frame, seed):
    rg = C.rig; pbs = rg.pose.bones
    names = [pb.name for pb in pbs]
    bq = {n: [] for n in names}; broot = []
    for f in range(1, END + 1):
        sc.frame_set(f)
        for pb in pbs: bq[pb.name].append(pb.rotation_quaternion.copy())
        broot.append(pbs['Root'].location.copy())
    rg.animation_data_clear()
    Rinv = pbs['Root'].bone.matrix_local.to_3x3().inverted()
    for i, f in enumerate(range(1, END + 1)):
        for n in names: pbs[n].rotation_quaternion = bq[n][i]
        t = f / FPS
        standing = 1.0 - max(0.0, min(1.0, (f - sit_frame) / 10.0))
        # weight shift while standing
        w = math.sin(2 * math.pi * t / 5.2 + seed)
        pbs['Root'].location = broot[i] + Rinv @ Vector((0.013 * w * standing, 0, -0.004 * abs(w) * standing))
        _rot(pbs['pelvis'], (0, 1, 0), 1.8 * w * standing)
        _rot(pbs['spine_02'], (0, 1, 0), -1.1 * w * standing)
        # breathing
        per = 3.3 if standing > 0.5 else 4.1
        b = math.sin(2 * math.pi * t / per + seed * 0.7)
        _rot(pbs['spine_02'], (1, 0, 0), -0.5 * b); _rot(pbs['spine_03'], (1, 0, 0), -1.0 * b)
        _rot(pbs['neck_01'], (1, 0, 0), 0.7 * b)
        _rot(pbs['clavicle_l'], (0, 1, 0), -1.0 * b); _rot(pbs['clavicle_r'], (0, 1, 0), 1.0 * b)
        # small living head motion (less during the kiss)
        k = 0.35 if 222 <= f <= 298 else 1.0
        n1 = mnoise.noise(Vector((t * 0.55, seed, 0.3))); n2 = mnoise.noise(Vector((t * 0.5, seed + 4.1, 1.7)))
        _rot(pbs['head'], (0, 0, 1), 2.2 * n1 * k); _rot(pbs['head'], (1, 0, 0), 1.4 * n2 * k)
        _rot(pbs['neck_01'], (0, 0, 1), 0.8 * n1 * k)
        upd()
        ft = feet_at(C, f)
        for side, sx in (('l', 1), ('r', -1)):
            pose5.leg_ik(rg, side, Vector((sx * ft[0] + ft[3], ft[1], ft[2])), pole=Vector((sx * 0.12, -1, 0.4)))
            pose5.set_dir(pbs['foot_' + side], (0, -1, -0.5))
        upd()
        for pb in pbs: pb.keyframe_insert('rotation_quaternion', frame=f)
        pbs['Root'].keyframe_insert('location', frame=f)
    for fc in rg.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


_muted = []
for ob in bpy.data.objects:
    for md in ob.modifiers:
        if md.show_viewport:
            md.show_viewport = False; _muted.append(md)
bake(A, FA, 0.0); bake(B, FB, 1.9)
for md in _muted: md.show_viewport = True

# ---------------- cushions give way when they sit down
scene5.cushion_dents(A, B, info, ((FA + 16, FA + 26), (FB + 16, FB + 26)))


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
look(A, 46, hb0 + Vector((0, 0.1, 0))); look(B, 44, ha0 + Vector((0, 0.1, 0)))      # talking to each other
look(A, 80, hb0 + Vector((0, 0.1, -0.1))); look(B, 78, ha0 + Vector((0, 0.1, -0.05)))
look(A, 96, Vector((0.6, cy - 0.3, 0.5))); look(B, 92, Vector((-0.6, cy - 0.3, 0.5)))    # glance at the couch
look(A, 112, Vector((0.2, 0.8, 0.8))); look(B, 108, Vector((-0.2, 0.8, 0.8)))
look(A, 140, TV); look(B, 136, TV)
look(A, 196, Vector((-0.4, cy + 0.1, 1.15))); look(B, 190, Vector((0.4, cy + 0.1, 1.2)))
look(A, 300, TV); look(B, 300, TV); look(A, 420, TV); look(B, 420, TV)
for f in (28, 62, 118, 188, 330, 396): blink(A, f)
for f in (20, 58, 100, 178, 360, 406): blink(B, f)
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
    seated = max(0.0, min(1.0, (f - (FB + 16)) / 12.0))
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
FINAL = ((0.05, cy - 1.05, 1.66), (0, NN, TVZ - 0.42))
crane = []
for i, f in enumerate(range(S4, S5 + 1, 3)):
    tt = (f - S4) / (S5 - S4); e = tt * tt * (3 - 2 * tt)
    ang = R(8) + e * R(172)                       # in front -> over the heads -> behind
    rad = 1.3 if math.cos(ang) > 0 else 1.05
    pos = Vector((0.12 * (1 - e) + 0.05 * e + 0.28 * math.sin(math.pi * e), cy + math.cos(ang) * rad,
                  1.3 + 0.42 * math.sin(math.pi * e) + (1.66 - 1.3) * e))
    k = max(0.0, min(1.0, (e - 0.62) / 0.38)); k = k * k * (3 - 2 * k)
    look_t = (mid + Vector((0, 0.05, 0.02))).lerp(Vector((0, NN, TVZ - 0.42)), k)
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
