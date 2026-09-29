"""Intro v5 characters.

Bodies and faces: MakeHuman base mesh + targets through the MPFB2 add-on (CC0).
Look: smooth porcelain-clay skin, foam-clay (tiny bead) clothes and hair, clay brows and glasses.
Everything is procedural; the two characters are described only by numbers in SPEC_A / SPEC_B.
"""
import bpy, bmesh, math, os, sys, importlib, random
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils import noise as mnoise
import addon_utils
from lib import *
import mats5

_M = "bl_ext.user_default.mpfb"


def mpfb():
    addon_utils.enable(_M, default_set=True)
    HS = importlib.import_module(_M + '.services.humanservice').HumanService
    TS = importlib.import_module(_M + '.services.targetservice').TargetService
    data = os.path.join(os.path.dirname(sys.modules[_M].__file__), 'data')
    return HS, TS, data


TOP_BONES = {'spine_01', 'spine_02', 'spine_03', 'clavicle_l', 'clavicle_r', 'upperarm_l', 'upperarm_r',
             'lowerarm_l', 'lowerarm_r', 'neck_01'}
LEG_BONES = {'thigh_l', 'thigh_r', 'calf_l', 'calf_r'}
FOOT_BONES = {'foot_l', 'foot_r', 'ball_l', 'ball_r'}

# ---------------------------------------------------------------------------------------------- specs
SPEC_A = dict(
    key='a', height=1.85,
    macro=dict(gender=1.0, age=0.5, muscle=0.72, weight=0.62, proportions=0.8, height=0.6,
               cupsize=0.5, firmness=0.5, race=dict(caucasian=1.0, asian=0.0, african=0.0)),
    face={'head/head-oval': 0.45, 'head/head-scale-vert-incr': 0.3, 'forehead/forehead-scale-vert-incr': 0.35,
          'cheek/l-cheek-bones-incr': 0.45, 'cheek/r-cheek-bones-incr': 0.45,
          'cheek/l-cheek-volume-decr': 0.3, 'cheek/r-cheek-volume-decr': 0.3,
          'chin/chin-width-decr': 0.25, 'chin/chin-height-incr': 0.2, 'chin/chin-prominent-incr': 0.15,
          'nose/nose-scale-vert-incr': 0.3, 'nose/nose-width1-decr': 0.25, 'nose/nose-point-width-decr': 0.2,
          'mouth/mouth-upperlip-volume-decr': 0.35, 'mouth/mouth-lowerlip-volume-decr': 0.2,
          'eyebrows/eyebrows-trans-down': 0.25, 'neck/neck-scale-horiz-incr': 0.2},
    skin='#d9997a', lips='#b97a70', blush=0.3, stubble=0.55, iris='#6d8fae',
    hair=('short', '#3b281d', '#4f3727'), brow=('#3f2b20', 'straight'),
    top=('#48648f', '#6f89b3'), pants='#384458', socks='#8b8e95', glasses=False,
)
SPEC_B = dict(
    key='b', height=1.66,
    macro=dict(gender=0.0, age=0.48, muscle=0.42, weight=0.4, proportions=0.82, height=0.42,
               cupsize=0.45, firmness=0.6, race=dict(caucasian=1.0, asian=0.0, african=0.0)),
    face={'head/head-round': 0.35, 'cheek/l-cheek-volume-incr': 0.5, 'cheek/r-cheek-volume-incr': 0.5,
          'cheek/l-cheek-bones-incr': 0.2, 'cheek/r-cheek-bones-incr': 0.2,
          'mouth/mouth-scale-horiz-incr': 0.3, 'mouth/mouth-lowerlip-volume-incr': 0.15,
          'nose/nose-point-up': 0.25, 'nose/nose-scale-horiz-decr': 0.15, 'chin/chin-width-decr': 0.1,
          'eyebrows/eyebrows-angle-up': 0.2},
    skin='#e2a78a', lips='#c96f77', blush=0.6, stubble=0.0, iris='#5f88b5',
    hair=('long', '#5a3b28', '#b0804f'), brow=('#4b3326', 'arched'),
    top=('#e3a1aa', '#f2c1c8'), pants='#8fa7c6', socks='#efe6dc', glasses=True,
)


# ---------------------------------------------------------------------------------------------- utils
def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def table(tab, x):
    x = abs(x)
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[-1][1]


def vweights(ob):
    names = {g.index: g.name for g in ob.vertex_groups}
    return [{names[g.group]: g.weight for g in v.groups} for v in ob.data.vertices]


