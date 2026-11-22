"""Blender preview of the R6 tennis animations on a real R6 rig: the classic R6 body (2x2x1 torso, 1x2x1 limbs, the
round R6 head with the classic smile), holding the realistic racket, on a tennis court in bright Roblox-style
daylight. Renders each clip to a GIF (front + in-game camera side by side, with the ball), a key-pose sheet, and a
.blend with every clip keyed on one timeline (markers name the clips).

    python game/anim/preview_blender.py [-- clips Forehand,Serve] [-- sheet] [-- norender] [-- quick]
"""
import math
import os
import shutil
import subprocess
import sys

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6  # noqa: E402
import rig  # noqa: E402
from clips import CLIPS, ORDER  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'previews')
TMP = os.path.join(OUT, '_tmp')
RACKET_GLB = os.path.join(ROOT, 'out', 'tennis_racket', 'TennisRacket.glb')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FPS = rig.FPS
HEAD_CENTER = 2.01          # racket string-bed centre, studs above the hand
QUICK = 'quick' in ARGS

G = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # Roblox (Y up, -Z forward) -> Blender
GI = G.inverted()
HIP = 3.0                    # HumanoidRootPart height above the floor
# classic noob BrickColors: Bright yellow, Bright blue, Br. yellowish green
NOOB = {'Head': (245, 205, 48), 'Torso': (13, 105, 172), 'Right Arm': (245, 205, 48), 'Left Arm': (245, 205, 48),
        'Right Leg': (164, 189, 71), 'Left Leg': (164, 189, 71)}


def srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    return tuple(srgb(v) for v in rgb)


def material(name, rgb, rough=.5, spec=.35):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(rgb), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    return m


def finish_mesh(name, bm, smooth=False):
    bm.transform(G.to_3x3().to_4x4())           # Roblox-local -> Blender-local
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    else:
        me.shade_flat()
    return me


