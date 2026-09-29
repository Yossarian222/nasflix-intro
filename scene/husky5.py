"""Small sitting husky: metaball body (smooth sculpted look) with short plush fur (geometry-nodes curves)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion
from mathutils import noise as mnoise
from lib import *
import mats5
R = math.radians

DARK, MID, WHITE = '#2c3037', '#5b6069', '#f3f0ea'


def _sst(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)


# local frame: faces -Y, sits on z = 0, total height ~0.46 m
EYE_Z, EYE_Y, EYE_X = 0.385, -0.122, 0.031


def _metaballs():
    mb = bpy.data.metaballs.new('husky_mb'); mb.resolution = 0.004; mb.render_resolution = 0.004; mb.threshold = 0.6
    ob = bpy.data.objects.new('husky_mb', mb); link(ob)

    def ball(c, r, stiff=2.0, kind='BALL', size=None, rot=None):
        e = mb.elements.new(); e.type = kind; e.co = c; e.radius = r / 0.62; e.stiffness = stiff
        if size is not None:
            e.size_x, e.size_y, e.size_z = size
        if rot is not None:
            e.rotation = rot
        return e
    def ell(c, rx, ry, rz, rot=None):
        m = max(rx, ry, rz)
        return ball(c, m, kind='ELLIPSOID', size=(rx / m, ry / m, rz / m), rot=rot)
    # hindquarters and thighs (sitting)
    ell((0, 0.07, 0.1), 0.112, 0.118, 0.095)
    for sx in (1, -1):
        ell((sx * 0.082, 0.035, 0.088), 0.058, 0.09, 0.072)
        ell((sx * 0.07, -0.055, 0.022), 0.03, 0.05, 0.02)          # hind paws
    # torso rising to the chest
    q = Quaternion((1, 0, 0), R(-28))
    ell((0, 0.0, 0.2), 0.098, 0.1, 0.13, rot=q)
    ball((0, -0.07, 0.235), 0.078)
    # front legs and paws
    for sx in (1, -1):
        for t in range(13):
            f = t / 12
            ball((sx * 0.046, -0.088 - 0.02 * f, 0.2 - 0.18 * f), 0.03 - 0.004 * f, stiff=1.6)
        ell((sx * 0.044, -0.118, 0.019), 0.028, 0.036, 0.018)
    # neck, head, muzzle, cheeks
    ball((0, -0.052, 0.305), 0.07)
    ball((0, -0.066, 0.39), 0.088)
    ell((0, -0.14, 0.356), 0.038, 0.046, 0.03)
    for sx in (1, -1):
        ball((sx * 0.044, -0.1, 0.352), 0.044)
    # tail curled around the right side
    pts = [(0.0, 0.16, 0.06), (0.06, 0.15, 0.04), (0.11, 0.1, 0.035), (0.135, 0.03, 0.033), (0.13, -0.04, 0.035), (0.11, -0.085, 0.04)]
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        for k in range(4):
            f = k / 4
            ball(a.lerp(b, f), 0.034 - 0.012 * (i + f) / (len(pts) - 1))
    return ob, mb


def _ear(name, sx, mat):
    """Triangular ear (thick, rounded), local to the head."""
    bm = bmesh.new()
    base_w, h, th = 0.056, 0.068, 0.024
    vs = []
    for (x, z) in ((-base_w / 2, 0.0), (base_w / 2, 0.0), (0.0, h)):
        vs.append(bm.verts.new((x, -th / 2, z))); vs.append(bm.verts.new((x, th / 2, z)))
    f0 = bm.faces.new([vs[0], vs[2], vs[4]]); f1 = bm.faces.new([vs[5], vs[3], vs[1]])
    for a, b in ((0, 2), (2, 4), (4, 0)):
        bm.faces.new([vs[a], vs[a + 1], vs[b + 1], vs[b]])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=4, use_grid_fill=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob)
    md = ob.modifiers.new('sub', 'SUBSURF'); md.levels = 2; md.render_levels = 2
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    ob.location = (sx * 0.045, -0.055, 0.438)
    ob.rotation_euler = (R(-8), sx * R(-14), sx * R(-12))
    return ob


def _markings(me):
    """Husky coat: dark cap/back/tail top, white face mask, chest, legs and belly."""
    col = me.attributes.new('furcol', 'FLOAT_COLOR', 'POINT')
    fm = me.attributes.new('furmask', 'FLOAT', 'POINT')
    dk, md, wh = hexcol(DARK), hexcol(MID), hexcol(WHITE)
    cols, masks = [], []
    for v in me.vertices:
        p = v.co
        n = mnoise.noise(p * 40.0) * 0.012
        # body: dark saddle on the back and upper sides
        back = _sst(-0.085, -0.01, p.y + n) * _sst(0.08, 0.15, p.z + n)
        side = _sst(0.04, 0.07, abs(p.x) + n) * _sst(0.1, 0.17, p.z + n)
        cape = _sst(0.03, 0.055, abs(p.x) + n) * _sst(0.2, 0.25, p.z + n) * _sst(0.36, 0.32, p.z) * _sst(-0.1, -0.06, p.y + n)
        body = max(back, side * 0.9, cape) * _sst(0.36, 0.31, p.z)
        # head: dark cap, stripe down the forehead, dark behind the eyes; white muzzle/cheeks
        head = 0.0
        if p.z > 0.3:
            cap = _sst(EYE_Z + 0.004, EYE_Z + 0.022, p.z + n)
            stripe = math.exp(-((p.x) / 0.009) ** 2) * _sst(EYE_Z - 0.01, EYE_Z + 0.01, p.z) * _sst(-0.1, -0.13, p.y)
            behind = _sst(EYE_Y + 0.03, EYE_Y + 0.06, p.y + n) * _sst(EYE_Z - 0.04, EYE_Z - 0.01, p.z)
            brow = math.exp(-(((abs(p.x) - 0.03) / 0.011) ** 2 + ((p.z - (EYE_Z + 0.02)) / 0.008) ** 2))
            head = max(cap, stripe * 0.9, behind) * (1 - 0.95 * brow)
            muzzle = _sst(-0.1, -0.125, p.y) * _sst(EYE_Z - 0.005, EYE_Z - 0.02, p.z)
            head *= 1 - muzzle
        # tail: dark on top
        tail = 0.0
        if p.z < 0.08 and (abs(p.x) > 0.09 or p.y > 0.12):
            tail = _sst(0.035, 0.06, p.z + n)
        # neck/chest and belly white
        chest = _sst(-0.045, -0.085, p.y + n * 0.5) * _sst(0.34, 0.2, p.z) * _sst(0.05, 0.03, abs(p.x))
        d = max(body, head, tail) * (1 - chest)
        d = max(0.0, min(1.0, d))
        c = tuple(wh[i] * (1 - d) + (dk[i] * 0.8 + md[i] * 0.2) * d for i in range(3)) + (1.0,)
        cols.append(c)
        # no fur on the nose tip and on the eyes
        eye = min((p - Vector((sx * EYE_X, EYE_Y - 0.01, EYE_Z))).length for sx in (1, -1))
        nose = (p - Vector((0, -0.186, 0.358))).length
        masks.append(_sst(0.013, 0.022, eye) * _sst(0.015, 0.024, nose))
    me.attributes['furcol'].data.foreach_set('color', [x for c in cols for x in c])
    me.attributes['furmask'].data.foreach_set('value', masks)


def _fur_material():
    m = bpy.data.materials.new('husky_fur'); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    hb = N.new('ShaderNodeBsdfHairPrincipled'); hb.parametrization = 'COLOR'
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'furcol'
    hi = N.new('ShaderNodeHairInfo')
    # slightly lighter tips
    mr = N.new('ShaderNodeMix'); mr.data_type = 'RGBA'; mr.blend_type = 'SCREEN'
    L.new(hi.outputs['Intercept'], mr.inputs['Factor']); L.new(at.outputs['Color'], mr.inputs['A'])
    mr.inputs['B'].default_value = (0.1, 0.1, 0.1, 1)
    L.new(mr.outputs['Result'], hb.inputs['Color'])
    hb.inputs['Roughness'].default_value = 0.55; hb.inputs['Radial Roughness'].default_value = 0.85
    hb.inputs['Coat'].default_value = 0.3
    L.new(hb.outputs[0], out.inputs['Surface'])
    return m


def _skin_material():
    m = bpy.data.materials.new('husky_skin'); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    b = N['Principled BSDF']
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'furcol'
    L.new(at.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8; b.inputs['Sheen Weight'].default_value = 0.6
    return m


def _fur_nodes(mat, target, density=420000.0, length=(0.005, 0.0095), radius=0.00032):
    ng = bpy.data.node_groups.new('husky_fur_' + target.name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi0 = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    oi = N.new('GeometryNodeObjectInfo'); oi.transform_space = 'RELATIVE'; oi.inputs['Object'].default_value = target
    class _GI: pass
    gi = _GI(); gi.outputs = [oi.outputs['Geometry']]
    dist = N.new('GeometryNodeDistributePointsOnFaces'); dist.distribute_method = 'RANDOM'
    dist.inputs['Seed'].default_value = 3
    na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'; na.inputs['Name'].default_value = 'furmask'
    dm = N.new('ShaderNodeMath'); dm.operation = 'MULTIPLY'; dm.inputs[1].default_value = density
    L.new(na.outputs['Attribute'], dm.inputs[0])
    L.new(gi.outputs[0], dist.inputs['Mesh']); L.new(dm.outputs[0], dist.inputs['Density'])
    line = N.new('GeometryNodeCurvePrimitiveLine'); line.inputs['End'].default_value = (0, 0, 1)
    rs = N.new('GeometryNodeResampleCurve'); rs.inputs['Count'].default_value = 4
    L.new(line.outputs['Curve'], rs.inputs['Curve'])
    rv = N.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT'
    rv.inputs[2].default_value = length[0]; rv.inputs[3].default_value = length[1]
    inst = N.new('GeometryNodeInstanceOnPoints')
    L.new(dist.outputs['Points'], inst.inputs['Points']); L.new(rs.outputs['Curve'], inst.inputs['Instance'])
    L.new(dist.outputs['Rotation'], inst.inputs['Rotation'])
    L.new(rv.outputs[1], inst.inputs['Scale'])
    real = N.new('GeometryNodeRealizeInstances'); L.new(inst.outputs['Instances'], real.inputs['Geometry'])
    # droop and comb backwards + a little noise, growing towards the tips
    sp = N.new('GeometryNodeSplineParameter')
    sq = N.new('ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 1.6
    L.new(sp.outputs['Factor'], sq.inputs[0])
    pos = N.new('GeometryNodeInputPosition')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 180.0
    L.new(pos.outputs['Position'], nz.inputs['Vector'])
    sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    L.new(nz.outputs['Color'], sub.inputs[0])
    sc1 = N.new('ShaderNodeVectorMath'); sc1.operation = 'SCALE'; sc1.inputs['Scale'].default_value = 0.006
    L.new(sub.outputs['Vector'], sc1.inputs[0])
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'; add.inputs[1].default_value = (0.0, 0.0035, -0.004)
    L.new(sc1.outputs['Vector'], add.inputs[0])
    sc2 = N.new('ShaderNodeVectorMath'); sc2.operation = 'SCALE'
    L.new(add.outputs['Vector'], sc2.inputs[0]); L.new(sq.outputs['Value'], sc2.inputs['Scale'])
    setp = N.new('GeometryNodeSetPosition'); L.new(real.outputs['Geometry'], setp.inputs['Geometry'])
    L.new(sc2.outputs['Vector'], setp.inputs['Offset'])
    rad = N.new('GeometryNodeSetCurveRadius'); rad.inputs['Radius'].default_value = radius
    L.new(setp.outputs['Geometry'], rad.inputs['Curve'])
    sm = N.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = mat
    L.new(rad.outputs['Curve'], sm.inputs['Geometry'])
    L.new(sm.outputs['Geometry'], go.inputs[0])
    return ng


def _fur_object(target, mat, parent, mul=1.0, **kw):
    cv = bpy.data.hair_curves.new(target.name + '_fur')
    fo = bpy.data.objects.new(target.name + '_fur', cv); link(fo)
    cv.materials.append(mat)
    L = kw.pop('length', (0.005, 0.0095)); Rr = kw.pop('radius', 0.00032)
    gn = fo.modifiers.new('fur', 'NODES'); gn.node_group = _fur_nodes(mat, target, length=(L[0] * mul, L[1] * mul), radius=Rr * mul, **kw)
    fo.parent = parent
    return fo


def make_husky(loc=(0, 0, 0), rotz=0.0, scale=1.0, fur_mul=1.0):
    mbo, mb = _metaballs()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    bpy.data.objects.remove(mbo); bpy.data.metaballs.remove(mb)
    body = bpy.data.objects.new('husky', me); link(body)
    for p in me.polygons: p.use_smooth = True
    _markings(me)
    skin = _skin_material(); fur = _fur_material()
    me.materials.append(skin)
    root = bpy.data.objects.new('husky_root', None); link(root)
    body.parent = root
    _fur_object(body, fur, root, mul=fur_mul)
    # ears (fur as well)
    for sx in (1, -1):
        e = _ear('husky_ear_%s' % ('l' if sx > 0 else 'r'), sx, skin)
        ea = e.data
        c = ea.attributes.new('furcol', 'FLOAT_COLOR', 'POINT'); fm = ea.attributes.new('furmask', 'FLOAT', 'POINT')
        dk, wh = hexcol(DARK), hexcol(WHITE)
        vals = []
        for v in ea.vertices:
            inner = _sst(0.004, -0.004, v.co.y) * _sst(0.012, 0.005, abs(v.co.x) - (0.026 - v.co.z * 0.37))
            vals.append(tuple(dk[i] * (1 - inner) + wh[i] * inner for i in range(3)) + (1.0,))
        ea.attributes['furcol'].data.foreach_set('color', [x for t in vals for x in t])
        ea.attributes['furmask'].data.foreach_set('value', [1.0] * len(ea.vertices))
        e.parent = root
        _fur_object(e, fur, e, mul=fur_mul, length=(0.005, 0.008))
    # eyes (light blue, glossy) and nose
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
    for sx in (1, -1):
        hit = bvh.ray_cast(Vector((sx * EYE_X, -0.4, EYE_Z)), Vector((0, 1, 0)))
        c = hit[0] + Vector((0, 0.0062, 0)) if hit[0] is not None else Vector((sx * EYE_X, EYE_Y, EYE_Z))
        eo = sphere('husky_eye', 0.0132, mats5.pet_eye('husky_eye_m', '#8cc4ec', 0.0132), loc=c, scale=(1.0, 1.0, 0.8), seg=24)
        eo.rotation_euler = (0, 0, sx * R(-15)); eo.parent = root
    hit = bvh.ray_cast(Vector((0, -0.4, 0.362)), Vector((0, 1, 0)))
    nc = hit[0] + Vector((0, 0.004, 0.002)) if hit[0] is not None else Vector((0, -0.19, 0.362))
    no = sphere('husky_nose', 0.0145, clay('husky_nose_m', '#141315', rough=0.25, coat=0.6, bump=0.3), loc=nc, scale=(1.15, 0.85, 0.8), seg=24)
    no.parent = root
    # tiny rig: head bone (fur follows because it samples the deformed body)
    arm = bpy.data.armatures.new('husky_arm'); rig = bpy.data.objects.new('husky_rig', arm); link(rig)
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects: o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    b0 = arm.edit_bones.new('body'); b0.head = (0, 0.05, 0.02); b0.tail = (0, 0.0, 0.25)
    b1 = arm.edit_bones.new('head'); b1.head = (0, -0.045, 0.3); b1.tail = (0, -0.07, 0.45); b1.parent = b0
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.parent = root
    gh = body.vertex_groups.new(name='head'); gb = body.vertex_groups.new(name='body')
    for v in me.vertices:
        w = _sst(0.285, 0.33, v.co.z) * _sst(0.02, -0.02, v.co.y - 0.02)
        if w > 0: gh.add([v.index], w, 'REPLACE')
        if w < 1: gb.add([v.index], 1 - w, 'REPLACE')
    am = body.modifiers.new('rig', 'ARMATURE'); am.object = rig
    bpy.context.view_layer.update()
    for o in [c for c in root.children if c is not body and c is not rig and not c.name.endswith('_fur')]:
        mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = 'head'
        bpy.context.view_layer.update(); o.matrix_world = mw
    for pb in rig.pose.bones: pb.rotation_mode = 'XYZ'
    root.location = loc; root.rotation_euler = (0, 0, rotz); root.scale = (scale, scale, scale)
    root['rig'] = rig.name
    return root