def dominant(w, bones):
    best, bw = None, 0.0
    for k, x in w.items():
        if k in bones and x > bw:
            best, bw = k, x
    return best


def parent_bone(ob, rig, bone):
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def keep_vertices(ob, keep):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    kill = [v for v in bm.verts if v.index not in keep]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def curve_tube(name, pts, radius, mat, cyclic=False, radii=None, extrude=0.0, res=4, parent=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = res; cu.extrude = extrude
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
        if radii: sp.points[i].radius = radii[i]
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu); link(ob)
    cu.materials.append(mat)
    return ob


class Person:
    pass


# ---------------------------------------------------------------------------------------------- build
def make_person(spec):
    HS, TS, DATA = mpfb()
    k = spec['key']
    b = HS.create_human(macro_detail_dict=spec['macro'])
    b.name = k + '_body'
    for rel, w in spec['face'].items():
        TS.load_target(b, os.path.join(DATA, 'targets', rel + '.target.gz'), weight=w)
    TS.bake_targets(b)
    W = vweights(b)
    body_idx = [i for i, w in enumerate(W) if w.get('body', 0) > 0.5]
    zmax = max(b.data.vertices[i].co.z for i in body_idx)
    s = spec['height'] / zmax
    b.data.transform(Matrix.Scale(s, 4)); b.data.update()
    U = os.path.join(DATA, 'targets', 'expression', 'units', 'caucasian')
    for nm, f in (('blink_l', 'eye-left-closure'), ('blink_r', 'eye-right-closure'),
                  ('smile', 'mouth-corner-puller'), ('smile_up', 'mouth-elevation'),
                  ('mouth_open', 'mouth-open'), ('squint_l', 'eye-left-slit'), ('squint_r', 'eye-right-slit'),
                  ('brows_up_l', 'eyebrows-left-up'), ('brows_up_r', 'eyebrows-right-up'),
                  ('pucker', 'mouth-pursing')):
        TS.load_target(b, os.path.join(U, f + '.target.gz'), weight=0.0, name=nm)
    rig = HS.add_builtin_rig(b, 'game_engine'); rig.name = k + '_rig'
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    b.data.update()
    P = Person(); P.key = k; P.spec = spec; P.body = b; P.rig = rig
    P.W = vweights(b)
    P.co = [v.co.copy() for v in b.data.vertices]
    P.nrm = [v.normal.copy() for v in b.data.vertices]
    P.body_idx = [i for i, w in enumerate(P.W) if w.get('body', 0) > 0.5]
    P.bset = set(P.body_idx)
    # eyes from the MakeHuman eye helpers
    P.eyes = {}
    for side in ('l', 'r'):
        idx = [i for i, w in enumerate(P.W) if w.get('helper-%s-eye' % side, 0) > 0.5]
        pts = [P.co[i] for i in idx]; c = sum(pts, Vector()) / len(pts)
        r = sum((p - c).length for p in pts) / len(pts)
        P.eyes[side] = (c, r)
    P.ec = (P.eyes['l'][0] + P.eyes['r'][0]) / 2
    P.C = P.ec + Vector((0, 0.088, 0.018))      # skull centre (character faces -Y)
    bones = rig.data.bones
    P.J = {n: bones[n].head_local.copy() for n in ('pelvis', 'neck_01', 'head', 'spine_03', 'upperarm_l', 'thigh_l', 'calf_l', 'foot_l')}
    # BVH of the skin (rest pose)
    bm = bmesh.new(); bm.from_mesh(b.data)
    faces = [f for f in bm.faces if all(v.index in P.bset for v in f.verts)]
    P.bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in faces])
    bm.free()
    P.look = bpy.data.objects.new(k + '_look', None); link(P.look)
    P.look.location = P.ec + Vector((0, -2.0, 0))
    _skin(P); _eyes(P); _brows(P); _clothes(P)
    if spec['hair'][0] == 'short':
        _hair_short(P)
    else:
        _hair_long(P)
    if spec['glasses']:
        _glasses(P)
    return P


