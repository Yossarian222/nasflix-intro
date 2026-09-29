"""Extra materials for intro v5 (skin, eyes, gradient beads)."""
import bpy, os, sys
from lib import hexcol, img, bead, clay, _mats

MPFB_TEX = None
def mpfb_tex(name):
    """Greyscale UV masks shipped with MPFB (lips, eyelids...)."""
    global MPFB_TEX
    if MPFB_TEX is None:
        MPFB_TEX = os.path.join(os.path.dirname(sys.modules['bl_ext.user_default.mpfb'].__file__), 'data', 'textures')
    im = bpy.data.images.load(os.path.join(MPFB_TEX, name), check_existing=True)
    im.colorspace_settings.name = 'Non-Color'
    return im


def skin(name, color, lips, blush_col='#e8868c', blush=0.4, stubble=0.0, sss=0.2):
    """Smooth porcelain/polymer-clay skin. Attributes 'blush' and 'stubble' come from the mesh.
    Node 'BlushAmt' (Value) can be animated."""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.42
    b.inputs['Coat Weight'].default_value = 0.12; b.inputs['Coat Roughness'].default_value = 0.32
    b.inputs['Sheen Weight'].default_value = 0.08
    b.subsurface_method = 'RANDOM_WALK'
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.42, 0.28)
    b.inputs['Subsurface Scale'].default_value = 0.006
    base = N.new('ShaderNodeRGB'); base.outputs[0].default_value = hexcol(color)
    # blush
    ab = N.new('ShaderNodeAttribute'); ab.attribute_name = 'blush'
    amt = N.new('ShaderNodeValue'); amt.name = 'BlushAmt'; amt.outputs[0].default_value = blush
    mb = N.new('ShaderNodeMath'); mb.operation = 'MULTIPLY'; mb.use_clamp = True
    L.new(ab.outputs['Fac'], mb.inputs[0]); L.new(amt.outputs[0], mb.inputs[1])
    bc = N.new('ShaderNodeRGB'); bc.outputs[0].default_value = hexcol(blush_col)
    mix1 = N.new('ShaderNodeMix'); mix1.data_type = 'RGBA'
    L.new(mb.outputs[0], mix1.inputs['Factor']); L.new(base.outputs[0], mix1.inputs['A']); L.new(bc.outputs[0], mix1.inputs['B'])
    col = mix1.outputs['Result']
    # stubble: fine dark speckles in the lower face
    if stubble > 0:
        st = N.new('ShaderNodeAttribute'); st.attribute_name = 'stubble'
        tc = N.new('ShaderNodeTexCoord')
        vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 900.0
        L.new(tc.outputs['Object'], vo.inputs['Vector'])
        dots = N.new('ShaderNodeMapRange'); dots.inputs['From Min'].default_value = 0.0; dots.inputs['From Max'].default_value = 0.28
        dots.inputs['To Min'].default_value = 1.0; dots.inputs['To Max'].default_value = 0.0
        L.new(vo.outputs['Distance'], dots.inputs['Value'])
        f = N.new('ShaderNodeMath'); f.operation = 'MULTIPLY'; f.use_clamp = True
        L.new(dots.outputs['Result'], f.inputs[0]); L.new(st.outputs['Fac'], f.inputs[1])
        f2 = N.new('ShaderNodeMath'); f2.operation = 'MULTIPLY'; f2.inputs[1].default_value = stubble
        L.new(f.outputs[0], f2.inputs[0])
        sc = N.new('ShaderNodeRGB'); sc.outputs[0].default_value = hexcol('#6b5144')
        mix2 = N.new('ShaderNodeMix'); mix2.data_type = 'RGBA'
        L.new(f2.outputs[0], mix2.inputs['Factor']); L.new(col, mix2.inputs['A']); L.new(sc.outputs[0], mix2.inputs['B'])
        col = mix2.outputs['Result']
    # lips from the MPFB UV mask
    uv = N.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'
    lt = N.new('ShaderNodeTexImage'); lt.image = mpfb_tex('mpfb_lips.jpg')
    L.new(uv.outputs['UV'], lt.inputs['Vector'])
    lm = N.new('ShaderNodeMapRange'); lm.inputs['From Min'].default_value = 0.15; lm.inputs['From Max'].default_value = 0.8
    lm.inputs['To Max'].default_value = 0.85
    L.new(lt.outputs['Color'], lm.inputs['Value'])
    lc = N.new('ShaderNodeRGB'); lc.outputs[0].default_value = hexcol(lips)
    mix3 = N.new('ShaderNodeMix'); mix3.data_type = 'RGBA'
    L.new(lm.outputs['Result'], mix3.inputs['Factor']); L.new(col, mix3.inputs['A']); L.new(lc.outputs[0], mix3.inputs['B'])
    col = mix3.outputs['Result']
    # inside of the mouth: dark
    it = N.new('ShaderNodeTexImage'); it.image = mpfb_tex('mpfb_inside-mouth.jpg')
    L.new(uv.outputs['UV'], it.inputs['Vector'])
    ic = N.new('ShaderNodeRGB'); ic.outputs[0].default_value = hexcol('#3a1d1f')
    mix4 = N.new('ShaderNodeMix'); mix4.data_type = 'RGBA'
    L.new(it.outputs['Color'], mix4.inputs['Factor']); L.new(col, mix4.inputs['A']); L.new(ic.outputs[0], mix4.inputs['B'])
    L.new(mix4.outputs['Result'], b.inputs['Base Color'])
    # faint hand-made surface
    tc2 = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 140; nz.inputs['Detail'].default_value = 3
    L.new(tc2.outputs['Object'], nz.inputs['Vector'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.035; bp.inputs['Distance'].default_value = 0.001
    L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    _mats[name] = m
    return m


def eye(name, iris, r):
    """Glossy eyeball; iris/pupil on the local -Y pole (object space, radius r)."""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    t = N.new('ShaderNodeMath'); t.operation = 'MULTIPLY'; t.inputs[1].default_value = -1.0 / r
    L.new(sep.outputs['Y'], t.inputs[0])
    ramp = N.new('ShaderNodeValToRGB'); L.new(t.outputs[0], ramp.inputs['Fac'])
    ir = hexcol(iris); dark = tuple(c * 0.35 for c in ir[:3]) + (1,); light = tuple(min(1, c * 1.35 + 0.05) for c in ir[:3]) + (1,)
    scl = hexcol('#f2ede4')
    E = ramp.color_ramp.elements
    E[0].position = 0.0; E[0].color = scl
    E[1].position = 1.0; E[1].color = hexcol('#050506')
    for pos, c in ((0.85, scl), (0.858, dark), (0.875, ir), (0.945, light), (0.952, hexcol('#050506'))):
        e = E.new(pos); e.color = c
    L.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02
    _mats[name] = m
    return m


def bead_grad(name, c0, c1, attr='hairT', speck=0.14, bead_size=0.006, bump=1.0, rough=0.62):
    """Bead material whose colour runs from c0 to c1 along a mesh attribute (0..1)."""
    if name in _mats: return _mats[name]
    m = bead(name + '_tmp', c0, speck=speck, bead=bead_size, bump=bump, rough=rough).copy()
    m.name = name
    N = m.node_tree.nodes; L = m.node_tree.links
    rgb = [n for n in N if n.type == 'RGB']   # [base, speck]
    a = N.new('ShaderNodeAttribute'); a.attribute_name = attr
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = hexcol(c0); ramp.color_ramp.elements[1].color = hexcol(c1)
    ramp.color_ramp.elements[0].position = 0.25
    L.new(a.outputs['Fac'], ramp.inputs['Fac'])
    for lk in list(L):
        if lk.from_node == rgb[0]:
            L.new(ramp.outputs['Color'], lk.to_socket)
    _mats[name] = m
    return m


def beadify(m, bead_size=0.008, mask=None, thr=0.45, rough=0.64, sheen=0.3, var=0.12, bump=1.0):
    """Turn an existing (textured) material into foam clay: keeps its colours/pattern, adds the bead
    relief and per-bead colour jitter. mask: None (everywhere), 'bright' or 'dark' (by luminance)."""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    bc = b.inputs['Base Color']
    if bc.is_linked:
        src = bc.links[0].from_socket
    else:
        rgb = N.new('ShaderNodeRGB'); rgb.outputs[0].default_value = bc.default_value; src = rgb.outputs[0]
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); tile = 46 * bead_size
    mp.inputs['Scale'].default_value = (1 / tile, 1 / tile, 1 / tile)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    th = N.new('ShaderNodeTexImage'); th.image = img('bead_h'); th.projection = 'BOX'; th.projection_blend = 0.3
    ti = N.new('ShaderNodeTexImage'); ti.image = img('bead_id'); ti.projection = 'BOX'; ti.projection_blend = 0.3
    ti.interpolation = 'Closest'
    L.new(mp.outputs['Vector'], th.inputs['Vector']); L.new(mp.outputs['Vector'], ti.inputs['Vector'])
    cr = N.new('ShaderNodeMapRange'); cr.inputs['From Max'].default_value = 0.55
    cr.inputs['To Min'].default_value = 0.32; cr.inputs['To Max'].default_value = 1.0
    L.new(th.outputs['Color'], cr.inputs['Value'])
    jit = N.new('ShaderNodeMapRange'); jit.inputs['To Min'].default_value = 1 - var; jit.inputs['To Max'].default_value = 1 + var * 0.6
    L.new(ti.outputs['Color'], jit.inputs['Value'])
    sh = N.new('ShaderNodeMath'); sh.operation = 'MULTIPLY'
    L.new(cr.outputs['Result'], sh.inputs[0]); L.new(jit.outputs['Result'], sh.inputs[1])
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    L.new(src, mul.inputs['A']); L.new(sh.outputs['Value'], mul.inputs['B'])
    if mask is None:
        mk = N.new('ShaderNodeValue'); mk.outputs[0].default_value = 1.0; msk = mk.outputs[0]
    else:
        bw = N.new('ShaderNodeRGBToBW'); L.new(src, bw.inputs['Color'])
        mr = N.new('ShaderNodeMapRange')
        lo, hi = (thr - 0.05, thr + 0.05)
        mr.inputs['From Min'].default_value = lo; mr.inputs['From Max'].default_value = hi
        if mask == 'dark':
            mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        L.new(bw.outputs['Val'], mr.inputs['Value']); msk = mr.outputs['Result']
    fin = N.new('ShaderNodeMix'); fin.data_type = 'RGBA'
    L.new(msk, fin.inputs['Factor']); L.new(src, fin.inputs['A']); L.new(mul.outputs['Result'], fin.inputs['B'])
    L.new(fin.outputs['Result'], bc)
    bp = N.new('ShaderNodeBump'); bp.inputs['Distance'].default_value = bead_size * 0.45
    sm = N.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = bump
    L.new(msk, sm.inputs[0]); L.new(sm.outputs[0], bp.inputs['Strength'])
    L.new(th.outputs['Color'], bp.inputs['Height'])
    nin = b.inputs['Normal']
    if nin.is_linked:
        L.new(nin.links[0].from_socket, bp.inputs['Normal'])
    L.new(bp.outputs['Normal'], nin)
    ri = b.inputs['Roughness']
    if ri.is_linked:
        rs = ri.links[0].from_socket
    else:
        rv = N.new('ShaderNodeValue'); rv.outputs[0].default_value = ri.default_value; rs = rv.outputs[0]
    rm = N.new('ShaderNodeMix'); rm.data_type = 'FLOAT'
    L.new(msk, rm.inputs['Factor']); L.new(rs, rm.inputs['A']); rm.inputs['B'].default_value = rough
    L.new(rm.outputs['Result'], ri)
    sw = N.new('ShaderNodeMath'); sw.operation = 'MULTIPLY'; sw.inputs[1].default_value = sheen
    L.new(msk, sw.inputs[0]); L.new(sw.outputs[0], b.inputs['Sheen Weight'])
    b.inputs['Sheen Roughness'].default_value = 0.4
    return m


def pet_eye(name, iris, r):
    """Animal eye: large iris, little white."""
    if name in _mats: return _mats[name]
    m = eye(name + '_base', iris, r).copy(); m.name = name
    ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    E = ramp.color_ramp.elements
    ir = hexcol(iris)
    dark = tuple(c * 0.3 for c in ir[:3]) + (1,)
    while len(E) > 2: E.remove(E[1])
    E[0].position = 0.0; E[0].color = hexcol('#2a2420')
    E[1].position = 1.0; E[1].color = hexcol('#030304')
    for pos, c in ((0.5, hexcol('#2a2420')), (0.56, dark), (0.62, ir), (0.86, tuple(min(1, c * 1.25) for c in ir[:3]) + (1,)), (0.875, hexcol('#030304'))):
        e = E.new(pos); e.color = c
    _mats[name] = m
    return m
