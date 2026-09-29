"""Intro v5 living room: the v4 layout (TV wall, window with the city, bookcase left of the TV)
furnished with Poly Haven CC0 models. Textiles are restyled to foam clay, wood/ceramics stay as they are."""
import bpy, math, random, os, glob
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from lib import *
import room4, mats5
R = math.radians
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get('NASFLIX_ASSETS') or os.path.join(HERE, '..', 'assets')

W0, W1, S, NN, H = -3.2, 3.2, -2.5, 3.2, 2.7
CY = -1.25            # couch centre (y); the couch faces +Y (towards the TV on the north wall)
SEAT_TOP = 0.48


def load_asset(name, pick=None):
    f = glob.glob(os.path.join(ASSETS, '*', name, name + '_1k.blend'))[0]
    with bpy.data.libraries.load(f, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if pick is None or pick(n)]
    obs = [o for o in dst.objects if o is not None]
    for o in obs:
        link(o)
    return obs


def place(name, loc, rotz=0.0, scale=1.0, pick=None, center=True):
    obs = [o for o in load_asset(name, pick) if o.type in ('MESH', 'EMPTY')]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in obs if o.type == 'MESH' for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    off = Vector(((mn.x + mx.x) / 2 if center else 0, (mn.y + mx.y) / 2 if center else 0, mn.z))
    root = bpy.data.objects.new(name + '_root', None); link(root)
    for o in obs:
        if o.parent is None or o.parent not in obs:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = Matrix.Translation(-off) @ mw
    root.location = loc; root.rotation_euler = (0, 0, rotz); root.scale = (scale, scale, scale)
    root['dims'] = tuple(mx - mn)
    return root, obs


def mats_of(obs):
    out = []
    for o in obs:
        if o.type == 'MESH':
            for s in o.material_slots:
                if s.material and s.material not in out:
                    out.append(s.material)
    return out


def top_z(root):
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in root.children_recursive if o.type == 'MESH' for c in o.bound_box]
    return max(zs)


# ------------------------------------------------------------------------------------ pieces
def couch(m):
    mat, mat2 = m['couch'], m['couch2']
    rounded_box('couch_frame', (2.34, 0.96, 0.26), 0.07, mat2, loc=(0, CY, 0.2))
    rounded_box('couch_back', (2.34, 0.26, 0.58), 0.12, mat, loc=(0, CY - 0.35, 0.6))
    for sx in (-1, 1):
        rounded_box('couch_arm', (0.27, 0.96, 0.4), 0.12, mat, loc=(sx * 1.08, CY, 0.46))
    for sx in (-0.465, 0.465):
        cushion('seat_cush', (0.92, 0.66, 0.14), mat, loc=(sx, CY + 0.1, 0.395), puff=0.22)
        cushion('back_cush', (0.9, 0.46, 0.17), mat, loc=(sx, CY - 0.19, 0.73), rot=(R(76), 0, 0), puff=0.3)
    for sx in (-1.04, 1.04):
        for sy in (CY - 0.4, CY + 0.4):
            cyl('couch_leg', 0.028, 0.07, m['woodd'], loc=(sx, sy, 0.035), bevel=0.006)
    # throw pillows (patterned, foam clay) at both ends
    root, obs = place('throw_pillows_01', (0, 0, 0))
    for mt in mats_of(obs):
        mats5.beadify(mt, bead_size=0.0075)
    p1 = [o for o in obs if o.name.endswith('pillow01')][0]; p2 = [o for o in obs if o.name.endswith('pillow02')][0]
    for p, x, rz in ((p1, 0.82, R(-12)), (p2, -0.86, R(10))):
        mw = p.matrix_world.copy(); p.parent = None; p.matrix_world = mw
        bpy.context.view_layer.update()
        pts = [p.matrix_world @ Vector(c) for c in p.bound_box]
        c = sum(pts, Vector()) / 8; zmin = min(q.z for q in pts)
        p.location += Vector((-c.x, -c.y, -zmin))
        root2 = bpy.data.objects.new('pillow_pivot', None); link(root2)
        mw = p.matrix_world.copy(); p.parent = root2; p.matrix_world = mw
        root2.location = (x, CY - 0.24, SEAT_TOP - 0.01); root2.rotation_euler = (R(-18), 0, rz); root2.scale = (0.78, 0.78, 0.78)
    bpy.data.objects.remove(root)