def _skin(P):
    sp = P.spec; me = P.body.data; ec = P.ec
    m = mats5.skin(P.key + '_skin', sp['skin'], sp['lips'], blush=sp['blush'], stubble=sp['stubble'])
    me.materials.clear(); me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    sd = P.body.modifiers.new('sub', 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    # cheek points on the skin surface
    cheeks = []
    for side, sx in (('l', 1), ('r', -1)):
        c, r = P.eyes[side]
        q = Vector((c.x + sx * 0.012, c.y - 0.3, c.z - 0.03))
        hit = P.bvh.ray_cast(q, Vector((0, 1, 0)))
        cheeks.append(hit[0] if hit[0] is not None else c)
    blv, stv = [], []
    for i, p in enumerate(P.co):
        d = min((p - c).length for c in cheeks)
        blv.append(math.exp(-(d / 0.022) ** 2))
        s = 0.0
        if i in P.bset and P.W[i].get('head', 0) + P.W[i].get('neck_01', 0) > 0.3:
            front = sstep(ec.y + 0.07, ec.y + 0.02, p.y)
            s = sstep(ec.z - 0.035, ec.z - 0.055, p.z) * sstep(ec.z - 0.165, ec.z - 0.125, p.z) * front
        stv.append(s)
    me.attributes.new('blush', 'FLOAT', 'POINT'); me.attributes['blush'].data.foreach_set('value', blv)
    me.attributes.new('stubble', 'FLOAT', 'POINT'); me.attributes['stubble'].data.foreach_set('value', stv)
    P.skin_mat = m


def _eyes(P):
    P.eyeballs = []
    for side in ('l', 'r'):
        c, r = P.eyes[side]
        rr = r * 0.96
        ob = sphere(P.key + '_eye_' + side, rr, mats5.eye(P.key + '_eye', P.spec['iris'], rr), loc=c, seg=32)
        parent_bone(ob, P.rig, 'head')
        con = ob.constraints.new('DAMPED_TRACK'); con.target = P.look; con.track_axis = 'TRACK_NEGATIVE_Y'; con.influence = 0.7
        P.eyeballs.append(ob)


def _surface(P, x, z, y0=-1.0):
    hit = P.bvh.ray_cast(Vector((x, y0, z)), Vector((0, 1, 0)))
    return hit[0], hit[1]


def _brows(P):
    col, style = P.spec['brow']
    mat = clay(P.key + '_brow', col, rough=0.7, bump=0.3)
    for side, sx in (('l', 1), ('r', -1)):
        c, r = P.eyes[side]
        pts = []; radii = []
        n = 9
        for i in range(n):
            t = i / (n - 1)
            x = c.x + sx * (-0.017 + t * 0.043)
            if style == 'arched':
                z = c.z + 0.0165 + 0.0065 * math.sin(math.pi * min(1, t * 1.25)) - 0.003 * t
            else:
                z = c.z + 0.017 + 0.0025 * math.sin(math.pi * t) - 0.002 * t
            loc, nrm = _surface(P, x, z)
            if loc is None: continue
            pts.append(loc + nrm * 0.0012)
            w = (0.0028 if style == 'straight' else 0.0021) * (1.0 - 0.55 * t ** 1.5) * (0.75 + 0.25 * sstep(0, 0.25, t))
            radii.append(w / 0.0025)
        ob = curve_tube(P.key + '_brow_' + side, pts, 0.0025, mat, radii=radii, res=3)
        ob.scale = (1, 1, 1)
        parent_bone(ob, P.rig, 'head')


def _skin_weights(P, ob):
    """Replace the (poor) helper-mesh weights with weights sampled from the nearest skin vertices."""
    from mathutils.kdtree import KDTree
    if not hasattr(P, 'kd'):
        P.kd = KDTree(len(P.body_idx))
        for n, i in enumerate(P.body_idx):
            P.kd.insert(P.co[i], n)
        P.kd.balance()
        P.bones = {b.name for b in P.rig.data.bones}
    for g in list(ob.vertex_groups):
        if g.name in P.bones:
            ob.vertex_groups.remove(g)
    groups = {}
    for v in ob.data.vertices:
        acc = {}; tot = 0.0
        for co, n, d in P.kd.find_n(v.co, 5):
            wt = 1.0 / (d + 0.002); tot += wt
            for g, w in P.W[P.body_idx[n]].items():
                if g in P.bones:
                    acc[g] = acc.get(g, 0.0) + w * wt
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        ssum = sum(w for _, w in top) or 1.0
        for g, w in top:
            if g not in groups:
                groups[g] = ob.vertex_groups.new(name=g)
            groups[g].add([v.index], w / ssum, 'REPLACE')


def _border_group(ob, name, dist):
    """Vertex group: 0 at open borders of the mesh, 1 further than dist away."""
    from mathutils.kdtree import KDTree
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bv = [v.co.copy() for v in bm.verts if v.is_boundary]
    bm.free()
    g = ob.vertex_groups.new(name=name)
    if not bv:
        g.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE'); return g
    kd = KDTree(len(bv))
    for i, c in enumerate(bv): kd.insert(c, i)
    kd.balance()
    for v in ob.data.vertices:
        d = kd.find(v.co)[2]
        g.add([v.index], sstep(0.0, dist, d), 'REPLACE')
    return g


def _ease(P, ob, part, zhem):
    """Garment ease in the rest pose: straight-leg trousers, a sweater that hangs a little."""
    me = ob.data; me.update()
    knee = P.J['calf_l'].z; ank = P.J['foot_l'].z
    ch = P.J['spine_03'].z
    for v in me.vertices:
        z = v.co.z; n = v.normal
        if part == 'pants':
            d = 0.017 * sstep(knee + 0.06, ank + 0.04, z) + 0.004 * sstep(zhem - 0.25, zhem - 0.1, z) * sstep(knee + 0.1, knee + 0.25, z)
        elif part == 'top':
            d = 0.009 * sstep(ch, zhem + 0.05, z) * sstep(zhem - 0.02, zhem + 0.03, z)
        else:
            d = 0.0
        if d:
            v.co = v.co + n * d
    me.update()


def _cut(ob, part, zhem, nk):
    """Straight hem / waistband / neckline: bisect the garment with planes."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    if part == 'top':
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, zhem), plane_no=(0, 0, 1), clear_inner=True)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        no = Vector((0, -0.42, 1)).normalized()
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, nk.y, nk.z + 0.006), plane_no=no, clear_outer=True)
    elif part == 'pants':
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, zhem + 0.045), plane_no=(0, 0, 1), clear_outer=True)
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def _finish_edges(ob, part, zhem, neck_cut, nk):
    """Snap the cut borders of a garment to smooth curves and fold them into a rolled rim."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bnd = [e for e in bm.edges if e.is_boundary]
    bverts = {v for e in bnd for v in e.verts}
    if part in ('top', 'pants'):
        bm.normal_update()
        ret = bmesh.ops.extrude_edge_only(bm, edges=bnd)
        new = [x for x in ret['geom'] if isinstance(x, bmesh.types.BMVert)]
        dl = bm.verts.layers.deform.active
        newset = set(new)
        for v in new:
            link = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in newset]
            if link:
                src = link[0]
                if dl is not None:
                    for gi, w in src[dl].items():
                        v[dl][gi] = w
                n = src.normal if src.normal.length > 0 else Vector((0, 0, 1))
                v.co = src.co + n * 0.0055
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def _clothes(P):
    sp = P.spec; b = P.body; W = P.W; co = P.co
    zhem = P.J['pelvis'].z - 0.005
    nk = P.J['neck_01']

    def neck_cut(p):
        front = sstep(nk.y + 0.02, nk.y - 0.06, p.y)
        return nk.z + 0.012 - 0.04 * front

    allb = TOP_BONES | LEG_BONES | FOOT_BONES | {'pelvis'}
    tights = [i for i, w in enumerate(W) if w.get('helper-tights', 0) > 0.5]

    def region(i):
        w = W[i]; p = co[i]
        foot = sum(w.get(x, 0) for x in FOOT_BONES)
        bone = dominant(w, allb)
        return bone, foot, p

    top, pants, socks = set(), set(), set()
    for i in tights:
        bone, foot, p = region(i)
        if foot > 0.12: socks.add(i)
        body = bone in LEG_BONES | {'pelvis', 'spine_01', 'spine_02'}
        if body and foot < 0.5 and p.z < zhem + 0.045 + 0.035: pants.add(i)
        if (bone in TOP_BONES | LEG_BONES | {'pelvis'}) and p.z > zhem - 0.035 and p.z < neck_cut(p) + 0.04: top.add(i)
    P.clothes = []
    for part, keep, thick, mat in (
            ('top', top, 0.011, bead(P.key + '_top', sp['top'][0], speck_color=sp['top'][1], speck=0.07, bead=0.0065, var=0.14)),
            ('pants', pants, 0.007, bead(P.key + '_pants', sp['pants'], speck=0.05, bead=0.006, var=0.12)),
            ('socks', socks, 0.004, bead(P.key + '_socks', sp['socks'], speck=0.06, bead=0.005))):
        ob = b.copy(); ob.data = b.data.copy(); link(ob); ob.name = P.key + '_' + part
        ob.shape_key_clear()
        for md in list(ob.modifiers):
            if md.type != 'ARMATURE': ob.modifiers.remove(md)
        keep_vertices(ob, keep)
        _cut(ob, part, zhem, nk)
        _finish_edges(ob, part, zhem, neck_cut, nk)
        _skin_weights(P, ob)
        _ease(P, ob, part, zhem)
        ob.data.materials.clear(); ob.data.materials.append(mat)
        tex = bpy.data.textures.new(P.key + '_wrinkle_' + part, 'CLOUDS'); tex.noise_scale = 0.045 if part == 'top' else 0.035
        tex.noise_depth = 1
        _border_group(ob, 'loose_w', 0.045)
        dp = ob.modifiers.new('loose', 'DISPLACE'); dp.texture = tex; dp.texture_coords = 'LOCAL'; dp.vertex_group = 'loose_w'
        dp.strength = {'top': 0.014, 'pants': 0.01, 'socks': 0.003}[part]; dp.mid_level = 0.3
        while ob.modifiers.find('loose') > 0:
            ob.modifiers.move(ob.modifiers.find('loose'), ob.modifiers.find('loose') - 1)
        so = ob.modifiers.new('thick', 'SOLIDIFY'); so.thickness = thick; so.offset = 1.0
        so.use_rim = True
        sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = 1; sd.render_levels = 1
        for p in ob.data.polygons: p.use_smooth = True
        P.clothes.append(ob)
    # hide skin under the clothes (keep a margin at the openings)
    cov = []
    for i in P.body_idx:
        w = W[i]; p = co[i]
        hand = sum(x for kk, x in w.items() if kk.startswith(('hand_', 'thumb', 'index', 'middle', 'ring', 'pinky')))
        if hand > 0.02: continue
        bone = dominant(w, allb | {'head'})
        if bone in ('head',): continue
        if bone in TOP_BONES or bone == 'pelvis' or bone in LEG_BONES or bone in FOOT_BONES:
            if bone in TOP_BONES and p.z > neck_cut(p) - 0.025: continue
            cov.append(i)
    vg = b.vertex_groups.new(name='covered'); vg.add(cov, 1.0, 'REPLACE')
    mk = b.modifiers.new('hide_covered', 'MASK'); mk.vertex_group = 'covered'; mk.invert_vertex_group = True
    # modifier order: armature, masks, subsurf
    order = [m.name for m in b.modifiers]
    for nm in ('hide_covered', 'sub'):
        idx = [m.name for m in b.modifiers].index(nm)
        b.modifiers.move(idx, len(b.modifiers) - 1)


