"""Render frames of intro v5.
usage: python3 render5.py FRAMES PCT SPP OUTDIR   (FRAMES: '1,5,9' or '1-420' or '1-420:2')"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]


def parse(spec):
    out = []
    for part in spec.split(','):
        if not part: continue
        if '-' in part:
            rng, _, step = part.partition(':')
            a, b = rng.split('-'); out += list(range(int(a), int(b) + 1, int(step or 1)))
        else:
            out.append(int(part))
    return out


frames = parse(args[0]); pct = int(args[1]); spp = int(args[2]); outdir = args[3]
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
import anim5
from lib import setup_render
import bpy
sc = setup_render((1920, 1080), samples=spp, pct=pct, out=outdir + '/f_')
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.015
sc.view_settings.look = 'AgX - Punchy'
for n, e in (('lamp_light', 60), ('lamp_down', 80)):
    if n in bpy.data.lights: bpy.data.lights[n].energy = e
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 95
print('scene ready', round(time.time() - t0, 1), flush=True)
for f in frames:
    p = f'{outdir}/f_{f:04d}.jpg'
    if os.path.exists(p): continue
    t = time.time(); sc.frame_set(f); sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print(f'FRAME {f} {time.time() - t:.1f}s', flush=True)
print('ALL DONE', round(time.time() - t0, 1), flush=True)
os._exit(0)
