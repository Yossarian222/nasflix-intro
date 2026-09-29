import bpy, math, random, bmesh, os
from mathutils import Vector, Euler, Matrix
from lib import *
R=math.radians

# ---------------------------------------------------------------- materials
def M():
    return dict(
        couch=bead('couch','#a8141f',speck_color='#d8434b',speck=0.12,bead=0.0095),
        couch2=bead('couch2','#8c111b',speck_color='#c43a42',speck=0.1,bead=0.0095),
        wall=bead('wall','#d8a88a',speck_color='#f3dcc8',speck=0.22,bead=0.011),
        wall2=bead('wall2','#7d98c2',speck_color='#a9bcdb',speck=0.1,bead=0.011),
        floor=bead('floor','#dccab2',speck_color='#f4e9d8',speck=0.15,bead=0.005),
        rug=bead('rug','#e9b7b5',speck_color='#fbe3df',speck=0.25,bead=0.008),
        rug2=bead('rug2','#8aa3c9',speck_color='#d2def0',speck=0.2,bead=0.008),
        wood=clay('wood','#b07a52',rough=0.6,bump=0.3),
        woodd=clay('woodd','#7a5236',rough=0.6,bump=0.3),
        cream=bead('cream','#efe3cf',speck_color='#ffffff',speck=0.2,bead=0.01),
        mustard=bead('mustard','#e0a63c',speck_color='#f7d88f',speck=0.2,bead=0.01),
        sage=bead('sage','#9fb08e',speck_color='#dbe4cf',speck=0.2,bead=0.012),
        white=clay('whiteclay','#efe9e0',rough=0.55),
        black=clay('blackclay','#1c1b1f',rough=0.35,coat=0.4),
        grey=clay('greyclay','#6c6f78',rough=0.5),
        green=bead('leaf','#6f9160',speck_color='#b5cc9c',speck=0.2,bead=0.007),
        green2=bead('leaf2','#86a56e',speck_color='#c6d9ae',speck=0.2,bead=0.007),
        terracotta=clay('terra','#c0714b',rough=0.75,bump=0.25),
        shade=bead('shade','#f4e2c6',speck_color='#ffffff',speck=0.2,bead=0.008),
        metal=simple('metal','#2a2a2a',rough=0.35,metal=1.0),
        brass=simple('brass','#b8893a',rough=0.3,metal=1.0),
        screen=emissive('screen','#0d0f14',1.0),
        bulb=emissive('bulb','#ffcf7a',18.0),
        flame=emissive('flame','#ffb04a',25.0),
        led=emissive('led','#39a0ff',8.0),
        pink=bead('pinkflower','#ec8f96',speck_color='#ffd3d6',speck=0.3,bead=0.006),
        blue=clay('blueclay','#6f97c4',rough=0.45,coat=0.3),
    )

