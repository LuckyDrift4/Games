"""Blender preview of the R6 tennis animations: an R6 noob holding the realistic racket, every clip rendered to a GIF
plus a key-pose sheet, and a .blend with the whole set keyed on one timeline (markers name each clip).

    python game/anim/preview_blender.py [-- clips Forehand,Serve] [-- norender]     (Blender's bpy module)
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6  # noqa: E402
from clips import CLIPS, ORDER  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'previews')
RACKET_GLB = os.path.join(ROOT, 'out', 'tennis_racket', 'TennisRacket.glb')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FPS = 20

G = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # Roblox / glTF (Y up) -> Blender (Z up)
GI = G.inverted()
NOOB = {'Head': (.96, .80, .19), 'Torso': (.05, .41, .67), 'Right Arm': (.96, .80, .19), 'Left Arm': (.96, .80, .19),
        'Right Leg': (.64, .74, .28), 'Left Leg': (.64, .74, .28)}


def lin(c):
    return tuple(x ** 2.2 for x in c)


def material(name, rgb, rough=.6):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(rgb), 1)
    b.inputs['Roughness'].default_value = rough
    return m


def box_mesh(name, size, bevel=.08, head=False):
    bm = bmesh.new()
    if head:                                    # R6 head: rounded cylinder about 1.25 x 1.25
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=.62, radius2=.62, depth=1.18)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=bm.verts)
    else:
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=.14 if head else bevel, segments=3 if head else 2,
                    affect='EDGES', clamp_overlap=True)
    bm.transform(G.to_3x3().to_4x4())           # Roblox-local -> Blender-local
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    return me


def to_blender(M):
    return G @ Matrix(M) @ GI


def build_character():
    coll = bpy.data.collections.new('R6')
    bpy.context.scene.collection.children.link(coll)
    objs = {}
    for part, col in NOOB.items():
        me = box_mesh(part, r6.PART_SIZE[part], head=(part == 'Head'))
        me.materials.append(material('M_' + part, col, .55))
        o = bpy.data.objects.new(part, me)
        coll.objects.link(o)
        objs[part] = o
    face = material('M_face', (.05, .05, .06), .4)
    for name, verts in (('EyeL', (-.22, .12, -.6)), ('EyeR', (.22, .12, -.6))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=.09)
        bmesh.ops.scale(bm, vec=(1, 1.4, .5), verts=bm.verts)
        bmesh.ops.translate(bm, vec=verts, verts=bm.verts)
        bm.transform(G.to_3x3().to_4x4())
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(face)
        e = bpy.data.objects.new(name, me); coll.objects.link(e); e.parent = objs['Head']
    bm = bmesh.new()                            # smile
    pts = [(math.sin(a) * .28, -.12 - math.cos(a) * .1, -.6) for a in [(-.8 + 1.6 * i / 10) for i in range(11)]]
    for a, b in zip(pts, pts[1:]):
        v = [bm.verts.new(p) for p in (a, b, (b[0], b[1] - .05, b[2]), (a[0], a[1] - .05, a[2]))]
        bm.faces.new(v)
    bm.transform(G.to_3x3().to_4x4())
    me = bpy.data.meshes.new('Smile'); bm.to_mesh(me); bm.free(); me.materials.append(face)
    s = bpy.data.objects.new('Smile', me); coll.objects.link(s); s.parent = objs['Head']
    # racket: the realistic model, butt at its origin, head along +Y
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=RACKET_GLB)
    racket = bpy.data.objects.new('Racket', None)
    coll.objects.link(racket)
    for o in set(bpy.data.objects) - before:
        if o.type == 'MESH':
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
            o.parent = racket
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_basis = Matrix.Translation((0, 0, -r6.RACKET_BUTT))   # hand at 0.30 above the butt (Blender Z)
    objs['Racket'] = racket
    return objs


def apply_pose(objs, pose, root=None):
    W = r6.solve(pose, root)
    for part, o in objs.items():
        o.matrix_world = to_blender(W[part])


def studio():
    sc = bpy.context.scene
    floor = bpy.data.meshes.new('Court')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
    bm.to_mesh(floor); bm.free()
    floor.materials.append(material('M_court', (.16, .33, .62), .7))
    sc.collection.objects.link(bpy.data.objects.new('Court', floor))
    line = bpy.data.meshes.new('Line')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(30, .25, .02), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 3.2, .01), verts=bm.verts)
    bm.to_mesh(line); bm.free()
    line.materials.append(material('M_line', (.95, .95, .95), .5))
    sc.collection.objects.link(bpy.data.objects.new('BaseLine', line))
    for name, loc, e, size in (('Key', (6, -9, 9), 900, 6), ('Fill', (-8, -6, 5), 260, 8), ('Rim', (-2, 9, 8), 600, 4)):
        L = bpy.data.lights.new(name, 'AREA'); L.energy = e; L.size = size
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 3)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('W'); sc.world = w
    w.node_tree.nodes['Background'].inputs[0].default_value = (.18, .2, .24, 1)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam); sc.camera = cam
    aim(cam, (6.2, 8.6, 4.4), (0, 0, 2.55), 42)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 14; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = .6
    return cam


def aim(cam, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


# the character faces Roblox -Z = Blender +Y; its right is Blender +X
VIEWS = {'front': ((6.2, 8.6, 4.4), (0, 0, 2.55)), 'side': ((10.5, -0.6, 3.6), (0, 0, 2.55)),
         'back': ((-5.5, -8.8, 4.6), (0, 0, 2.55))}


def render_keys(objs, names, size=230):
    """every keyframe of every clip from the front-right and the side: one sheet for fast pose review"""
    from PIL import Image, ImageDraw
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    cam = sc.camera
    rows = []
    tmp = os.path.join(OUT, '_k.png')
    for name in names:
        ims = []
        for kf in CLIPS[name]['keys']:
            apply_pose(objs, r6.sample(name, kf['t']))
            for v in ('front', 'side'):
                aim(cam, *VIEWS[v], 42)
                sc.render.filepath = tmp
                bpy.ops.render.render(write_still=True)
                ims.append(Image.open(tmp).convert('RGB').copy())
        rows.append((name, ims))
    w = max(len(r[1]) for r in rows)
    S = Image.new('RGB', (130 + w * size, len(rows) * size), (24, 26, 32))
    D = ImageDraw.Draw(S)
    for r, (name, ims) in enumerate(rows):
        D.text((6, r * size + size // 2), name, fill=(255, 255, 255))
        for c, im in enumerate(ims):
            S.paste(im, (130 + c * size, r * size))
    S.save(os.path.join(OUT, 'keys_%s.jpg' % '_'.join(names)), quality=86)
    os.remove(tmp)


def render_clip(objs, name, size=360):
    from PIL import Image
    clip = CLIPS[name]
    n = max(2, int(round(clip['length'] * FPS)))
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    frames = []
    tmp = os.path.join(OUT, '_frame.png')
    for i in range(n + (0 if clip['loop'] else 1)):
        t = i / FPS
        apply_pose(objs, r6.sample(name, t))
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        frames.append(Image.open(tmp).convert('RGB').copy())
    os.remove(tmp)
    frames[0].save(os.path.join(OUT, name + '.gif'), save_all=True, append_images=frames[1:], duration=int(1000 / FPS),
                   loop=0, optimize=True)
    return frames


def key_timeline(objs):
    """every clip one after another on the timeline, keyed per frame, with a marker per clip"""
    sc = bpy.context.scene
    sc.render.fps = 30
    f = 1
    for name in ORDER:
        clip = CLIPS[name]
        sc.timeline_markers.new(name, frame=f)
        n = int(round(clip['length'] * 30))
        for i in range(n + 1):
            apply_pose(objs, r6.sample(name, i / 30))
            for o in objs.values():
                o.rotation_mode = 'QUATERNION'
                o.rotation_quaternion = o.matrix_world.to_quaternion()
                o.keyframe_insert('location', frame=f + i)
                o.keyframe_insert('rotation_quaternion', frame=f + i)
        f += n + 10
    sc.frame_start, sc.frame_end = 1, f


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    objs = build_character()
    studio()
    names = ARGS[ARGS.index('clips') + 1].split(',') if 'clips' in ARGS else ORDER
    if 'keys' in ARGS:
        render_keys(objs, names)
        print('PREVIEW_OK')
        return
    if 'norender' not in ARGS:
        from PIL import Image, ImageDraw
        sheet_rows = []
        for name in names:
            frames = render_clip(objs, name)
            clip = CLIPS[name]
            idx = [int(round(kf['t'] * FPS)) for kf in clip['keys']]
            idx = [min(len(frames) - 1, i) for i in idx][:6]
            sheet_rows.append((name, [frames[i] for i in idx]))
            print('CLIP', name, len(frames), 'frames')
        cell = 220
        S = Image.new('RGB', (cell * 6 + 150, cell * len(sheet_rows)), (24, 26, 32))
        D = ImageDraw.Draw(S)
        for r, (name, fr) in enumerate(sheet_rows):
            D.text((8, r * cell + cell // 2), name, fill=(255, 255, 255))
            for c, im in enumerate(fr):
                S.paste(im.resize((cell, cell)), (150 + c * cell, r * cell))
        S.save(os.path.join(OUT, 'key_poses%s.jpg' % ('' if names == ORDER else '_' + '_'.join(names))), quality=88)
    if names == ORDER:
        key_timeline(objs)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'TennisR6Animations.blend'))
    print('PREVIEW_OK')


main()