def _hairline_point(P, th, z):
    """Skin point at azimuth th (deg, 0 = front) and height z, found by a horizontal ray towards the skull axis."""
    ra = math.radians(th)
    d = Vector((math.sin(ra), -math.cos(ra), 0.0))
    o = Vector((P.C.x, P.C.y, z)) + d * 0.4
    hit = P.bvh.ray_cast(o, -d)
    return hit[0]


def _scalp(P, d):
    """Skin point + normal along direction d from the skull centre."""
    hit = P.bvh.ray_cast(P.C + d * 0.4, -d)
    return hit[0], hit[1]


def _cap(P, hairline, thick_fn, name, mat, ncol=120, nrow=34, solid=0.004, top=Vector((0, 0.1, 1))):
    """Hair cap as a smooth parametric shell: columns run from the hairline to the crown."""
    ec, C = P.ec, P.C
    top = top.normalized()
    verts, polys, uvs = [], [], []
    for ci in range(ncol):
        th = -180.0 + 360.0 * ci / ncol
        H = _hairline_point(P, th, ec.z + table(hairline, th))
        d0 = (H - C).normalized()
        for rj in range(nrow):
            s = rj / (nrow - 1)
            d = d0.slerp(top, min(s, 0.985))
            S, n = _scalp(P, d)
            if S is None:
                S, n = C + d * 0.1, d
            verts.append(S + n * thick_fn(S, th, s, n))
            uvs.append((th, s))
    for ci in range(ncol):
        c2 = (ci + 1) % ncol
        for rj in range(nrow - 1):
            a = ci * nrow + rj; b = c2 * nrow + rj
            polys.append([a, b, b + 1, a + 1])
    # close the crown
    tip = len(verts)
    S, n = _scalp(P, top)
    verts.append(S + n * thick_fn(S, 0.0, 1.0, n))
    for ci in range(ncol):
        c2 = (ci + 1) % ncol
        polys.append([ci * nrow + nrow - 1, c2 * nrow + nrow - 1, tip])
    ob = mesh_obj(name, verts, polys, mat, smooth=True)
    if solid:
        so = ob.modifiers.new('thick', 'SOLIDIFY'); so.thickness = solid; so.offset = 1.0; so.use_rim = True
    sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    parent_bone(ob, P.rig, 'head')
    return ob


