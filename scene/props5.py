"""Hand props for intro v5: stout pint (no branding) and a wooden bowl of popcorn."""
import bpy, math, random, bmesh
from mathutils import Vector, Matrix
from lib import *
import props4, room5
R = math.radians


def pint():
    return props4.pint('pint')


def popcorn_bowl():
    root = bpy.data.objects.new('bowl', None); link(root)
    br, obs = room5.place('wooden_bowl_01', (0, 0, 0), scale=0.72)
    br.parent = root
    pm = [bead('pop1', '#f4e6bd', speck_color='#fff6dc', speck=0.2, bead=0.0035, bump=0.6),
          bead('pop2', '#edd394', speck_color='#f8e7b5', speck=0.2, bead=0.0035, bump=0.6)]
    rnd = random.Random(4)
    for mi in range(2):
        bm = bmesh.new()
        for i in range(120):
            a = rnd.uniform(0, 2 * math.pi); r = math.sqrt(rnd.random()) * 0.095
            h = 0.035 + 0.035 * (1 - (r / 0.1) ** 2) + rnd.uniform(-0.006, 0.01)
            c = Vector((r * math.cos(a), r * math.sin(a), h))
            for k in range(4):
                if (i + k) % 2 != mi: continue
                rad = rnd.uniform(0.009, 0.013) if k == 0 else rnd.uniform(0.005, 0.008)
                off = Vector((0, 0, 0)) if k == 0 else Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1))) * 0.009
                M = Matrix.Translation(c + off) @ Matrix.Diagonal((1, rnd.uniform(0.7, 1), rnd.uniform(0.7, 1), 1))
                bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=rad, matrix=M)
        me = bpy.data.meshes.new(f'pop{mi}'); bm.to_mesh(me); bm.free()
        for pl in me.polygons: pl.use_smooth = True
        ob = bpy.data.objects.new(f'pop{mi}', me); link(ob); me.materials.append(pm[mi]); ob.parent = root
    return root
