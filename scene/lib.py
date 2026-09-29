import bpy, math, os, mathutils
from mathutils import Vector, Euler
HERE=os.path.dirname(os.path.abspath(__file__))
TEX=os.path.join(HERE,'tex')
_img={}
def img(name):
    if name not in _img:
        im=bpy.data.images.load(os.path.join(TEX,name+'.png'),check_existing=True)
        im.colorspace_settings.name='Non-Color'
        _img[name]=im
    return _img[name]

def reset():
    for coll in (bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.curves,bpy.data.armatures,bpy.data.node_groups,bpy.data.worlds,bpy.data.actions):
        for x in list(coll): coll.remove(x)
    _img.clear(); _mats.clear()

def hexcol(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    # srgb -> linear
    return tuple(((x+0.055)/1.055)**2.4 if x>0.04045 else x/12.92 for x in c)+(1.0,)

_mats={}
STYLE='bead'
def bead(name,color,speck_color=None,speck=0.12,bead=0.012,bump=1.0,rough=0.62,var=0.1,emit=None,sheen=0.25):
    if name in _mats: return _mats[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; N=nt.nodes; L=nt.links
    for n in list(N): N.remove(n)
    out=N.new('ShaderNodeOutputMaterial')
    bsdf=N.new('ShaderNodeBsdfPrincipled')
    tc=N.new('ShaderNodeTexCoord'); mp=N.new('ShaderNodeMapping')
    tile=46*bead; m['tile']=tile
    mp.inputs['Scale'].default_value=(1/tile,1/tile,1/tile)
    L.new(tc.outputs['Object'],mp.inputs['Vector'])
    th=N.new('ShaderNodeTexImage'); th.image=img('bead_h'); th.projection='BOX'; th.projection_blend=0.3; th.interpolation='Linear'
    ti=N.new('ShaderNodeTexImage'); ti.image=img('bead_id'); ti.projection='BOX'; ti.projection_blend=0.3; ti.interpolation='Closest'
    L.new(mp.outputs['Vector'],th.inputs['Vector']); L.new(mp.outputs['Vector'],ti.inputs['Vector'])
    nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=2.5
    L.new(tc.outputs['Object'],nz.inputs['Vector'])
    base=hexcol(color)
    sc=hexcol(speck_color) if speck_color else tuple(min(1,c*1.9+0.08) for c in base[:3])+(1,)
    # per-bead: speck color for a fraction of beads, value jitter for the rest
    gt=N.new('ShaderNodeMath'); gt.operation='GREATER_THAN'; gt.inputs[1].default_value=1-speck
    L.new(ti.outputs['Color'],gt.inputs[0])
    c1=N.new('ShaderNodeRGB'); c1.outputs[0].default_value=base
    c2=N.new('ShaderNodeRGB'); c2.outputs[0].default_value=sc
    mix=N.new('ShaderNodeMix'); mix.data_type='RGBA'
    L.new(gt.outputs[0],mix.inputs['Factor']); L.new(c1.outputs[0],mix.inputs['A']); L.new(c2.outputs[0],mix.inputs['B'])
    jit=N.new('ShaderNodeMapRange'); jit.inputs['To Min'].default_value=1-var; jit.inputs['To Max'].default_value=1+var*0.6
    L.new(ti.outputs['Color'],jit.inputs['Value'])
    cr=N.new('ShaderNodeMapRange'); cr.inputs['From Max'].default_value=0.55; cr.inputs['To Min'].default_value=0.28; cr.inputs['To Max'].default_value=1.0
    L.new(th.outputs['Color'],cr.inputs['Value'])
    shade=N.new('ShaderNodeMath'); shade.operation='MULTIPLY'
    L.new(jit.outputs['Result'],shade.inputs[0]); L.new(cr.outputs['Result'],shade.inputs[1])
    mul=N.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs['Factor'].default_value=1.0
    L.new(mix.outputs['Result'],mul.inputs['A']); L.new(shade.outputs['Value'],mul.inputs['B'])
    vv=N.new('ShaderNodeMix'); vv.data_type='RGBA'; vv.blend_type='OVERLAY'; vv.inputs['Factor'].default_value=0.06
    L.new(mul.outputs['Result'],vv.inputs['A']); L.new(nz.outputs['Color'],vv.inputs['B'])
    L.new(vv.outputs['Result'],bsdf.inputs['Base Color'])
    bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=bump; bp.inputs['Distance'].default_value=bead*0.45
    L.new(th.outputs['Color'],bp.inputs['Height']); L.new(bp.outputs['Normal'],bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value=rough
    bsdf.inputs['Sheen Weight'].default_value=sheen; bsdf.inputs['Sheen Roughness'].default_value=0.4
    bsdf.inputs['Specular IOR Level'].default_value=0.35
    if emit:
        bsdf.inputs['Emission Color'].default_value=hexcol(emit[0]); bsdf.inputs['Emission Strength'].default_value=emit[1]
    L.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    _mats[name]=m
    return m

def clay(name,color,rough=0.55,sss=0.0,coat=0.0,bump=0.08):
    """Smooth matte polymer clay / ceramic with a faint handmade surface."""
    if name in _mats: return _mats[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; N=nt.nodes; L=nt.links
    b=N['Principled BSDF']
    b.inputs['Base Color'].default_value=hexcol(color); b.inputs['Roughness'].default_value=rough
    b.inputs['Coat Weight'].default_value=coat; b.inputs['Coat Roughness'].default_value=0.25
    if sss>0:
        b.subsurface_method='BURLEY'
        b.inputs['Subsurface Weight'].default_value=sss*0.6; b.inputs['Subsurface Radius'].default_value=(0.012,0.005,0.004); b.inputs['Subsurface Scale'].default_value=0.5
    tc=N.new('ShaderNodeTexCoord'); nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=90; nz.inputs['Detail'].default_value=4
    L.new(tc.outputs['Object'],nz.inputs['Vector'])
    bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=bump; bp.inputs['Distance'].default_value=0.002
    L.new(nz.outputs['Fac'],bp.inputs['Height']); L.new(bp.outputs['Normal'],b.inputs['Normal'])
    _mats[name]=m
    return m

def yarn(name, color, pattern='knit_h', stitch=0.02, bump=0.8, sheen=0.7, rough=0.85, rot=0.0, aspect=1.0, var=0.08, emit=None, sss=0.0):
    """Knitted wool (style='knit') – by default the scene uses foam-clay beads."""
    if STYLE=='bead' and not name.startswith('knit_') and pattern!='felt_h':
        return bead(name,color,bead=max(0.0065,min(0.011,stitch*0.6)),bump=1.0,emit=emit)
    if STYLE=='bead' and pattern=='felt_h' and not name.startswith('knit_'):
        return clay(name,color,rough=0.6,sss=sss)
    key=name
    if key in _mats: return _mats[key]
    m=bpy.data.materials.new(name); m.use_nodes=True
    nt=m.node_tree; N=nt.nodes; L=nt.links
    for n in list(N): N.remove(n)
    out=N.new('ShaderNodeOutputMaterial'); out.location=(900,0)
    bsdf=N.new('ShaderNodeBsdfPrincipled'); bsdf.location=(600,0)
    tc=N.new('ShaderNodeTexCoord'); tc.location=(-900,0)
    mp=N.new('ShaderNodeMapping'); mp.location=(-700,0)
    # texture tile has 8 columns -> tile width = 8*stitch
    tile=8*stitch
    mp.inputs['Scale'].default_value=(1/tile,1/tile*aspect,1/tile)
    mp.inputs['Rotation'].default_value=(0,0,rot)
    L.new(tc.outputs['Object'],mp.inputs['Vector'])
    t=N.new('ShaderNodeTexImage'); t.location=(-450,0); t.image=img(pattern)
    t.projection='BOX'; t.projection_blend=0.25; t.interpolation='Linear'
    L.new(mp.outputs['Vector'],t.inputs['Vector'])
    # colour variation
    nz=N.new('ShaderNodeTexNoise'); nz.location=(-450,-300); nz.inputs['Scale'].default_value=3.0
    L.new(tc.outputs['Object'],nz.inputs['Vector'])
    base=hexcol(color)
    rgb=N.new('ShaderNodeRGB'); rgb.outputs[0].default_value=base; rgb.location=(-200,250)
    # crevice darkening
    cr=N.new('ShaderNodeMapRange'); cr.location=(-200,0)
    cr.inputs['From Min'].default_value=0.0; cr.inputs['From Max'].default_value=0.75
    cr.inputs['To Min'].default_value=0.35; cr.inputs['To Max'].default_value=1.0
    L.new(t.outputs['Color'],cr.inputs['Value'])
    mul=N.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.location=(100,150)
    mul.inputs['Factor'].default_value=1.0
    L.new(rgb.outputs[0],mul.inputs['A'])
    L.new(cr.outputs['Result'],mul.inputs['B'])
    vv=N.new('ShaderNodeMix'); vv.data_type='RGBA'; vv.blend_type='OVERLAY'; vv.location=(300,150)
    vv.inputs['Factor'].default_value=var
    L.new(mul.outputs['Result'],vv.inputs['A']); L.new(nz.outputs['Color'],vv.inputs['B'])
    L.new(vv.outputs['Result'],bsdf.inputs['Base Color'])
    bp=N.new('ShaderNodeBump'); bp.location=(300,-200)
    bp.inputs['Strength'].default_value=bump; bp.inputs['Distance'].default_value=stitch*0.25
    L.new(t.outputs['Color'],bp.inputs['Height'])
    L.new(bp.outputs['Normal'],bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value=rough
    bsdf.inputs['Sheen Weight'].default_value=sheen
    bsdf.inputs['Sheen Roughness'].default_value=0.35
    bsdf.inputs['Sheen Tint'].default_value=tuple(min(1,0.45+c*0.9) for c in base[:3])+(1,)
    if sss>0:
        bsdf.inputs['Subsurface Weight'].default_value=sss
        bsdf.inputs['Subsurface Radius'].default_value=(0.01,0.004,0.003)
    if emit:
        bsdf.inputs['Emission Color'].default_value=hexcol(emit[0]); bsdf.inputs['Emission Strength'].default_value=emit[1]
    L.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    _mats[key]=m
    return m

def simple(name,color,rough=0.5,metal=0.0,emit=None,alpha=None,trans=0.0,ior=1.45,coat=0.0):
    if name in _mats: return _mats[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=hexcol(color)
    b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    b.inputs['Transmission Weight'].default_value=trans; b.inputs['IOR'].default_value=ior
    b.inputs['Coat Weight'].default_value=coat
    if emit:
        b.inputs['Emission Color'].default_value=hexcol(emit[0]); b.inputs['Emission Strength'].default_value=emit[1]
    if alpha is not None: b.inputs['Alpha'].default_value=alpha
    _mats[name]=m
    return m

def emissive(name,color,strength):
    if name in _mats: return _mats[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    N=m.node_tree.nodes; L=m.node_tree.links
    for n in list(N): N.remove(n)
    o=N.new('ShaderNodeOutputMaterial'); e=N.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=hexcol(color); e.inputs['Strength'].default_value=strength
    L.new(e.outputs[0],o.inputs[0]); _mats[name]=m; return m

def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob); return ob

def mesh_obj(name, verts, faces, mat=None, smooth=True, subsurf=0):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); link(ob)
    if smooth:
        for p in me.polygons: p.use_smooth=True
    if mat: me.materials.append(mat)
    if subsurf:
        md=ob.modifiers.new('sub','SUBSURF'); md.levels=subsurf; md.render_levels=subsurf
    return ob

def rounded_box(name, size, radius, mat=None, loc=(0,0,0), rot=(0,0,0), segs=4):
    """Box with bevelled edges (cushion-like). size = full dims."""
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    ob=bpy.context.active_object; ob.name=name
    ob.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=ob.modifiers.new('bev','BEVEL'); b.width=radius; b.segments=segs; b.limit_method='NONE'
    s=ob.modifiers.new('sub','SUBSURF'); s.levels=1; s.render_levels=1
    for p in ob.data.polygons: p.use_smooth=True
    if mat: ob.data.materials.append(mat)
    return ob

def cushion(name,size,mat,loc=(0,0,0),rot=(0,0,0),puff=0.35):
    """Pillow: subdivided cube squashed + inflated."""
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    ob=bpy.context.active_object; ob.name=name
    me=ob.data
    import bmesh
    bm=bmesh.new(); bm.from_mesh(me)
    bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=6,use_grid_fill=True)
    for v in bm.verts:
        x,y,z=v.co
        # inflate: push toward sphere
        l=max(abs(x),abs(y),abs(z))*2
        v.co=Vector((x*size[0],y*size[1],z*size[2]))
        f=(1-(2*x)**2)*(1-(2*y)**2)
        v.co.z*= (1+puff*f)
    bm.to_mesh(me); bm.free()
    s=ob.modifiers.new('sub','SUBSURF'); s.levels=1; s.render_levels=2
    for p in me.polygons: p.use_smooth=True
    ob.data.materials.append(mat)
    return ob

def cyl(name,r,h,mat=None,loc=(0,0,0),rot=(0,0,0),verts=48,bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=h,location=loc,rotation=rot,vertices=verts)
    ob=bpy.context.active_object; ob.name=name
    if bevel:
        b=ob.modifiers.new('bev','BEVEL'); b.width=bevel; b.segments=3
    for p in ob.data.polygons: p.use_smooth=True
    if mat: ob.data.materials.append(mat)
    return ob

def sphere(name,r,mat=None,loc=(0,0,0),scale=(1,1,1),seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=loc,segments=seg,ring_count=seg//2)
    ob=bpy.context.active_object; ob.name=name; ob.scale=scale
    for p in ob.data.polygons: p.use_smooth=True
    if mat: ob.data.materials.append(mat)
    return ob

def camera(name='Cam',loc=(0,-5,1.5),target=(0,0,1),lens=35,fstop=2.8,focus=None):
    cd=bpy.data.cameras.new(name); cd.lens=lens; cd.sensor_width=36
    cam=bpy.data.objects.new(name,cd); link(cam); cam.location=loc
    tgt=bpy.data.objects.new(name+'_tgt',None); link(tgt); tgt.location=target
    c=cam.constraints.new('TRACK_TO'); c.target=tgt; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
    cd.dof.use_dof=True; cd.dof.aperture_fstop=fstop
    foc=bpy.data.objects.new(name+'_focus',None); link(foc); foc.location=focus or target
    cd.dof.focus_object=foc
    bpy.context.scene.camera=cam
    return cam,tgt,foc

def area_light(name,loc,rot,size,color,power,shape='RECTANGLE',size_y=None):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=power; ld.color=hexcol(color)[:3]
    ld.shape=shape; ld.size=size; ld.size_y=size_y or size
    ob=bpy.data.objects.new(name,ld); link(ob); ob.location=loc; ob.rotation_euler=rot
    return ob

def point_light(name,loc,color,power,radius=0.05):
    ld=bpy.data.lights.new(name,'POINT'); ld.energy=power; ld.color=hexcol(color)[:3]; ld.shadow_soft_size=radius
    ob=bpy.data.objects.new(name,ld); link(ob); ob.location=loc; return ob

def setup_render(res=(1920,1080),samples=64,pct=100,out='out/frame',fps=24, threads=0):
    sc=bpy.context.scene
    sc.render.engine='CYCLES'
    sc.cycles.device='CPU'
    sc.cycles.samples=samples
    sc.cycles.use_adaptive_sampling=True
    sc.cycles.use_denoising=True
    try: sc.cycles.denoiser='OPENIMAGEDENOISE'
    except: pass
    sc.cycles.max_bounces=5; sc.cycles.diffuse_bounces=2; sc.cycles.glossy_bounces=1
    sc.cycles.transmission_bounces=4; sc.cycles.transparent_max_bounces=8; sc.cycles.volume_bounces=0
    sc.cycles.use_fast_gi=False
    sc.cycles.adaptive_threshold=0.04
    sc.cycles.caustics_reflective=False; sc.cycles.caustics_refractive=False
    sc.cycles.blur_glossy=1.0
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.resolution_percentage=pct
    sc.render.fps=fps
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_depth='8'
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
    sc.render.filepath=out
    sc.render.film_transparent=False
    if threads:
        sc.render.threads_mode='FIXED'; sc.render.threads=threads
    return sc

def world(color='#0b0d18',strength=0.3):
    w=bpy.data.worlds.new('W'); bpy.context.scene.world=w; w.use_nodes=True
    bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=hexcol(color); bg.inputs[1].default_value=strength
