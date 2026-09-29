import bpy, math, random
from mathutils import Vector
from lib import *
R=math.radians

def pint(name='pint'):
    """Stout pint (no branding): glass, dark body, creamy knitted head. Origin at glass bottom centre."""
    root=bpy.data.objects.new(name,None); link(root)
    glassm=bpy.data.materials.new('pintglass'); glassm.use_nodes=True
    b=glassm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(1,1,1,1); b.inputs['Transmission Weight'].default_value=1.0
    b.inputs['Roughness'].default_value=0.02; b.inputs['IOR'].default_value=1.45
    # tulip-ish pint via lathe
    prof=[(0.030,0.0),(0.032,0.01),(0.036,0.06),(0.040,0.11),(0.043,0.135),(0.041,0.155),(0.040,0.16)]
    def lathe(nm,prof,mat,seg=48,cap_bottom=True):
        verts=[];faces=[]
        for i,(r,z) in enumerate(prof):
            for k in range(seg):
                a=2*math.pi*k/seg; verts.append((r*math.cos(a),r*math.sin(a),z))
        for i in range(len(prof)-1):
            for k in range(seg):
                a=i*seg+k; b_=i*seg+(k+1)%seg
                faces.append((a,b_,b_+seg,a+seg))
        if cap_bottom: faces.append(tuple(range(seg))[::-1])
        ob=mesh_obj(nm,verts,faces,mat)
        return ob
    g=lathe(name+'_glass',prof,glassm)
    sol=g.modifiers.new('s','SOLIDIFY'); sol.thickness=0.0025
    beer=[(r-0.004,z) for r,z in prof[:5]]
    beer[0]=(0.026,0.004)
    liquid=lathe(name+'_beer',beer,simple('stout','#120905',rough=0.1,coat=0.3))
    # top cap of liquid is the foam
    foam=cyl(name+'_foam',0.039,0.022,yarn('foam','#efe2c6',pattern='felt_h',stitch=0.01,bump=0.5),loc=(0,0,0.143),bevel=0.006)
    for o in (g,liquid,foam): o.parent=root
    return root

def popcorn_bowl(name='bowl'):
    root=bpy.data.objects.new(name,None); link(root)
    stripe_r=yarn('bowl_r','#c8202c',pattern='rib_h',stitch=0.008)
    stripe_w=yarn('bowl_w','#efe6d6',pattern='rib_h',stitch=0.008)
    # knitted bowl: hemisphere shell with stripes as two materials by angle
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=0.14)
    bw=bpy.context.active_object; bw.name=name+'_shell'
    import bmesh
    bm=bmesh.new(); bm.from_mesh(bw.data)
    for v in [v for v in bm.verts if v.co.z>0.02]: bm.verts.remove(v)
    bm.to_mesh(bw.data); bm.free()
    bw.data.materials.append(stripe_r); bw.data.materials.append(stripe_w)
    for p in bw.data.polygons:
        a=math.atan2(p.center.y,p.center.x)
        p.material_index=int((a+math.pi)/(2*math.pi)*12)%2
        p.use_smooth=True
    bw.scale=(1,1,0.62)
    s=bw.modifiers.new('s','SOLIDIFY'); s.thickness=0.01
    bw.location=(0,0,0.087)
    bw.parent=root
    # popcorn: felt puffs, clustered
    pm=[yarn('pop1','#f3e3b3',pattern='felt_h',stitch=0.01,bump=0.6),yarn('pop2','#ecd08a',pattern='felt_h',stitch=0.01,bump=0.6)]
    rnd=random.Random(4)
    import bmesh
    from mathutils import Matrix
    for mi in range(2):
        bm=bmesh.new()
        for i in range(140):
            a=rnd.uniform(0,2*math.pi); r=math.sqrt(rnd.random())*0.125
            h=0.075+0.05*(1-(r/0.13)**2)+rnd.uniform(-0.01,0.015)
            c=Vector((r*math.cos(a),r*math.sin(a),h))
            for k in range(4):
                rad=rnd.uniform(0.011,0.017) if k==0 else rnd.uniform(0.006,0.01)
                off=Vector((0,0,0)) if k==0 else Vector((rnd.uniform(-1,1),rnd.uniform(-1,1),rnd.uniform(-0.5,1)))*0.011
                if (i+k)%2!=mi: continue
                M=Matrix.Translation(c+off)@Matrix.Diagonal((1,rnd.uniform(0.7,1),rnd.uniform(0.7,1),1))
                bmesh.ops.create_uvsphere(bm,u_segments=10,v_segments=6,radius=rad,matrix=M)
        me=bpy.data.meshes.new(f'{name}_pop{mi}'); bm.to_mesh(me); bm.free()
        for pl in me.polygons: pl.use_smooth=True
        ob=bpy.data.objects.new(f'{name}_pop{mi}',me); link(ob); me.materials.append(pm[mi]); ob.parent=root
    return root