def _hair_short(P):
    _, c0, c1 = P.spec['hair']
    mat = bead(P.key + '_hair', c0, speck_color=c1, speck=0.14, bead=0.0045, rough=0.58, bump=0.8)
    ec = P.ec
    hairline = [(0, 0.066), (18, 0.064), (34, 0.052), (48, 0.047), (70, 0.043), (86, 0.037), (100, 0.037),
                (114, 0.0), (132, -0.05), (155, -0.078), (180, -0.086)]

    def thick(S, th, s, n):
        a = abs(th)
        side = 0.0032
        topw = sstep(0.28, 0.72, n.z) * sstep(135, 70, a) * sstep(0.02, 0.2, s)
        t = side + 0.0125 * topw
        # hair combed up at the front, rising softly from the hairline
        front = sstep(60, 8, a) * sstep(0.45, 0.12, s) * sstep(0.0, 0.2, s)
        t += 0.0065 * front
        # combed clumps running front to back + a bit of mess
        t += topw * (0.0026 * math.cos(math.radians(th) * 22.0 + 4.0 * mnoise.noise(S * 12.0)) + 0.004 * mnoise.noise(S * 22.0))
        t *= 0.3 + 0.7 * sstep(0.0, 0.1, s)
        return max(0.0012, t)
    cap = _cap(P, hairline, thick, P.key + '_hair', mat, solid=0.0015)
    mb = bpy.data.metaballs.new(P.key + '_tufts'); mb.resolution = 0.0028; mb.render_resolution = 0.0028; mb.threshold = 0.6
    mbo = bpy.data.objects.new(P.key + '_tufts', mb); link(mbo)
    rnd = random.Random(5)
    top = Vector((0, 0.1, 1)).normalized()
    def tuft(th, s, size, lean, up=1.0):
        H = _hairline_point(P, th, ec.z + table(hairline, th))
        d = (H - P.C).normalized().slerp(top, s)
        S, n = _scalp(P, d)
        if S is None: return
        base = S + n * thick(S, th, s, n) * 0.6
        axis = (n * up + Vector((0, 0.35, 0.5)) * lean).normalized()
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = base + axis * size[2] * 0.4
        e.radius = max(size) / 0.62; e.stiffness = 2.0
        e.size_x, e.size_y, e.size_z = size[0] / max(size), size[1] / max(size), size[2] / max(size)
        e.rotation = Vector((0, 0, 1)).rotation_difference(axis)
    for th in range(-42, 43, 7):
        tuft(th + rnd.uniform(-2, 2), 0.09 + rnd.uniform(0, 0.03), (0.0085, 0.0075, 0.016 + rnd.uniform(0, 0.004)), 0.9)
    for th in range(-36, 37, 9):
        tuft(th + rnd.uniform(-3, 3), 0.22 + rnd.uniform(0, 0.04), (0.009, 0.0075, 0.02), 1.5, up=0.35)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    bpy.data.objects.remove(mbo); bpy.data.metaballs.remove(mb)
    tob = bpy.data.objects.new(P.key + '_hairtufts', me); link(tob)
    me.materials.append(mat)
    for pg in me.polygons: pg.use_smooth = True
    parent_bone(tob, P.rig, 'head')
    P.hair = [cap, tob]