def flowers(m,loc,scale=1.0,n=7,seed=3,color='pink'):
    """Bead flowers in a clay vase (like the reference miniatures)."""
    rnd=random.Random(seed); x,y,z=loc
    vase=cyl('vase',0.07*scale,0.2*scale,m['blue'] if seed%2 else m['terracotta'],loc=(x,y,z+0.1*scale),verts=32,bevel=0.02*scale)
    for i in range(n):
        a=rnd.uniform(0,2*math.pi); h=rnd.uniform(0.28,0.45)*scale; r=rnd.uniform(0.02,0.12)*scale
        top=Vector((x+math.cos(a)*r,y+math.sin(a)*r,z+0.2*scale+h))
        cu=bpy.data.curves.new('fstem','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.004*scale
        sp=cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co=(x,y,z+0.19*scale,1); sp.points[1].co=(top.x,top.y,top.z,1)
        so=bpy.data.objects.new('fstem',cu); link(so); cu.materials.append(m['green'])
        for k in range(5):
            sphere('fl',rnd.uniform(0.022,0.035)*scale,m[color],loc=top+Vector((rnd.uniform(-1,1),rnd.uniform(-1,1),rnd.uniform(-0.5,1)))*0.025*scale,seg=14)
    return vase

def teapot(m,loc,s=1.0):
    x,y,z=loc
    body=sphere('teapot',0.07*s,m['blue'],loc=(x,y,z+0.065*s),scale=(1,1,0.85),seg=32)
    sphere('teapot_lid',0.035*s,m['blue'],loc=(x,y,z+0.125*s),scale=(1,1,0.5),seg=20)
    sphere('teapot_knob',0.012*s,m['blue'],loc=(x,y,z+0.145*s),seg=12)
    cu=bpy.data.curves.new('spout','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.012*s
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    sp.bezier_points[0].co=(x+0.06*s,y,z+0.06*s); sp.bezier_points[1].co=(x+0.12*s,y,z+0.12*s)
    for bp in sp.bezier_points: bp.handle_left_type=bp.handle_right_type='AUTO'
    o=bpy.data.objects.new('spout',cu); link(o); cu.materials.append(m['blue'])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.04*s,minor_radius=0.009*s,location=(x-0.07*s,y,z+0.07*s),rotation=(math.pi/2,0,0))
    h=bpy.context.active_object; h.data.materials.append(m['blue'])
    for p in h.data.polygons: p.use_smooth=True

def book(name,loc,w,h,d,mat,title=None,title_mat=None,rot=0):
    ob=rounded_box(name,(w,d,h),0.006,mat,loc=(loc[0],loc[1],loc[2]+h/2),rot=(0,rot,0),segs=2)
    if title:
        bpy.ops.object.text_add(location=(loc[0],loc[1]+d/2+0.002,loc[2]+h/2))
        t=bpy.context.active_object; t.name=name+'_t'
        t.data.body=title; t.data.align_x='CENTER'; t.data.align_y='CENTER'
        t.data.size=min(w*0.62,0.03)*(0.8 if len(title)>12 else 1.0); t.data.extrude=0.0012
        t.rotation_euler=(R(-90),R(-90),0)  # faces +Y, reads bottom->top
        t.data.materials.append(title_mat)
    return ob

def bookshelf(m,x0,y0,width=1.1,height=2.05,depth=0.32):
    """Knitted bookshelf standing against south wall (y0 = wall), facing +Y."""
    objs=[]
    th=0.03
    yc=y0+depth/2
    # sides + top/bottom + shelves
    for sx in (x0+th/2,x0+width-th/2):
        objs.append(rounded_box('shelf_side',(th,depth,height),0.008,m['wood'],loc=(sx,yc,height/2),segs=2))
    shelves=[0.05,0.45,0.85,1.25,1.65,height-th/2]
    for z in shelves:
        objs.append(rounded_box('shelf',(width,depth,th),0.008,m['wood'],loc=(x0+width/2,yc,z),segs=2))
    objs.append(rounded_box('shelf_back',(width,0.015,height),0.004,m['woodd'],loc=(x0+width/2,y0+0.008,height/2),segs=1))
    rnd=random.Random(7)
    gold=simple('goldfoil','#d9b25a',rough=0.3,metal=0.8)
    silver=simple('silverfoil','#e0ddd6',rough=0.3,metal=0.6)
    cols=['#7d2430','#27476e','#3f6b3f','#a6782d','#5a3d6b','#2f2f36','#8c5a3c','#c7b89a','#355c5e','#9c3f2e']
    hp=['#5b1e24','#2a3e62','#6b4a2a','#2c5236','#4b2f5c','#7a2d2d','#3a3a44']  # 7 volumes
    hg=['#1f1f24','#7a2a1d','#3c3c42']
    def bookmat(c,i):
        return clay(f'bk{c}{i}',c,rough=0.55,coat=0.15,bump=0.15)
    rowlist=[]
    # shelf 2 (z=0.85): Harry Potter set;  shelf 3 (1.25): Hunger Games + others
    for si,z in enumerate(shelves[:-1]):
        x=x0+th+0.02
        xmax=x0+width-th-0.02
        base=z+th/2
        i=0
        while x<xmax-0.03:
            if si==2 and i<7:
                w=0.035+i*0.004; h=0.235; c=hp[i]; title=None
                tm=gold
            elif si==3 and i<3:
                w=0.04; h=0.215; c=hg[i]; title=None; tm=None
            elif si==3 and i==3:
                x+=0.03; i+=1; continue
            else:
                if rnd.random()<0.12 and si in (0,4):
                    # stacked horizontal books / gap with decor
                    x+=0.10; i+=1; continue
                w=rnd.uniform(0.025,0.05); h=rnd.uniform(0.18,0.30); c=rnd.choice(cols); title=None; tm=None
            if si==0: h=min(h,0.36)
            if x+w>xmax: break
            tilt=0.0
            book(f'book{si}_{i}',(x+w/2,yc+0.02,base),w,h,depth*0.72,bookmat(c,i%3),title,tm,rot=tilt)
            x+=w+0.002; i+=1
    return objs

def plant(m,loc,scale=1.0,leaves=11,seed=1):
    rnd=random.Random(seed)
    x,y,z=loc
    pot=cyl('pot',0.14*scale,0.28*scale,m['terracotta'],loc=(x,y,z+0.14*scale),verts=40,bevel=0.01)
    soil=cyl('soil',0.13*scale,0.01,yarn('soil','#3b2a1e',pattern='felt_h',stitch=0.05),loc=(x,y,z+0.27*scale))
    for i in range(leaves):
        a=i/leaves*2*math.pi+rnd.uniform(-0.2,0.2)
        l=rnd.uniform(0.35,0.6)*scale
        el=rnd.uniform(R(25),R(60))
        # stem
        stem_end=Vector((x+math.cos(a)*l*0.55*math.cos(el), y+math.sin(a)*l*0.55*math.cos(el), z+0.28*scale+l*math.sin(el)))
        cu=bpy.data.curves.new('stem','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.006*scale
        sp=cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        p0=Vector((x,y,z+0.27*scale)); sp.bezier_points[0].co=p0; sp.bezier_points[1].co=stem_end
        for bp in sp.bezier_points: bp.handle_left_type=bp.handle_right_type='AUTO'
        so=bpy.data.objects.new('stem',cu); link(so); cu.materials.append(m['green'])
        # leaf: ellipse disc bent
        bpy.ops.mesh.primitive_circle_add(vertices=24,radius=0.5,fill_type='TRIFAN')
        lf=bpy.context.active_object; lf.name='leaf'
        me=lf.data
        for v in me.vertices:
            v.co.x*=0.55; v.co.y+=0.5
            v.co.z=-0.18*(v.co.x**2)*4 - 0.05*v.co.y**2
        lf.scale=(0.28*scale,0.36*scale,0.28*scale)
        lf.location=stem_end
        lf.rotation_euler=Euler((R(-20)+el*0.3, 0, a-math.pi/2),'XYZ')
        sol=lf.modifiers.new('s','SOLIDIFY'); sol.thickness=0.02
        sub=lf.modifiers.new('sub','SUBSURF'); sub.levels=1; sub.render_levels=2
        for p in me.polygons: p.use_smooth=True
        me.materials.append(m['green'] if i%2 else m['green2'])
    return pot

def floor_lamp(m,loc,h=1.55):
    x,y,z=loc
    cyl('lamp_base',0.16,0.03,m['metal'],loc=(x,y,0.015),bevel=0.01)
    cyl('lamp_pole',0.012,h,m['brass'],loc=(x,y,h/2))
    # shade: truncated cone open, knitted
    bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=0.26,radius2=0.17,depth=0.32,end_fill_type='NOTHING',location=(x,y,h))
    sh=bpy.context.active_object; sh.name='lamp_shade'
    sol=sh.modifiers.new('s','SOLIDIFY'); sol.thickness=0.01
    for p in sh.data.polygons: p.use_smooth=True
    sh.data.materials.append(m['shade'])
    sphere('lamp_bulb',0.04,m['bulb'],loc=(x,y,h-0.02))
    # glow through the shade: warm point light
    point_light('lamp_light',(x,y,h-0.02),'#ffd2a0',45,radius=0.08)
    area_light('lamp_down',(x,y,h-0.17),(0,0,0),0.4,'#ffbf73',60,shape='DISK')
    area_light('lamp_up',(x,y,h+0.17),(math.pi,0,0),0.3,'#ffbf73',40,shape='DISK')

def fairy_lights(m,p0,p1,n=26,sag=0.12,col='#ffcf7a'):
    cu=bpy.data.curves.new('fl','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.0025
    sp=cu.splines.new('POLY'); sp.points.add(n-1)
    pts=[]
    for i in range(n):
        t=i/(n-1)
        p=p0.lerp(p1,t); p.z-=sag*4*t*(1-t)
        # little waviness
        pts.append(p)
        sp.points[i].co=(p.x,p.y,p.z,1)
    ob=bpy.data.objects.new('fl_wire',cu); link(ob); cu.materials.append(simple('wire','#2b3a2b',rough=0.6))
    bm=emissive('fairy','#ffc766',30.0)
    for i,p in enumerate(pts[1:-1]):
        sphere(f'fb{i}',0.011,bm,loc=(p.x,p.y,p.z-0.014),seg=12)
    return pts

def window_and_city(m,x0,x1,z0,z1,y):
    """Window in south wall at y; returns nothing. City outside at y-? (further south)."""
    fr=m['white']
    t=0.06
    cx=(x0+x1)/2; w=x1-x0; h=z1-z0
    rounded_box('win_frame_t',(w+t,0.10,t),0.01,fr,loc=(cx,y,z1))
    rounded_box('win_frame_b',(w+t,0.22,t),0.01,fr,loc=(cx,y+0.06,z0))  # sill
    rounded_box('win_frame_l',(t,0.10,h),0.01,fr,loc=(x0,y,(z0+z1)/2))
    rounded_box('win_frame_r',(t,0.10,h),0.01,fr,loc=(x1,y,(z0+z1)/2))
    rounded_box('win_frame_m',(0.04,0.08,h),0.01,fr,loc=(cx,y,(z0+z1)/2))
    rounded_box('win_frame_h',(w,0.08,0.04),0.01,fr,loc=(cx,y,z0+h*0.72))
    # curtains (knitted, gathered): wavy vertical panels
    for side,xa in ((-1,x0-0.28),(1,x1+0.28)):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=40,y_subdivisions=4,size=1)
        c=bpy.context.active_object; c.name='curtain'
        for v in c.data.vertices:
            u=v.co.x+0.5; hh=v.co.y+0.5
            v.co=Vector(((u-0.5)*0.55, 0.035*math.sin(u*math.pi*9), (hh)*(z1-z0+0.55)))
        c.location=(xa,y+0.12,z0-0.35)
        sol=c.modifiers.new('s','SOLIDIFY'); sol.thickness=0.012
        sub=c.modifiers.new('sub','SUBSURF'); sub.levels=1; sub.render_levels=1
        for p in c.data.polygons: p.use_smooth=True
        c.data.materials.append(m['sage'])
    # rod
    cyl('rod',0.012,w+1.4,m['brass'],loc=(cx,y+0.12,z1+0.22),rot=(0,R(90),0))
    # glass (very subtle)
    g=bpy.data.materials.new('glass'); g.use_nodes=True
    N=g.node_tree.nodes; L=g.node_tree.links
    for n in list(N): N.remove(n)
    o=N.new('ShaderNodeOutputMaterial'); tr=N.new('ShaderNodeBsdfTransparent'); gl=N.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value=0.05
    mx=N.new('ShaderNodeMixShader'); mx.inputs[0].default_value=0.06
    L.new(tr.outputs[0],mx.inputs[1]); L.new(gl.outputs[0],mx.inputs[2]); L.new(mx.outputs[0],o.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1,location=(cx,y-0.01,(z0+z1)/2),rotation=(R(90),0,0))
    gp=bpy.context.active_object; gp.scale=(w,h,1); gp.data.materials.append(g); gp.name='glasspane'
    city(m,cx,y)

def city(m,cx,y):
    """Night city skyline outside the window (built south of the window, y smaller)."""
    rnd=random.Random(11)
    sky=bpy.data.materials.new('sky'); sky.use_nodes=True
    N=sky.node_tree.nodes; L=sky.node_tree.links
    for n in list(N): N.remove(n)
    o=N.new('ShaderNodeOutputMaterial'); e=N.new('ShaderNodeEmission')
    tc=N.new('ShaderNodeTexCoord'); sep=N.new('ShaderNodeSeparateXYZ'); ramp=N.new('ShaderNodeValToRGB')
    L.new(tc.outputs['Generated'],sep.inputs[0]); L.new(sep.outputs['Y'],ramp.inputs[0])
    ramp.color_ramp.elements[0].color=hexcol('#2a2346'); ramp.color_ramp.elements[1].color=hexcol('#0b1030')
    ramp.color_ramp.elements.new(0.25).color=hexcol('#3b2d52')
    L.new(ramp.outputs[0],e.inputs[0]); e.inputs[1].default_value=1.2
    # add knit bump look to sky: mix with yarn texture via emission strength
    L.new(e.outputs[0],o.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1,location=(cx,y-40,8),rotation=(R(90),0,0))
    sp=bpy.context.active_object; sp.scale=(90,40,1); sp.data.materials.append(sky); sp.name='sky'
    # moon (felt) + stars
    sphere('moon',1.3,emissive('moonm','#f4ecd0',3.0),loc=(cx+9,y-38,14))
    for i in range(60):
        sphere(f'star{i}',rnd.uniform(0.04,0.09),emissive('starm','#fff1c9',6.0),loc=(cx+rnd.uniform(-30,30),y-39,rnd.uniform(6,24)),seg=8)
    # hill with a landmark far away
    hill=sphere('hill',1,yarn('hill','#1d2a26',stitch=0.5,bump=0.6),loc=(cx-6,y-30,-2),scale=(12,5,5.2))
    cw=yarn('landmark','#e8e1cf',stitch=0.25,bump=0.6)
    cxl=cx-6; cyl_=y-28.5; cz=3.2
    rounded_box('landmark',(4.2,2.2,1.8),0.08,cw,loc=(cxl,cyl_,cz))
    for dx in (-2.0,2.0):
        for dy in (-1.0,1.0):
            rounded_box('tower',(0.6,0.6,2.6),0.05,cw,loc=(cxl+dx,cyl_+dy,cz+0.4))
            bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=0.5,depth=0.5,location=(cxl+dx,cyl_+dy,cz+1.95),rotation=(0,0,R(45)))
            bpy.context.active_object.data.materials.append(yarn('roof','#7a3326',stitch=0.2))
    bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=3.0,radius2=2.2,depth=0.6,location=(cxl,cyl_,cz+1.2),rotation=(0,0,R(45)))
    rf=bpy.context.active_object; rf.scale=(1.0,0.55,1); rf.data.materials.append(yarn('roof','#7a3326',stitch=0.2))
    # landmark floodlight
    area_light('landmark_flood',(cxl,cyl_+4,1.5),(R(-70),0,0),3,'#ffe3b0',1500)
    # Danube strip (dark knit with glints)
    bpy.ops.mesh.primitive_plane_add(size=1,location=(cx,y-22,0.2)); dn=bpy.context.active_object
    dn.scale=(80,6,1); dn.data.materials.append(simple('danube','#0f1a2a',rough=0.15,coat=0.5))
    # bridge: pylon + deck
    bx=cx+5; by=y-21
    deck=rounded_box('bridge_deck',(26,0.8,0.25),0.05,yarn('bridge','#8d949c',stitch=0.2),loc=(bx-3,by,1.2))
    for sx in (-0.9,0.9):
        rounded_box('pylon',(0.3,0.3,7),0.05,yarn('bridge','#8d949c',stitch=0.2),loc=(bx+6+sx*0.6,by,4.3),rot=(0,R(-10*sx),0))
    ufo=sphere('ufo',1.0,yarn('ufo','#a8adb4',stitch=0.2),loc=(bx+6,by,8.0),scale=(1.2,1.2,0.35))
    ring=sphere('ufo_glow',1.0,emissive('ufog','#ffd27a',6.0),loc=(bx+6,by,7.92),scale=(1.1,1.1,0.12))
    # stay cables
    for i in range(7):
        cu=bpy.data.curves.new('cab','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.03
        s=cu.splines.new('POLY'); s.points.add(1)
        s.points[0].co=(bx+6,by,7.0,1); s.points[1].co=(bx+6-3-i*2.2,by,1.3,1)
        ob=bpy.data.objects.new('cable',cu); link(ob); cu.materials.append(yarn('bridge','#8d949c',stitch=0.2))
    # deck lights
    for i in range(14):
        sphere(f'dl{i}',0.08,emissive('streetl','#ffc46b',12.0),loc=(bx-15+i*1.8,by-0.45,1.45),seg=8)
    # apartment blocks (nearer), with lit windows
    wall=yarn('panel','#c9c2b3',pattern='rib_h',stitch=0.18,bump=0.5)
    wlit=[emissive('wl1','#ffcf85',5.0),emissive('wl2','#ffe2a8',4.0),emissive('wl3','#9fc6ff',2.5)]
    wdark=simple('wd','#141820',rough=0.4)
    win_quads=[[],[],[],[]]
    blocks=[(-9,-9,14,28),( 7,-8,10,33),(-2,-14,22,24),(13,-13,8,40),(-15,-12,9,36)]
    for bi,(bx0,by0,bw,bh) in enumerate(blocks):
        bxw=cx+bx0; byw=y+by0
        floors=int(bh/2.8)
        rounded_box('block',(bw,2.2,floors*0.7+0.3),0.05,wall,loc=(bxw,byw,floors*0.35+0.15))
        ncol=int(bw/0.9)
        for f in range(floors):
            for c in range(ncol):
                mi=rnd.randrange(3) if rnd.random()<0.35 else 3
                x=bxw-bw/2+0.45+c*0.9; z=0.5+f*0.7; yy=byw+1.11
                win_quads[mi].append((x,yy,z))
    for mi,qs in enumerate(win_quads):
        V=[];F=[]
        for (x,yy,z) in qs:
            k=len(V); V+=[(x-0.25,yy,z-0.17),(x+0.25,yy,z-0.17),(x+0.25,yy,z+0.17),(x-0.25,yy,z+0.17)]; F.append((k,k+1,k+2,k+3))
        mesh_obj(f'winq{mi}',V,F,(wlit+[wdark])[mi],smooth=False)
    # trees (felt balls)
    for i in range(22):
        tx=cx+rnd.uniform(-14,14); ty=y+rnd.uniform(-7,-3.5)
        cyl('trunk',0.08,1.2,yarn('trunk','#3a2a20',stitch=0.05),loc=(tx,ty,0.6))
        sphere('crown',rnd.uniform(0.7,1.1),yarn('treeg','#1f3a2a',pattern='felt_h',stitch=0.2,bump=0.5),loc=(tx,ty,1.8),scale=(1,1,1.2),seg=16)
    # street lamps
    for i in range(6):
        lx=cx-10+i*4; ly=y-5.2
        cyl('slp',0.04,3.2,m['metal'],loc=(lx,ly,1.6))
        sphere('sl',0.12,emissive('streetl','#ffc46b',12.0),loc=(lx,ly,3.25),seg=12)
    # ground
    bpy.ops.mesh.primitive_plane_add(size=1,location=(cx,y-15,0.0)); g=bpy.context.active_object
    g.scale=(80,30,1); g.data.materials.append(yarn('grass','#18241c',stitch=0.3,bump=0.5))
    # moon light
    sun=bpy.data.lights.new('moonlight','SUN'); sun.energy=0.08; sun.color=(0.6,0.7,1.0); sun.angle=R(3)
    so=bpy.data.objects.new('moonlight',sun); link(so); so.rotation_euler=(R(60),0,R(160))

def robot_vacuum(m,loc,rotz=0):
    x,y,z=loc
    body=cyl('robovac',0.175,0.075,yarn('vac','#3a3d44',stitch=0.012),loc=(x,y,0.045),bevel=0.02)
    top=cyl('robovac_top',0.12,0.012,m['black'],loc=(x,y,0.088),bevel=0.004)
    laser=cyl('robovac_lidar',0.045,0.03,yarn('vac2','#d9d6cf',stitch=0.008),loc=(x+0.0,y+0.08,0.1),bevel=0.006)
    led=sphere('robovac_led',0.008,m['led'],loc=(x,y-0.12,0.09))
    bump=cyl('robovac_bumper',0.178,0.03,yarn('vacb','#9a9ea6',pattern='rib_h',stitch=0.008),loc=(x,y,0.035))
    root=bpy.data.objects.new('robovac_root',None); link(root); root.location=(x,y,0)
    for o in (body,top,laser,led,bump):
        o.parent=root; o.location=(o.location.x-x,o.location.y-y,o.location.z)
    root.rotation_euler=(0,0,rotz)
    return root

def build_room():
    m=M()
    W0,W1=-3.2,3.2; S,Nn=-2.5,3.2; H=2.7
    # floor
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,(S+Nn)/2,0)); f=bpy.context.active_object; f.name='floor'
    f.scale=(W1-W0,Nn-S,1); f.data.materials.append(m['floor'])
    # rug (round, striped rings)
    for i,(r,mat) in enumerate(((1.35,m['rug']),(1.1,m['rug2']),(0.95,m['rug']),(0.55,m['rug2']),(0.4,m['rug']))):
        cyl(f'rug{i}',r,0.012+i*0.001,mat,loc=(0,0.35,0.006+i*0.0005),verts=96,bevel=0.004)
    # walls: south wall with window hole: build as 4 pieces
    win=(0.1,2.1,0.85,2.25)  # x0,x1,z0,z1
    wm=m['wall']
    def wall_piece(name,x0,x1,z0,z1,y,mat,thick=0.12):
        rounded_box(name,(x1-x0,thick,z1-z0),0.01,mat,loc=((x0+x1)/2,y,(z0+z1)/2),segs=1)
    wall_piece('ws_l',W0,win[0],0,H,S,wm); wall_piece('ws_r',win[1],W1,0,H,S,wm)
    wall_piece('ws_b',win[0],win[1],0,win[2],S,wm); wall_piece('ws_t',win[0],win[1],win[3],H,S,wm)
    wall_piece('wn',W0,W1,0,H,Nn,m['wall2'])
    rounded_box('ww',(0.12,Nn-S,H),0.01,wm,loc=(W0,(S+Nn)/2,H/2),segs=1)
    rounded_box('we',(0.12,Nn-S,H),0.01,wm,loc=(W1,(S+Nn)/2,H/2),segs=1)
    rounded_box('ceil',(W1-W0,Nn-S,0.1),0.01,m['white'],loc=(0,(S+Nn)/2,H+0.05),segs=1)
    # skirting
    window_and_city(m,win[0],win[1],win[2],win[3],S)
    # couch (red) centered, facing +Y
    cy=-1.25
    rounded_box('couch_base',(2.3,0.95,0.30),0.06,m['couch2'],loc=(0,cy,0.22))
    rounded_box('couch_back',(2.3,0.28,0.62),0.1,m['couch'],loc=(0,cy-0.36,0.62))
    for sx in (-1,1):
        rounded_box('couch_arm',(0.24,0.95,0.40),0.1,m['couch'],loc=(sx*1.1,cy,0.52))
    for sx in (-0.47,0.47):
        cushion('seat_cush',(0.93,0.66,0.16),m['couch'],loc=(sx,cy+0.1,0.46),puff=0.25)
        cushion('back_cush',(0.9,0.45,0.18),m['couch'],loc=(sx,cy-0.2,0.78),rot=(R(78),0,0),puff=0.3)
    # legs
    for sx in (-1.05,1.05):
        for sy in (cy-0.4,cy+0.4):
            cyl('couch_leg',0.025,0.07,m['woodd'],loc=(sx,sy,0.035))
    # throw pillows + blanket
    cushion('pillow_m',(0.42,0.42,0.13),m['mustard'],loc=(-0.86,cy-0.12,0.75),rot=(R(72),R(8),R(14)),puff=0.6)
    cushion('pillow_c',(0.40,0.40,0.13),m['cream'],loc=(0.88,cy-0.12,0.75),rot=(R(72),R(-8),R(-12)),puff=0.6)
    # coffee table (knitted wood) with candle, remote, book
    rounded_box('table_top',(1.1,0.55,0.05),0.02,m['wood'],loc=(0,0.35,0.40))
    for sx in (-0.48,0.48):
        for sy in (0.14,0.56):
            cyl('tleg',0.022,0.38,m['woodd'],loc=(sx,sy,0.19))
    cyl('candle',0.035,0.08,m['cream'],loc=(0.3,0.3,0.465))
    sphere('flame',0.009,m['flame'],loc=(0.3,0.3,0.52),scale=(0.8,0.8,1.8))
    point_light('candle_l',(0.3,0.3,0.54),'#ffa347',6,radius=0.01)
    rounded_box('remote',(0.05,0.18,0.02),0.008,m['black'],loc=(-0.25,0.42,0.435),rot=(0,0,R(20)))
    rounded_box('tbook',(0.2,0.26,0.035),0.005,yarn('tb','#2c4c6c',pattern='rib_h',stitch=0.008),loc=(-0.05,0.3,0.44),rot=(0,0,R(-8)))
    # TV console + TV on north wall
    rounded_box('tv_console',(1.9,0.42,0.45),0.03,m['wood'],loc=(0,Nn-0.27,0.25))
    for sx in (-0.6,0.0,0.6):
        rounded_box('drawer',(0.55,0.02,0.3),0.01,m['woodd'],loc=(sx,Nn-0.48,0.25))
    tvw,tvh=1.46,0.84; tvz=1.25
    rounded_box('tv_body',(tvw+0.03,0.05,tvh+0.03),0.008,m['black'],loc=(0,Nn-0.12,tvz))
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,Nn-0.147,tvz),rotation=(R(90),0,R(180)))
    scr=bpy.context.active_object; scr.name='tv_screen'; scr.scale=(tvw,tvh,1)
    scr.data.materials.append(tv_screen_material())
    # TV light onto room
    tvl=area_light('tv_light',(0,Nn-0.2,tvz),(R(-90),0,0),tvw,'#bcd2ff',60,size_y=tvh)
    tvl.rotation_euler=(R(90),0,0)
    # TV wall decor: floating shelves, books, candles, plants, fairy lights, wall hanging
    for sx in (1,):
        for k,z in enumerate((1.05,1.55)):
            x=sx*1.45
            rounded_box('wshelf',(0.7,0.22,0.03),0.008,m['wood'],loc=(x,Nn-0.17,z))
            if k==0:
                for j in range(6):
                    book(f'wb{sx}{j}',(x-0.28+j*0.045,Nn-0.17,z+0.015),0.04,0.2+0.02*(j%3),0.15,clay(f'wbm{j%3}',['#b8575a','#5c7fa8','#d3a24f'][j%3],rough=0.55))
                plant(m,(x+0.18,Nn-0.17,z+0.015),scale=0.35,leaves=7,seed=10+sx)
            else:
                cyl('wcandle',0.03,0.1,m['cream'],loc=(x-0.15,Nn-0.17,z+0.065))
                sphere('wflame',0.008,m['flame'],loc=(x-0.15,Nn-0.17,z+0.125),scale=(0.8,0.8,1.8))
                point_light('wcl',(x-0.15,Nn-0.2,z+0.14),'#ffa347',4,radius=0.01)
                sphere('yarnball',0.06,yarn('yb','#b0513a',stitch=0.006),loc=(x+0.1,Nn-0.17,z+0.075))
                cyl('vase',0.04,0.16,m['terracotta'],loc=(x+0.25,Nn-0.17,z+0.095))
    fairy_lights(m,Vector((-1.2,Nn-0.14,2.15)),Vector((1.2,Nn-0.14,2.15)),n=30,sag=0.18)
    # decor on console: plant + small speaker + books
    plant(m,(-0.75,Nn-0.27,0.475),scale=0.6,leaves=9,seed=3)
    cyl('speaker',0.06,0.22,m['grey'],loc=(0.8,Nn-0.27,0.585),bevel=0.01)
    # big plant in corner, floor lamp, shelf
    plant(m,(-2.6,-1.95,0),scale=1.25,leaves=13,seed=5)
    plant(m,(2.6,-1.95,0),scale=0.9,leaves=10,seed=9)
    floor_lamp(m,(1.55,-1.75,0))
    # bookshelf on the TV wall, left of the TV (built facing +Y, then turned to face the room)
    before=set(bpy.data.objects)
    bookshelf(m,-0.55,-0.16)
    bs_root=bpy.data.objects.new('bookshelf_root',None); link(bs_root)
    for o in set(bpy.data.objects)-before:
        if o.parent is None and o!=bs_root: o.parent=bs_root
    bs_root.rotation_euler=(0,0,math.pi); bs_root.location=(-2.35,Nn-0.22,0)
    # fairy lights along window top + shelf
    fairy_lights(m,Vector((-0.3,S+0.14,2.45)),Vector((2.5,S+0.14,2.45)),n=30,sag=0.12)
    fairy_lights(m,Vector((-2.9,Nn-0.42,2.1)),Vector((-1.8,Nn-0.42,2.1)),n=14,sag=0.08)
    # wall picture above couch? (window is there) -> picture on west wall
    rounded_box('frame',(0.04,0.8,0.6),0.01,m['woodd'],loc=(W0+0.08,0.2,1.55))
    rounded_box('art',(0.02,0.7,0.5),0.01,yarn('art','#3b6a8a',stitch=0.03),loc=(W0+0.1,0.2,1.55))
    sphere('art_sun',0.08,m['mustard'],loc=(W0+0.115,0.35,1.65),scale=(0.2,1,1))
    # ceiling pendant is off; general low ambient fill (cool, as if from the window)
    area_light('fill_window',(1.1,S+0.3,1.6),(R(-90),0,0),1.8,'#8fa6ff',25,size_y=1.3).rotation_euler=(R(-90),0,0)
    flowers(m,(-0.45,0.28,0.425),scale=0.8,n=6,seed=4)
    teapot(m,(0.05,0.45,0.425),s=0.9)
    flowers(m,(0.75,Nn-0.27,0.475),scale=1.0,n=8,seed=5)
    flowers(m,(2.75,1.2,0.0),scale=1.8,n=10,seed=7)
    flowers(m,(-2.7,-0.6,0.0),scale=1.6,n=9,seed=8)
    for i,(px,py) in enumerate(((2.45,-1.2),(-2.65,1.6),(2.6,2.6))):
        cyl('bigpot',0.16,0.3,m['terracotta'],loc=(px,py,0.15),verts=36,bevel=0.03)
        sphere('bush',0.26,m['green2'] if i%2 else m['green'],loc=(px,py,0.42),scale=(1,1,0.8),seg=24)
    area_light('key_warm',(-0.9,0.9,1.9),(R(58),0,R(200)),2.5,'#ffe3c8',240)
    area_light('key_front',(0.6,1.6,1.3),(R(80),0,R(180)),2.2,'#fff1e2',110)
    area_light('ceiling_soft',(0,0.3,2.6),(0,0,0),3.5,'#ffe8d0',90,size_y=4.0)
    rv=robot_vacuum(m,(1.2,0.9,0),rotz=R(30))
    return dict(tv_screen=scr,tv_light=tvl,robovac=rv,couch_y=cy,north=Nn,south=S,tvz=tvz,tvw=tvw,tvh=tvh)

def tv_screen_material():
    """Screen shows a soft generic glow; the app overlays the real clip at runtime."""
    m=bpy.data.materials.new('tvscreen'); m.use_nodes=True
    N=m.node_tree.nodes; L=m.node_tree.links
    for n in list(N): N.remove(n)
    o=N.new('ShaderNodeOutputMaterial'); e=N.new('ShaderNodeEmission'); e.name='E'
    tx=N.new('ShaderNodeTexImage'); tx.image=bpy.data.images.load(os.path.join(TEX,'tv_fallback.png'))
    tc=N.new('ShaderNodeTexCoord'); L.new(tc.outputs['UV'],tx.inputs['Vector'])
    L.new(tx.outputs['Color'],e.inputs['Color']); e.inputs['Strength'].default_value=1.6
    L.new(e.outputs[0],o.inputs[0])
    return m
