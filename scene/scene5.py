"""Intro v5 scene assembly: room, two characters, husky and hand props."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix, Quaternion
from lib import *
import room5, people5, pose5, husky5, props5
R = math.radians

AX, BX = 0.28, -0.25          # seat positions (world x) of the two characters
HUSKY_X = -0.72


def seat_root(P, seat_top):
    hipz = P.rig.data.bones['thigh_l'].head_local.z
    return (0, 0.1, seat_top + 0.065 - hipz)


def attach(ob, rig, bone, world_matrix):
    """Parent ob to a pose bone keeping world_matrix at the current pose."""
    bpy.context.view_layer.update()
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = world_matrix


def build():
    reset()
    world('#05060c', 0.04)
    info = room5.build_room()
    A = people5.make_person(people5.SPEC_A)
    B = people5.make_person(people5.SPEC_B)
    cy = info['couch_y']
    for P, x in ((A, AX), (B, BX)):
        P.rig.location = (x, cy + 0.02, 0); P.rig.rotation_euler = (0, 0, math.pi)
    husky = husky5.make_husky((HUSKY_X, cy + 0.06, info['seat_top'] - 0.014), rotz=math.pi - R(22), scale=0.5, fur_mul=1.6)
    pint = props5.pint(); bowl = props5.popcorn_bowl()
    bpy.context.view_layer.update()
    return info, A, B, husky, pint, bowl


# ------------------------------------------------------------------ poses (armature space, character faces -Y)
SEAT = dict(pelvis=(0, 0.5, 1), spine_01=(0, 0.3, 1), spine_02=(0, 0.2, 1), spine_03=(0, 0.06, 1),
            neck_01=(0, -0.18, 1), head=(0, -0.04, 1))
ARMS_A_HOLD = {'upperarm_r': (-0.22, 0.05, -1), 'lowerarm_r': (-0.12, -1, 0.55), 'hand_r': (-0.05, -1, 0.35),
               'upperarm_l': (0.2, -0.02, -1), 'lowerarm_l': (0.05, -1, -0.2), 'hand_l': (0.02, -1, -0.45)}
ARMS_B_BOWL = {'upperarm_l': (0.16, -0.18, -1), 'lowerarm_l': (-0.28, -1, -0.08), 'hand_l': (-0.35, -1, -0.3),
               'upperarm_r': (-0.16, -0.18, -1), 'lowerarm_r': (0.28, -1, -0.08), 'hand_r': (0.35, -1, -0.3)}


def seat_pose(P, arms, curls, seat_top, extra=None):
    d = dict(SEAT); d.update(arms)
    if extra: d.update(extra)
    pose5.pose(P.rig, d, root=seat_root(P, seat_top), curls=curls)
    for side, sx in (('l', 1), ('r', -1)):
        pose5.leg_ik(P.rig, side, Vector((sx * 0.15, -0.44, 0.085)), pole=Vector((0, -1, 0.45)))
        pose5.set_dir(P.rig.pose.bones['foot_' + side], (0, -1, -0.5)); pose5.upd()


def cushion_dents(A, B, info, timing):
    """The seat cushions sink under the two of them (shape key keyed when they land) and a little under the dog."""
    import math as _m
    cush = sorted([o for o in bpy.data.objects if o.name.startswith('seat_cush')], key=lambda o: o.location.x)
    bpy.context.scene.frame_set(timing[0][1] + 12)
    spots = []
    for C in (A, B):
        rg = C.rig
        hips = (rg.matrix_world @ rg.pose.bones['thigh_l'].head + rg.matrix_world @ rg.pose.bones['thigh_r'].head) / 2
        spots.append((C.key, hips))
    for ob in cush:
        me = ob.data
        if not me.shape_keys:
            ob.shape_key_add(name='Basis')
        for (key, hips), (f0, f1) in zip(spots, timing):
            if abs(hips.x - ob.location.x) > 0.5:
                continue
            kb = ob.shape_key_add(name='dent_' + key, from_mix=False)
            for i, v in enumerate(me.vertices):
                if v.co.z <= 0: continue
                w = ob.matrix_world @ v.co
                dx = w.x - hips.x
                d = 0.036 * _m.exp(-((dx / 0.19) ** 2 + ((w.y - (hips.y - 0.03)) / 0.15) ** 2))
                d += 0.022 * _m.exp(-((dx / 0.18) ** 2 + ((w.y - (hips.y + 0.24)) / 0.2) ** 2))
                kb.data[i].co = v.co - Vector((0, 0, d))
            kb.value = 0.0; kb.keyframe_insert('value', frame=f0)
            kb.value = 1.0; kb.keyframe_insert('value', frame=f1)
        if ob.location.x < 0:          # the small dog sits on this one
            kb = ob.shape_key_add(name='dent_dog', from_mix=False)
            for i, v in enumerate(me.vertices):
                if v.co.z <= 0: continue
                w = ob.matrix_world @ v.co
                d = 0.012 * _m.exp(-(((w.x - HUSKY_X) / 0.09) ** 2 + ((w.y - (info['couch_y'] + 0.06)) / 0.09) ** 2))
                kb.data[i].co = v.co - Vector((0, 0, d))
            kb.value = 1.0
    bpy.context.scene.frame_set(1)