def _collision_bvh(P):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for ob in [P.body] + [c for c in P.clothes if c.name.endswith('_top')]:
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        off = len(vs)
        vs += [ob.matrix_world @ v.co for v in me.vertices]
        fs += [[off + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)


def _drape(P, bvh, root, nrm, length, clear0, clear1, step=0.01, back=0.0):
    p = root.copy(); v = (nrm * 0.5 + Vector((0, back, -1))).normalized()
    path = [p.copy()]; acc = 0.0
    zf = P.ec.z - 0.1
    while acc < length:
        p = p + v * step; acc += step
        clear = clear0 + (clear1 - clear0) * sstep(zf, zf - 0.14, p.z)
        loc, n2, idx, dist = bvh.find_nearest(p)
        if loc is not None and ((p - loc).dot(n2) < 0 or dist < clear):
            p = loc + n2 * clear
        v = (v * 0.5 + Vector((0, back * 0.3, -1)) * 0.5).normalized()
        path.append(p.copy())
    return path


def _hair_long(P):
    _, c0, c1 = P.spec['hair']
    capmat = bead(P.key + '_haircap', c0, speck_color=c1, speck=0.05, bead=0.0045, rough=0.56, bump=0.7)
    lockmat = mats5.bead_grad(P.key + '_hairlock', c0, c1, bead_size=0.0045, speck=0.12, bump=0.8)
    ec, C = P.ec, P.C
    hairline = [(0, 0.064), (14, 0.062), (28, 0.055), (42, 0.043), (58, 0.026), (80, 0.006), (100, -0.004),
                (125, -0.03), (150, -0.07), (180, -0.085)]

    def thick(S, th, s, n):
        a = abs(th)
        t = 0.0085 + 0.0045 * sstep(0.3, 0.8, s) + 0.002 * sstep(55, 110, a)
        t += 0.0016 * math.cos(math.radians(th) * 30.0) * sstep(0.1, 0.4, s) * sstep(40, 70, a)
        t *= 0.45 + 0.55 * sstep(0.0, 0.07, s)
        if a < 60: t *= 0.2 + 0.8 * sstep(0.0, 0.18, s)
        part = math.exp(-((th - 24.0) / 4.0) ** 2) * sstep(0.75, 0.2, s)
        t *= 1.0 - 0.45 * part
        return max(0.0015, t)
    cap = _cap(P, hairline, thick, P.key + '_haircap', capmat, solid=0.0015, top=Vector((0.08, 0.12, 1)))
    bvh = _collision_bvh(P)
    sh_z = P.J['upperarm_l'].z
    neck_z = P.J['neck_01'].z
    rnd = random.Random(11)
    mb = bpy.data.metaballs.new(P.key + '_hairmb')
    mb.resolution = 0.0042; mb.render_resolution = 0.0042; mb.threshold = 0.6
    mbo = bpy.data.objects.new(P.key + '_hairmb', mb); link(mbo)
    locks = []
    # (angle range, step, root height above eye line, radius, clearance start/end, length, ribbon)
    layers = ((62, 180, 3.6, 0.084, 0.0108, (0.004, 0.026), 0.62, False),)
    for layer, (lo, hi, stepd, zr, rad, clr, L0, ribbon) in enumerate(layers):
        a = lo
        while a <= hi + 1e-6:
            for sgn in (1, -1):
                th = sgn * (a + rnd.uniform(-1.5, 1.5))
                root = _hairline_point(P, th, ec.z + zr + rnd.uniform(-0.006, 0.006))
                if root is None: continue
                nrm = (root - Vector((C.x, C.y, root.z))).normalized()
                L = (L0 + 0.04 * math.sin(math.radians(th) * 3.0) + rnd.uniform(-0.025, 0.025))
                if abs(th) < 75: L -= 0.07
                path = _drape(P, bvh, root + nrm * clr[0], nrm, L, clr[0], clr[1], back=0.6 if abs(th) > 90 else 0.95)
                locks.append((th, path, rad, layer, ribbon))
            a += stepd
    for th, path, rad, layer, ribbon in locks:
        n = len(path); acc = 0.0
        ph = math.radians(abs(th)) * 1.4 + rnd.uniform(-0.25, 0.25); amp = 0.012 + rnd.uniform(-0.002, 0.002); wl = 0.105
        below = [j for j in range(n) if path[j].z < ec.z - 0.1]
        j0 = below[0] if below else n
        for j in range(n):
            q = path[j]
            if j: acc += (path[j] - path[j - 1]).length
            u = j / (n - 1)
            t = (path[min(j + 1, n - 1)] - path[max(j - 1, 0)]).normalized()
            loc, n2, idx, dist = bvh.find_nearest(q)
            out = (q - loc).normalized() if loc is not None and (q - loc).length > 1e-6 else Vector((0, 1, 0))
            bn = t.cross(out).normalized()
            fall = sstep(j0 - 3, j0 + 12, j)          # waves and volume only below the ears
            w = amp * fall * math.sin(ph + acc / wl * 6.283)
            q = q + bn * w + out * 0.35 * abs(w)
            r = rad * (0.8 + 0.45 * fall) * (1.0 - 0.4 * sstep(0.75, 1.0, u))
            chains = ((-0.42, 0.72), (0.42, 0.72)) if ribbon else ((0.0, 1.0),)
            for off, rs in chains:
                el = mb.elements.new(); el.type = 'BALL'; el.co = q + bn * (off * r * 1.6)
                el.radius = r * rs / 0.62; el.stiffness = 2.0
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    bpy.data.objects.remove(mbo); bpy.data.metaballs.remove(mb)
    ob = bpy.data.objects.new(P.key + '_hairlocks', me); link(ob)
    me.materials.clear(); me.materials.append(lockmat)
    for pgn in me.polygons: pgn.use_smooth = True
    top_z = ec.z + 0.03; bot_z = sh_z - 0.3
    zs = [v.co.z for v in me.vertices]
    at = me.attributes.new('hairT', 'FLOAT', 'POINT')
    at.data.foreach_set('value', [sstep(top_z, bot_z, z) for z in zs])
    g1 = ob.vertex_groups.new(name='head'); g2 = ob.vertex_groups.new(name='spine_03')
    for i, z in enumerate(zs):
        w = sstep(sh_z + 0.02, neck_z + 0.07, z)
        if w > 0: g1.add([i], w, 'REPLACE')
        if w < 1: g2.add([i], 1 - w, 'REPLACE')
    ob.parent = P.rig
    am = ob.modifiers.new('rig', 'ARMATURE'); am.object = P.rig
    P.hair = [cap, ob]


def _glasses(P):
    mat = clay(P.key + '_frames', '#08080a', rough=0.34, coat=0.22, bump=0.02)
    parts = []
    ring_pts = {}
    for side, sx in (('l', 1), ('r', -1)):
        c, r = P.eyes[side]
        w, h, cr = 0.0232, 0.0152, 0.007
        # depth: in front of the face around the lens area
        ymin = 1.0
        for gx in (-1, -0.5, 0, 0.5, 1):
            for gz in (-1, 0, 1):
                loc, nrm = _surface(P, c.x + gx * w, c.z + gz * h)
                if loc is not None: ymin = min(ymin, loc.y)
        y = min(c.y - r - 0.0075, ymin - 0.0045)
        cx = c.x + sx * 0.0015
        pts = []
        N = 40
        for i in range(N):
            a = i / N * 6.2832
            px, pz = math.cos(a), math.sin(a)
            # rounded rectangle via superellipse
            e = 0.55
            qx = math.copysign(abs(px) ** e, px) * w
            qz = math.copysign(abs(pz) ** e, pz) * h
            tilt = sx * qx / w * 0.0045   # wrap: outer edge further back
            pts.append(Vector((cx + qx, y + max(0, tilt) * 1.0, c.z + 0.0012 + qz)))
        ring_pts[side] = (cx, y, w, h)
        parts.append(curve_tube(P.key + '_glass_' + side, pts, 0.0017, mat, cyclic=True, extrude=0.0017))
    # bridge
    (lx, ly, w, h), (rx_, ry, _, _) = ring_pts['l'], ring_pts['r']
    zc = P.ec.z + 0.009
    br = [Vector((lx - w + 0.001, ly, zc)), Vector(((lx + rx_) / 2, (ly + ry) / 2 - 0.0035, zc + 0.003)), Vector((rx_ + w - 0.001, ry, zc))]
    parts.append(curve_tube(P.key + '_glass_bridge', br, 0.0021, mat, extrude=0.0012))
    # temples
    for side, sx in (('l', 1), ('r', -1)):
        cx, y, w, h = ring_pts[side]
        z = P.ec.z + 0.012
        pts = [Vector((cx + sx * w, y + 0.002, z))]
        for yy in (0.02, 0.045, 0.07, 0.09):
            ry_ = P.ec.y + yy
            hit = P.bvh.ray_cast(Vector((sx * 0.4, ry_, z)), Vector((-sx, 0, 0)))
            xs = hit[0].x + sx * 0.0045 if hit[0] is not None else cx + sx * (w + 0.02)
            pts.append(Vector((xs, ry_, z - (0.012 if yy > 0.085 else 0.0))))
        parts.append(curve_tube(P.key + '_glass_temple_' + side, pts, 0.0016, mat))
    for ob in parts:
        parent_bone(ob, P.rig, 'head')
    P.glasses = parts