def block(name, size):
    """an R6 body part: a plain block with a hairline bevel so edges catch the light like Roblox parts"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=.035, segments=2, affect='EDGES', clamp_overlap=True)
    me = finish_mesh(name, bm, smooth=True)
    me.polygons.foreach_set('use_smooth', [False] * len(me.polygons))
    return me


def r6_head():
    """the R6 head: a 1.2 x 1.2 cylinder with rounded top and bottom edges (MeshType Head at scale 1.25)"""
    R, H, rr = .6, 1.2, .26
    prof = [(0.0, -H / 2)]
    for i in range(9):                          # bottom rounded edge
        a = -math.pi / 2 + i / 8 * math.pi / 2
        prof.append((R - rr + rr * math.cos(a), -H / 2 + rr + rr * math.sin(a)))
    for i in range(9):                          # top rounded edge
        a = i / 8 * math.pi / 2
        prof.append((R - rr + rr * math.cos(a), H / 2 - rr + rr * math.sin(a)))
    prof.append((0.0, H / 2))
    N = 64
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rings = []
    for i in range(N):
        a = i / N * 2 * math.pi
        rings.append([bm.verts.new((math.sin(a) * r, y, -math.cos(a) * r)) for r, y in prof])
    for i in range(N):
        A, B = rings[i], rings[(i + 1) % N]
        for j in range(len(prof) - 1):
            f = bm.faces.new((A[j], B[j], B[j + 1], A[j + 1]))
            for lp in f.loops:
                v = lp.vert.co
                ang = math.atan2(v.x, -v.z)              # 0 = straight ahead (Roblox -Z)
                lp[uv].uv = (0.5 + ang / (math.pi * 1.1), 0.5 + v.y / 1.2)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return finish_mesh('Head', bm, smooth=True)


def face_texture(path):
    """the classic R6 smile: two tall oval eyes and a smile"""
    from PIL import Image, ImageDraw
    S = 1024
    im = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(im)
    # texture u spans +-99 degrees around the head, v spans the head height (top = v 1 = image row 0)
    def px(ang_deg, y):
        return (0.5 + math.radians(ang_deg) / (math.pi * 1.1)) * S, (0.5 - y / 1.2) * S
    for ang in (-15.5, 15.5):
        cx, cy = px(ang, 0.1)
        d.ellipse((cx - 26, cy - 62, cx + 26, cy + 62), fill=255)
    pts = []
    for i in range(41):
        a = -36 + 72 * i / 40
        pts.append(px(a, -0.13 - 0.16 * math.cos(math.radians(a * 2.4)) ** 1.2 if abs(a * 2.4) < 90 else -0.13))
    for i in range(41):
        a = -36 + 72 * i / 40
        x, y = pts[i]
        w = 13 * (1 - (abs(a) / 36) ** 2) + 5
        d.ellipse((x - w, y - w, x + w, y + w), fill=255)
    im = im.resize((S, S))
    im.save(path)


def head_material(tex):
    m = bpy.data.materials.new('M_Head')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = .5
    b.inputs['Specular IOR Level'].default_value = .35
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(tex)
    img.image.colorspace_settings.name = 'Non-Color'
    img.extension = 'CLIP'
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*lin(NOOB['Head']), 1)
    mix.inputs['B'].default_value = (0.008, 0.008, 0.01, 1)
    nt.links.new(img.outputs['Color'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def build_character():
    coll = bpy.data.collections.new('R6')
    bpy.context.scene.collection.children.link(coll)
    objs = {}
    os.makedirs(TMP, exist_ok=True)
    tex = os.path.join(TMP, 'r6_face.png')
    face_texture(tex)
    for part, col in NOOB.items():
        if part == 'Head':
            me = r6_head()
            me.materials.append(head_material(tex))
        else:
            me = block(part, r6.PART_SIZE[part])
            me.materials.append(material('M_' + part, col))
        o = bpy.data.objects.new(part, me)
        coll.objects.link(o)
        objs[part] = o
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
            o.matrix_basis = Matrix.Translation((0, 0, -r6.RACKET_BUTT))   # hand 0.30 above the butt (Blender Z)
    objs['Racket'] = racket
    ball = bpy.data.objects.new('Ball', ball_mesh())
    coll.objects.link(ball)
    objs['Ball'] = ball
    return objs


def ball_mesh():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.35)
    me = bpy.data.meshes.new('Ball')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.materials.append(material('M_ball', (214, 240, 60), .75, .2))
    return me


def to_blender(M):
    return G @ Matrix(M) @ GI


def apply(objs, mats, ball=None):
    W = r6.solve(mats, r6.mat(p=(0, HIP, 0)))
    for part, o in objs.items():
        if part in W:
            o.matrix_world = to_blender(W[part])
    b = objs['Ball']
    if ball is None:
        b.hide_render = True
        b.location = (0, 0, -20)
    else:
        b.hide_render = False
        b.location = (ball[0], -ball[2], ball[1] + HIP)


# ---------------------------------------------------------------- the court
def court():
    sc = bpy.context.scene
    col = bpy.data.collections.new('Court')
    sc.collection.children.link(col)

    def slab(name, x0, x1, y0, y1, z, rgb, rough=.8, h=.02):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, z - h / 2), verts=bm.verts)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(material('M_' + name, rgb, rough, .2))
        o = bpy.data.objects.new(name, me)
        col.objects.link(o)
        return o
    # the player stands just behind the near baseline, facing +Y (the net is 40 studs ahead)
    base = 1.4
    L, Wd, Ws, SL = 78, 36, 27, 21
    slab('Apron', -60, 60, -40, 140, 0, (52, 122, 86))
    slab('Court', -Wd / 2, Wd / 2, base, base + L, .01, (42, 92, 168), .75)
    lw = .35
    white = (240, 242, 245)
    for x in (-Wd / 2, Wd / 2, -Ws / 2, Ws / 2):
        slab('Side', x - lw / 2, x + lw / 2, base, base + L, .03, white, .6)
    for y in (base, base + L):
        slab('Base', -Wd / 2, Wd / 2, y - lw / 2, y + lw / 2, .03, white, .6)
    for y in (base + L / 2 - SL, base + L / 2 + SL):
        slab('Service', -Ws / 2, Ws / 2, y - lw / 2, y + lw / 2, .03, white, .6)
    slab('Center', -lw / 2, lw / 2, base + L / 2 - SL, base + L / 2 + SL, .03, white, .6)
    slab('Mark', -lw / 2, lw / 2, base, base + 1.2, .03, white, .6)
    # net
    ny = base + L / 2
    slab('Net', -21, 21, ny - .05, ny + .05, 3.0, (25, 28, 34), .9, h=3.0)
    slab('NetTape', -21, 21, ny - .08, ny + .08, 3.15, white, .6, h=.3)
    for x in (-21, 21):
        slab('Post', x - .2, x + .2, ny - .2, ny + .2, 3.6, (30, 70, 50), .5, h=3.6)
    # back wall and stands far away
    slab('Wall', -60, 60, base + L + 20, base + L + 21, 6, (24, 40, 78), .8, h=6)
    slab('Stand', -60, 60, base + L + 21, base + L + 40, 16, (70, 78, 92), .9, h=10)
    slab('WallNear', -60, 60, -26, -25, 6, (24, 40, 78), .8, h=6)


def lights():
    sc = bpy.context.scene
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 4.2
    sun.angle = math.radians(2.5)
    o = bpy.data.objects.new('Sun', sun)
    sc.collection.objects.link(o)
    o.rotation_euler = (math.radians(38), math.radians(-24), math.radians(-35))
    w = bpy.data.worlds.new('Sky')
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes['Background']
    # a simple bright blue sky that also lights the scene
    bg.inputs['Color'].default_value = (.42, .62, .95, 1)
    bg.inputs['Strength'].default_value = 1.0
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 10 if QUICK else 24
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = -.15
    sc.render.film_transparent = False


def camera(name):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    return cam


def aim(cam, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


# Blender: the character faces +Y, its right is +X, the floor is z = 0
VIEWS = {
    'front': ((7.5, 10.5, 4.6), (0.4, 0.6, 2.6), 46),       # front-right three-quarter
    'game': ((-1.0, -12.5, 7.2), (0.2, 3.0, 2.6), 36),      # the in-game camera behind the player
    'side': ((12.0, 0.5, 3.4), (0, 0.5, 2.7), 46),
    'back': ((-7.0, -8.5, 4.8), (0, 0.6, 2.6), 46),
}


def render_to(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- the ball for each clip
def ball_track(name, frames):
    """ball position (Roblox character space) per frame, or None"""
    clip = CLIPS[name]
    c = clip.get('contact')
    if c is None:
        return [None] * len(frames)
    ts = [t for t, _, _ in frames]
    ci = min(range(len(ts)), key=lambda i: abs(ts[i] - c))
    hit = rig.racket_point(frames[ci][1], HEAD_CENTER)
    g = 38.0
    out = []
    if name == 'Serve':
        toss_t = clip['toss']
        ti = min(range(len(ts)), key=lambda i: abs(ts[i] - toss_t))
        for i, (t, mats, P) in enumerate(frames):
            W = rig.world(mats)
            lhand = rig.pos_of(r6.mul(W['Left Arm'], r6.mat(p=(0, -1.25, -0.1))))
            if i <= ti:
                out.append(lhand)
                continue
            out.append(None)
        p0 = out[ti]
        T = c - toss_t
        v = tuple((hit[k] - p0[k]) / T for k in range(3))
        v = (v[0], v[1] + .5 * g * T, v[2])
        for i, t in enumerate(ts):
            if ti < i <= ci:
                dt = t - toss_t
                out[i] = (p0[0] + v[0] * dt, p0[1] + v[1] * dt - .5 * g * dt * dt, p0[2] + v[2] * dt)
        vout = (0.0, -6.0, -95.0)
    else:
        volley = name.startswith('Volley') or name == 'Smash'
        if name == 'Smash':
            vin = (0.5, -16.0, 30.0)        # a lob dropping in (Roblox z: +30 = toward the player)
        elif volley:
            vin = (-6.0 if 'Fore' in name else 6.0, 2.0, 70.0)
        else:
            vin = (-10.0 if name == 'Forehand' else 10.0, 6.0, 52.0)
        for t in ts:
            if t > c:
                out.append(None)
                continue
            dt = c - t
            if volley:
                p = (hit[0] - vin[0] * dt, hit[1] - vin[1] * dt - .5 * g * dt * dt, hit[2] - vin[2] * dt)
            else:
                # bounced 0.3 s before contact: rewind the rise, then the incoming flight before the bounce
                tb = .3
                vy_up = (hit[1] - (-3 + .35) + .5 * g * tb * tb) / tb
                if dt <= tb:
                    s = tb - dt
                    p = (hit[0] - vin[0] * dt, -3 + .35 + vy_up * s - .5 * g * s * s, hit[2] - vin[2] * dt)
                else:
                    e = dt - tb
                    bounce = (hit[0] - vin[0] * tb, -3 + .35, hit[2] - vin[2] * tb)
                    vy_in = vy_up / .72
                    p = (bounce[0] - vin[0] / .84 * e, -3 + .35 + vy_in * e - .5 * g * e * e, bounce[2] - vin[2] / .84 * e)
            out.append(p)
        vout = {'Forehand': (8.0, 9.0, -78.0), 'Backhand': (-8.0, 9.0, -78.0), 'Smash': (0.0, -22.0, -100.0)}.get(
            name, (0.0, 2.0, -62.0))
    for i, t in enumerate(ts):
        if t > c:
            dt = t - c
            out[i] = (hit[0] + vout[0] * dt, hit[1] + vout[1] * dt - .5 * g * dt * dt, hit[2] + vout[2] * dt)
    return out


# ---------------------------------------------------------------- outputs
def baked(name):
    return rig.bake(CLIPS[name])


def sheet(names, views=('front', 'side', 'game'), size=200):
    """key poses (every key of each clip) from several views, for quick review"""
    from PIL import Image, ImageDraw
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.cycles.samples = 8
    cams = {v: camera('C_' + v) for v in views}
    for v in views:
        aim(cams[v], *VIEWS[v])
    rows = []
    for name in names:
        clip = CLIPS[name]
        frames = baked(name)
        balls = ball_track(name, frames)
        cols = []
        for kt, _, _ in clip['keys']:
            i = min(range(len(frames)), key=lambda j: abs(frames[j][0] - kt))
            apply(OBJS, frames[i][1], balls[i])
            ims = []
            for v in views:
                sc.camera = cams[v]
                p = os.path.join(TMP, 's.png')
                render_to(p)
                ims.append(Image.open(p).convert('RGB').copy())
            cols.append((kt, ims))
        rows.append((name, cols))
    wmax = max(len(c) for _, c in rows)
    S = Image.new('RGB', (110 + wmax * size, sum(len(views) for _ in rows) * size), (22, 24, 30))
    D = ImageDraw.Draw(S)
    y = 0
    for name, cols in rows:
        D.text((6, y + 8), name, fill=(255, 255, 255))
        for c, (kt, ims) in enumerate(cols):
            for r, im in enumerate(ims):
                S.paste(im, (110 + c * size, y + r * size))
            D.text((110 + c * size + 4, y + 4), '%.2fs' % kt, fill=(255, 255, 0))
        y += len(views) * size
    path = os.path.join(OUT, 'sheet_%s.jpg' % '_'.join(names) if len(names) < 4 else 'sheet_all.jpg')
    S.save(path, quality=85)
    print('SHEET', path)


def gif(name, size=400):
    """one clip as a GIF: three-quarter front view | in-game camera, the ball flying in and out"""
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.cycles.samples = 10 if QUICK else 16
    frames = baked(name)
    balls = ball_track(name, frames)
    cams = {v: camera('G_' + v) for v in ('front', 'game')}
    for v in cams:
        aim(cams[v], *VIEWS[v])
    d = os.path.join(TMP, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    from PIL import Image
    n = len(frames)
    hold = 0 if CLIPS[name]['loop'] else 8               # pause on the last frame before looping
    for i, (t, mats, P) in enumerate(frames):
        apply(OBJS, mats, balls[i])
        ims = []
        for v in ('front', 'game'):
            sc.camera = cams[v]
            p = os.path.join(d, '%s.png' % v)
            render_to(p)
            ims.append(Image.open(p).convert('RGB'))
        S = Image.new('RGB', (size * 2, size))
        S.paste(ims[0], (0, 0))
        S.paste(ims[1], (size, 0))
        S.save(os.path.join(d, 'f%04d.png' % i))
    for j in range(hold):
        shutil.copy(os.path.join(d, 'f%04d.png' % (n - 1)), os.path.join(d, 'f%04d.png' % (n + j)))
    out = os.path.join(OUT, name + '.gif')
    pal = os.path.join(d, 'pal.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(d, 'f%04d.png'),
                    '-vf', 'palettegen=max_colors=256:stats_mode=full', pal], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(d, 'f%04d.png'),
                    '-i', pal, '-lavfi', 'paletteuse=dither=sierra2_4a', '-loop', '0', out], check=True)
    mp4 = os.path.join(OUT, name + '.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(d, 'f%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', mp4], check=True)
    mid = Image.open(os.path.join(d, 'f%04d.png' % min(n - 1, int(round((CLIPS[name].get('contact') or 0) * FPS)))))
    mid.save(os.path.join(TMP, name + '_contact.png'))
    shutil.rmtree(d, ignore_errors=True)
    print('GIF', out, n, 'frames')


def key_timeline(objs):
    """every clip one after another on the timeline (30 fps, one key per frame), a marker per clip"""
    sc = bpy.context.scene
    sc.render.fps = FPS
    f = 1
    for name in ORDER:
        sc.timeline_markers.new(name, frame=f)
        for i, (t, mats, P) in enumerate(baked(name)):
            apply(objs, mats, None)
            for part, o in objs.items():
                if part == 'Ball':
                    continue
                o.rotation_mode = 'QUATERNION'
                o.rotation_quaternion = o.matrix_world.to_quaternion()
                o.keyframe_insert('location', frame=f + i)
                o.keyframe_insert('rotation_quaternion', frame=f + i)
            last = i
        f += last + 12
    sc.frame_start, sc.frame_end = 1, f


OBJS = None


def main():
    global OBJS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    OBJS = build_character()
    court()
    lights()
    names = ARGS[ARGS.index('clips') + 1].split(',') if 'clips' in ARGS else ORDER
    if 'sheet' in ARGS:
        views = ARGS[ARGS.index('views') + 1].split(',') if 'views' in ARGS else ('front', 'side', 'game')
        sheet(names, views)
        print('PREVIEW_OK')
        return
    if 'norender' not in ARGS:
        for name in names:
            gif(name)
    if names == ORDER:
        key_timeline(OBJS)
        for o in bpy.data.objects:
            if o.name.startswith(('G_', 'C_')):
                bpy.data.objects.remove(o)
        cam = camera('Camera')
        aim(cam, *VIEWS['front'])
        bpy.context.scene.camera = cam
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'TennisR6Animations.blend'))
    print('PREVIEW_OK')


main()