def books_in_cubby(x0, x1, y, z, depth, seed, lean=True):
    rnd = random.Random(seed)
    cols = ['#b8575a', '#5c7fa8', '#d3a24f', '#6f8f6a', '#e3d6c0', '#8a5a8f', '#c96f4a', '#3f5a73']
    x = x0 + 0.01
    while x < x1 - 0.03:
        w = rnd.uniform(0.022, 0.045); h = rnd.uniform(0.2, 0.27)
        if x + w > x1 - 0.01: break
        mat = clay('book%d' % rnd.randrange(8), cols[rnd.randrange(8)], rough=0.55, coat=0.12, bump=0.15)
        room4.book('bk', (x + w / 2, y, z), w, h, depth * rnd.uniform(0.75, 0.9), mat)
        x += w + rnd.uniform(0.001, 0.004)
    return x


def bookcase(m):
    """Cube shelf left of the TV, filled with title-less books and small things."""
    root, obs = place('wooden_display_shelves_01', (-1.78, NN - 0.2, 0), rotz=0.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for o in obs:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); off = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [[off + i for i in p.vertices] for p in me.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    bvh = BVHTree.FromPolygons(vs, fs)
    w, d, h = root['dims']
    xs = [-1.78 + (i - 1) * w / 3 for i in range(3)]
    shelves = []
    for cx in xs:
        z = h - 0.02
        levels = []
        while z > 0.05:
            hit = bvh.ray_cast(Vector((cx, NN - 0.2, z)), Vector((0, 0, -1)))
            if hit[0] is None: break
            levels.append(hit[0].z)
            z = hit[0].z - 0.03
        shelves.append((cx, levels))
    k = 0
    for ci, (cx, levels) in enumerate(shelves):
        for li, zl in enumerate(levels[:-1] if len(levels) > 3 else levels):
            k += 1
            x0, x1 = cx - w / 6 + 0.03, cx + w / 6 - 0.03
            kind = (ci * 3 + li) % 5
            if li == len(levels) - 1:
                continue      # bottom row has fabric boxes
            if kind in (0, 2, 3):
                books_in_cubby(x0, x1 if kind != 3 else (x0 + x1) / 2 + 0.02, NN - 0.22, zl, 0.25, seed=k)
                if kind == 3:
                    r2, o2 = place('ceramic_vase_03' if k % 2 else 'jug_01', ((x0 + x1) / 2 + 0.08, NN - 0.22, zl), rotz=R(20), scale=0.55)
            elif kind == 1:
                place('antique_ceramic_vase_01', ((x0 + x1) / 2, NN - 0.22, zl), scale=0.6)
            else:
                place('standing_picture_frame_01', ((x0 + x1) / 2, NN - 0.22, zl), rotz=R(8), scale=0.95)
    return root


def build_room():
    m = room4.M()
    info = {}
    # floor, rug, walls (v4 foam clay)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, (S + NN) / 2, 0)); f = bpy.context.active_object; f.name = 'floor'
    f.scale = (W1 - W0, NN - S, 1); f.data.materials.append(m['floor'])
    for i, (r, mat) in enumerate(((1.45, m['rug']), (1.2, m['rug2']), (1.03, m['rug']), (0.6, m['rug2']), (0.44, m['rug']))):
        cyl(f'rug{i}', r, 0.012 + i * 0.001, mat, loc=(0, 0.1, 0.006 + i * 0.0005), verts=128, bevel=0.004)
    win = (0.1, 2.1, 0.85, 2.25)
    wm = m['wall']

    def wall_piece(name, x0, x1, z0, z1, y, mat, thick=0.12):
        rounded_box(name, (x1 - x0, thick, z1 - z0), 0.01, mat, loc=((x0 + x1) / 2, y, (z0 + z1) / 2), segs=1)
    wall_piece('ws_l', W0, win[0], 0, H, S, wm); wall_piece('ws_r', win[1], W1, 0, H, S, wm)
    wall_piece('ws_b', win[0], win[1], 0, win[2], S, wm); wall_piece('ws_t', win[0], win[1], win[3], H, S, wm)
    wall_piece('wn', W0, W1, 0, H, NN, m['wall2'])
    rounded_box('ww', (0.12, NN - S, H), 0.01, wm, loc=(W0, (S + NN) / 2, H / 2), segs=1)
    rounded_box('we', (0.12, NN - S, H), 0.01, wm, loc=(W1, (S + NN) / 2, H / 2), segs=1)
    rounded_box('ceil', (W1 - W0, NN - S, 0.1), 0.01, m['white'], loc=(0, (S + NN) / 2, H + 0.05), segs=1)
    for y in (S + 0.07, NN - 0.07):
        rounded_box('skirt', (W1 - W0, 0.02, 0.08), 0.005, m['white'], loc=(0, y, 0.04), segs=1)
    room4.window_and_city(m, win[0], win[1], win[2], win[3], S)
    couch(m)
    # coffee table + things on it
    ct, _ = place('coffee_table_round_01', (0, 0.28, 0), scale=0.85)
    tz = top_z(ct)
    place('wooden_candlestick', (0.26, 0.42, tz), scale=0.9)
    cz = tz + 0.22 * 0.9
    cyl('candle', 0.022, 0.07, m['cream'], loc=(0.26, 0.42, cz + 0.02))
    sphere('flame', 0.008, m['flame'], loc=(0.26, 0.42, cz + 0.068), scale=(0.8, 0.8, 1.9))
    info['candle'] = point_light('candle_l', (0.26, 0.42, cz + 0.085), '#ffa347', 5, radius=0.01)
    jr, _ = place('jug_01', (-0.22, 0.38, tz), rotz=R(-30), scale=0.8)
    room4.flowers(m, (-0.22, 0.38, tz + 0.13), scale=0.65, n=6, seed=4)
    rounded_box('remote', (0.05, 0.18, 0.02), 0.008, m['black'], loc=(0.05, 0.05, tz + 0.012), rot=(0, 0, R(20)))
    # TV console + TV
    rounded_box('tv_console', (1.9, 0.42, 0.45), 0.03, m['wood'], loc=(0, NN - 0.27, 0.25))
    for sx in (-0.6, 0.0, 0.6):
        rounded_box('drawer', (0.55, 0.02, 0.3), 0.01, m['woodd'], loc=(sx, NN - 0.48, 0.25))
        cyl('knob', 0.012, 0.02, m['brass'], loc=(sx, NN - 0.495, 0.3), rot=(R(90), 0, 0))
    tvw, tvh, tvz = 1.46, 0.84, 1.25
    rounded_box('tv_body', (tvw + 0.03, 0.05, tvh + 0.03), 0.008, m['black'], loc=(0, NN - 0.12, tvz))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, NN - 0.147, tvz), rotation=(R(90), 0, R(180)))
    scr = bpy.context.active_object; scr.name = 'tv_screen'; scr.scale = (tvw, tvh, 1)
    scr.data.materials.append(room4.tv_screen_material())
    tvl = area_light('tv_light', (0, NN - 0.2, tvz), (R(90), 0, 0), tvw, '#bcd2ff', 60, size_y=tvh)
    place('potted_plant_04', (-0.72, NN - 0.28, 0.475), scale=0.9)
    place('ceramic_vase_01', (0.62, NN - 0.28, 0.475), scale=0.55)
    place('ceramic_vase_03', (0.78, NN - 0.26, 0.475), scale=0.45)
    room4.fairy_lights(m, Vector((-1.2, NN - 0.14, 2.15)), Vector((1.2, NN - 0.14, 2.15)), n=30, sag=0.18)
    # bookcase left of the TV
    bookcase(m)
    # cabinet right of the TV with a lamp, clock and a plant
    cab, _ = place('painted_wooden_cabinet', (1.78, NN - 0.34, 0))
    cz = top_z(cab)
    lamp, lobs = place('vintage_oil_lamp', (1.45, NN - 0.3, cz), scale=0.9)
    for o in lobs:
        if o.name.endswith('flame'):
            o.data.materials.clear(); o.data.materials.append(m['flame'])
    info['oil_lamp'] = point_light('oil_l', (1.45, NN - 0.36, cz + 0.36), '#ffb25a', 14, radius=0.02)
    place('mantel_clock_01', (1.9, NN - 0.3, cz), scale=0.9, pick=lambda n: n.startswith('mantel_clock_01'))
    place('potted_plant_02', (2.18, NN - 0.34, cz), scale=0.62)
    # west wall: chest of drawers, painting, vases
    place('vintage_wooden_drawer_01', (W0 + 0.3, 0.55, 0), rotz=R(-90))
    place('fancy_picture_frame_01', (W0 + 0.075, 0.55, 1.2), rotz=R(-90), center=True)
    place('antique_ceramic_vase_01', (W0 + 0.3, 0.3, 0.55), scale=0.7)
    pp, _ = place('planter_pot_clay', (W0 + 0.3, 0.85, 0.55), scale=0.7)
    place('fern_02', (W0 + 0.3, 0.85, 0.55 + 0.14), scale=0.55, pick=lambda n: n == 'fern_02_b')
    # couch surroundings
    st, _ = place('side_table_01', (1.52, CY + 0.08, 0), rotz=R(90))
    sz = top_z(st)
    place('standing_picture_frame_01', (1.42, CY + 0.2, sz), rotz=R(-160), scale=1.0)
    place('wooden_bowl_01', (1.62, CY - 0.02, sz), scale=0.6)
    place('potted_plant_01', (-1.62, CY - 0.28, 0))
    place('wicker_basket_02', (-1.55, CY + 0.45, 0), rotz=R(25), pick=lambda n: True)
    room4.floor_lamp(m, (1.55, -1.95, 0))
    # armchair + ottoman in the east part of the room
    ac, aobs = place('ArmChair_01', (2.3, 0.75, 0), rotz=R(125))
    for mt in mats_of(aobs):
        mats5.beadify(mt, bead_size=0.0085, mask='bright', thr=0.32)
    ot, oobs = place('Ottoman_01', (1.7, 0.2, 0), rotz=R(30))
    omat = bead('ottoman', '#d9a441', speck_color='#f0cf86', speck=0.08, bead=0.0085)
    for o in oobs:
        if o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(omat)
    place('hanging_picture_frame_02', (W1 - 0.075, 0.9, 1.55), rotz=R(90))
    place('painted_wooden_shelves', (W1 - 0.2, -0.9, 0.9), rotz=R(90))
    place('potted_plant_02', (W1 - 0.35, 2.4, 0), scale=1.0)
    place('potted_plant_01', (2.75, S + 0.45, 0), scale=1.1)
    place('modern_ceiling_lamp_01', (2.25, 0.8, H - 0.95), scale=0.9)
    room4.fairy_lights(m, Vector((-0.3, S + 0.14, 2.45)), Vector((2.5, S + 0.14, 2.45)), n=30, sag=0.12)
    rv = room4.robot_vacuum(m, (1.2, 0.9, 0), rotz=R(30))
    # lights: cosy evening
    area_light('fill_window', (1.1, S + 0.3, 1.6), (R(-90), 0, 0), 1.8, '#8fa6ff', 18, size_y=1.3).rotation_euler = (R(-90), 0, 0)
    info['key'] = area_light('key_warm', (-0.9, 0.9, 1.9), (R(58), 0, R(200)), 1.2, '#ffc58c', 230)
    area_light('key_front', (0.6, 1.6, 1.3), (R(80), 0, R(180)), 2.2, '#ffe9d6', 22)
    area_light('ceiling_soft', (0, 0.3, 2.6), (0, 0, 0), 3.5, '#ffe2c4', 6, size_y=4.0)
    area_light('lamp_rim', (1.45, -1.9, 1.55), (R(70), 0, R(35)), 0.6, '#ffbe7a', 170)
    fk = area_light('face_key', (-0.75, -0.15, 1.55), (0, 0, 0), 0.7, '#ffd2a6', 55)
    d = Vector((0.0, CY, 1.15)) - fk.location; fk.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT':
            ob.visible_camera = False
    info.update(tv_screen=scr, tv_light=tvl, robovac=rv, couch_y=CY, north=NN, south=S, tvz=tvz, tvw=tvw, tvh=tvh,
                seat_top=SEAT_TOP)
    return info
