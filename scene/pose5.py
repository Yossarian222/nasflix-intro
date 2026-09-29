"""Posing helpers for the MPFB 'game_engine' rig (character faces -Y in armature space)."""
import bpy, math
from mathutils import Vector, Matrix, Quaternion

ORDER = ['Root', 'pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head',
         'clavicle_l', 'upperarm_l', 'lowerarm_l', 'hand_l', 'clavicle_r', 'upperarm_r', 'lowerarm_r', 'hand_r',
         'thigh_l', 'calf_l', 'foot_l', 'ball_l', 'thigh_r', 'calf_r', 'foot_r', 'ball_r']
FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']


def upd():
    bpy.context.view_layer.update()


def set_dir(pb, d, twist=0.0):
    rest = pb.bone.matrix_local.to_3x3()
    ry = rest.col[1].normalized()
    d = Vector(d).normalized()
    q = ry.rotation_difference(d)
    if twist:
        q = Quaternion(d, math.radians(twist)) @ q
    M = (q.to_matrix() @ rest).to_4x4(); M.translation = pb.head
    pb.matrix = M


def pose(rig, dirs, root=(0, 0, 0), curls=None):
    """dirs: bone -> direction (armature space) or (direction, twist_deg). Others: rest relative to parent."""
    pbs = rig.pose.bones
    for pb in pbs:
        pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)
    upd()
    if 'Root' in pbs:
        R = pbs['Root']
        R.matrix = Matrix.Translation(Vector(root)) @ R.bone.matrix_local
        upd()
    for name in ORDER:
        if name not in pbs or name == 'Root': continue
        if name in dirs:
            v = dirs[name]; tw = 0.0
            if isinstance(v, tuple) and len(v) == 2 and not isinstance(v[0], (int, float)):
                v, tw = v
            set_dir(pbs[name], v, tw)
            upd()
    if curls:
        for side, amt in curls.items():
            for f in FINGERS:
                for k in (1, 2, 3):
                    nm = f'{f}_0{k}_{side}'
                    if nm in pbs:
                        a = amt * (0.55 if f == 'thumb' else 1.0) * (0.8 if k == 1 else 1.0)
                        pbs[nm].rotation_quaternion = Quaternion((1, 0, 0), math.radians(a))
        upd()


def leg_ik(rig, side, target, pole=Vector((0, -1, 0.1))):
    """Two-bone IK in armature space: thigh/calf so the ankle reaches target, knee toward pole."""
    upd()
    th = rig.pose.bones['thigh_' + side]; ca = rig.pose.bones['calf_' + side]
    a = th.bone.length; b = ca.bone.length
    hip = th.head.copy(); t = Vector(target)
    d = t - hip; L = min(d.length, a + b - 1e-4); dn = d.normalized()
    x = (a * a - b * b + L * L) / (2 * L); h = math.sqrt(max(a * a - x * x, 0))
    pn = (pole - pole.dot(dn) * dn).normalized()
    knee = hip + dn * x + pn * h
    set_dir(th, knee - hip); upd()
    set_dir(ca, (hip + dn * L) - knee); upd()


def key(rig, frame):
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=frame)
    if 'Root' in rig.pose.bones:
        rig.pose.bones['Root'].keyframe_insert('location', frame=frame)


def smooth(ob, interp='BEZIER'):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp; kp.easing = 'AUTO'
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'


def aim_head(rig, target_world, blend=1.0, bone='head', up=(0, 0, 1)):
    """Rotate a bone so the face (-Y of the character) points at target_world."""
    upd()
    pb = rig.pose.bones[bone]
    inv = rig.matrix_world.inverted()
    tgt = inv @ Vector(target_world)
    fwd = (tgt - pb.head).normalized()
    cur = pb.matrix.to_3x3()
    # current face direction in armature space: rest face is -Y of the armature
    face = (cur @ pb.bone.matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))).normalized()
    q = face.rotation_difference(fwd)
    q = Quaternion().slerp(q, blend)
    M = (q.to_matrix() @ cur).to_4x4(); M.translation = pb.head
    pb.matrix = M; upd()


def arm_ik(rig, side, target, pole):
    """Two-bone IK for the arm: wrist (hand head) reaches target, elbow toward pole."""
    upd()
    ua = rig.pose.bones['upperarm_' + side]; la = rig.pose.bones['lowerarm_' + side]
    a = ua.bone.length; b = la.bone.length
    sh = ua.head.copy(); t = Vector(target)
    d = t - sh; L = min(d.length, a + b - 1e-4); dn = d.normalized()
    x = (a * a - b * b + L * L) / (2 * L); h = math.sqrt(max(a * a - x * x, 0))
    pn = (pole - pole.dot(dn) * dn).normalized()
    el = sh + dn * x + pn * h
    set_dir(ua, el - sh); upd()
    set_dir(la, (sh + dn * L) - el); upd()


def mouth(rig):
    """Approximate mouth position (armature space) from the posed head bone."""
    upd()
    pb = rig.pose.bones['head']
    M = pb.matrix @ pb.bone.matrix_local.inverted()
    rest = pb.bone.head_local + Vector((0, -0.105, -0.035))
    return M @ rest


def roll_head(rig, deg, bone='head'):
    """Tilt a bone around the armature Y axis (character's front-back axis)."""
    upd()
    pb = rig.pose.bones[bone]
    q = Quaternion(Vector((0, 1, 0)), math.radians(deg))
    M = (q.to_matrix() @ pb.matrix.to_3x3()).to_4x4(); M.translation = pb.head
    pb.matrix = M; upd()
