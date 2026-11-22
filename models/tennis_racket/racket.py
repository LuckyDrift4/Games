"""Realistic tennis racket in headless Blender (bpy): model, studio renders and a Roblox-ready GLB.

    python models/tennis_racket/racket.py [-- norender] [-- shots hero,front]     (Blender's bpy module)
    blender -b --factory-startup --python models/tennis_racket/racket.py -- ...   (same, with a Blender install)

Model space: metres, Blender Z up. The racket stands on its butt cap at the origin, string plane = XZ, depth = Y.
Real proportions: 68.6 cm long, 100 sq in head (34 x 25.5 cm outside), 23 mm beam, 16 x 19 string pattern woven
over / under, 4 3/8 grip with a wound overgrip. Every part is its own mesh (one Roblox MeshPart each, < 20k tris).
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'out', 'tennis_racket')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
STUDS_LONG = 3.0                         # exported length in Roblox studs (real proportions, sized for an avatar)

# ------------------------------------------------------------------ dimensions (metres)
A, B, ZC, NSE, EGG = .1675, .1210, .5125, 2.35, .06      # head centreline: half length, half width, centre, shape
Z_JUNCTION = .405                                          # where the throat arms leave the head hoop
XS = .0072                                                 # shaft rail centre (two rails make the 29 mm shaft)
Z_SHAFT = .205                                             # throat arms end / shaft starts
Z_BRIDGE = .382                                            # throat bridge centreline (middle)
STRING_R, WEAVE = .00064, .00062                           # 1.28 mm strings, over / under offset
N_MAINS, N_CROSSES = 16, 19
GRIP_Z0, GRIP_Z1 = .012, .186

COL = {                                                    # linear RGB, roughness, metallic, coat
    'frame':   ((.006, .006, .008), .25, 0.0, 1.0),
    'accent':  ((.010, .095, .620), .30, .45, .9),
    'stripe':  ((.80, .80, .82), .28, .6, .6),
    'bumper':  ((.022, .022, .026), .72, 0.0, 0.0),
    'grommet': ((.012, .012, .014), .55, 0.0, 0.0),
    'string':  ((.78, .75, .62), .38, 0.0, .3),
    'grip':    ((.82, .84, .86), .88, 0.0, 0.0),
    'tape':    ((.008, .008, .009), .30, 0.0, .6),
    'damp':    ((.85, .32, .012), .60, 0.0, 0.0),
}


# ------------------------------------------------------------------ curves
def head(t):
    """head centreline in (x, z); t = 0 at the top, t > 0 on the +x side"""
    c, s = math.cos(t), math.sin(t)
    x = B * math.copysign(abs(s) ** (2 / NSE), s)
    z = ZC + A * math.copysign(abs(c) ** (2 / NSE), c)
    x *= 1 + EGG * (z - ZC) / A
    return Vector((x, z))


def head_t_at(z_target):
    """t on the +x side where the head centreline reaches z_target (lower half)"""
    lo, hi = math.pi / 2, math.pi
    for _ in range(60):
        mid = (lo + hi) / 2
        if head(mid).y > z_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def bezier(p0, p1, p2, p3, n):
    return [p0 * (1 - u) ** 3 + p1 * 3 * u * (1 - u) ** 2 + p2 * 3 * u * u * (1 - u) + p3 * u ** 3
            for u in [i / n for i in range(n + 1)]]


def resample(pts, step):
    """even spacing along a 2D/3D polyline (keeps both ends)"""
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + (b - a).length)
    n = max(2, int(round(d[-1] / step)) + 1)
    out, j = [], 0
    for i in range(n):
        s = d[-1] * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        u = (s - d[j]) / max(1e-12, d[j + 1] - d[j])
        out.append(pts[j].lerp(pts[j + 1], min(1.0, max(0.0, u))))
    return out


def frame_path():
    """one continuous centreline: right rail up, right arm, hoop over the top, left arm, left rail down.
    Returns [(point2d, region, t)] with region in rail / arm / hoop (t = head parameter on the hoop)"""
    tR = head_t_at(Z_JUNCTION)
    dense = [head(tR - (2 * tR) * i / 2000) for i in range(2001)]
    hoop = resample(dense, .0042)
    eps = 1e-4
    tan_out = (head(tR - eps) - head(tR)).normalized()        # direction the path takes leaving J_R over the top
    J = head(tR)
    S = Vector((XS, Z_SHAFT))
    arm_r = resample(bezier(S, S + Vector((0, .085)), J - tan_out * .07, J, 400), .0042)
    rail_r = resample([Vector((XS, .03)), S], .006)
    arm_l = [Vector((-p.x, p.y)) for p in reversed(arm_r)]
    rail_l = [Vector((-p.x, p.y)) for p in reversed(rail_r)]
    out = [(p, 'rail', 0.0) for p in rail_r[:-1]] + [(p, 'arm', 0.0) for p in arm_r[:-1]]
    for i, p in enumerate(hoop):
        out.append((p, 'hoop', tR - 2 * tR * i / (len(hoop) - 1)))
    out += [(p, 'arm', 0.0) for p in arm_l[1:]] + [(p, 'rail', 0.0) for p in rail_l[1:]]
    return out, tR


# ------------------------------------------------------------------ mesh helpers
class Mesh:
    def __init__(self):
        self.v, self.f = [], []

    def add_v(self, p):
        self.v.append(tuple(p))
        return len(self.v) - 1

    def obj(self, name, mat, smooth=True, coll=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(me)
        bm.free()
        me.update()
        if smooth:
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(40))   # keeps tape steps / beam edges crisp (no shading artefacts)
        me.materials.append(MATS[mat])
        o = bpy.data.objects.new(name, me)
        (coll or RACKET).objects.link(o)
        o.parent = ROOT_EMPTY
        return o


def profile(hw, hd, stripe=.0009, corner=.55):
    """rounded-rectangle cross-section in (n, y): n = in-plane outward, y = depth. Returns points + edge labels"""
    rc = min(hw, hd) * corner
    pts, lab = [], []

    def arc(cx, cy, a0):
        for k in range(1, 3):
            a = math.radians(a0 + 30 * k)
            pts.append((cx + math.cos(a) * rc, cy + math.sin(a) * rc)); lab.append('corner')
    pts += [(hw, -(hd - rc)), (hw, 0), (hw, hd - rc)]; lab += ['outer', 'outer', 'outer']
    arc(hw - rc, hd - rc, 0)
    pts += [(hw - rc, hd), (stripe, hd), (-stripe, hd), (-(hw - rc), hd)]; lab += ['front', 'fstripe', 'front', 'front']
    arc(-(hw - rc), hd - rc, 90)
    pts += [(-hw, hd - rc), (-hw, 0), (-hw, -(hd - rc))]; lab += ['inner', 'inner', 'inner']
    arc(-(hw - rc), -(hd - rc), 180)
    pts += [(-(hw - rc), -hd), (-stripe, -hd), (stripe, -hd), (hw - rc, -hd)]; lab += ['back', 'bstripe', 'back', 'back']
    arc(hw - rc, -(hd - rc), 270)
    return pts, lab


def sweep(meshes, path, prof_fn, mat_fn, close_ends=False):
    """sweep a varying cross-section along a 2D path in the XZ plane; mat_fn picks the mesh for each quad"""
    n = len(path)
    rings = []
    for i, (p, region, t) in enumerate(path):
        a = path[max(0, i - 1)][0]
        b = path[min(n - 1, i + 1)][0]
        T = (b - a).normalized()
        N = Vector((T.y, -T.x))                            # in-plane outward normal (path runs clockwise)
        pts, lab = prof_fn(region, t, p)
        rings.append((p, N, pts, lab, region, t))
    for i in range(n - 1):
        p0, N0, pts0, lab, region, t = rings[i]
        p1, N1, pts1, _, region1, t1 = rings[i + 1]
        k = len(pts0)
        for j in range(k):
            m = mat_fn(lab[j], region if region == region1 else 'rail', (t + t1) / 2)
            M = meshes[m]
            quad = []
            for (pp, NN, pts) in ((p0, N0, pts0), (p1, N1, pts1)):
                for jj in (j, (j + 1) % k):
                    nn, yy = pts[jj]
                    quad.append(M.add_v((pp.x + NN.x * nn, yy, pp.y + NN.y * nn)))
            M.f.append((quad[0], quad[2], quad[3], quad[1]))


def tube(M, pts, r, sides=6):
    """round tube through 3D points (parallel-transport frames)"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    T = [(pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized() for i in range(n)]
    up = Vector((0, 1, 0)) if abs(T[0].y) < .9 else Vector((1, 0, 0))
    U = [T[0].cross(up).normalized()]
    for i in range(1, n):
        u = U[-1] - T[i] * U[-1].dot(T[i])
        U.append(u.normalized())
    rings = []
    for i in range(n):
        V = T[i].cross(U[i])
        rings.append([M.add_v(pts[i] + (U[i] * math.cos(a) + V * math.sin(a)) * r)
                      for a in [k * math.tau / sides for k in range(sides)]])
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            M.f.append((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    M.f.append(tuple(reversed(rings[0])))
    M.f.append(tuple(rings[-1]))


def chaikin(poly, it=2):
    for _ in range(it):
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            out += [a.lerp(b, .25), a.lerp(b, .75)]
        poly = out
    return poly


def octagon(ax, ay):
    """elongated grip octagon (half across-flats ax in x, ay in y), rounded bevels"""
    s = math.tan(math.radians(22.5))
    pts = [Vector((ax, -ay * s)), Vector((ax, ay * s)), Vector((ax * s, ay)), Vector((-ax * s, ay)),
           Vector((-ax, ay * s)), Vector((-ax, -ay * s)), Vector((-ax * s, -ay)), Vector((ax * s, -ay))]
    return chaikin(pts, 2)


def loft(M, rings_xy_z, cap0=True, cap1=True):
    """rings of (x, y) at heights z -> closed side wall"""
    idx = []
    for ring, z in rings_xy_z:
        idx.append([M.add_v((p.x, p.y, z)) for p in ring])
    k = len(idx[0])
    for i in range(len(idx) - 1):
        for j in range(k):
            j2 = (j + 1) % k
            M.f.append((idx[i][j], idx[i][j2], idx[i + 1][j2], idx[i + 1][j]))
    if cap0:
        M.f.append(tuple(reversed(idx[0])))
    if cap1:
        M.f.append(tuple(idx[-1]))


# ------------------------------------------------------------------ materials
MATS = {}


def make_materials():
    for k, (c, rough, metal, coat) in COL.items():
        m = bpy.data.materials.new('M_' + k)
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*c, 1)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = .04
        MATS[k] = m
    # render-only surface detail (glTF keeps only colour / roughness / metal)
    g = MATS['grip'].node_tree
    tex = g.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 900; tex.inputs['Detail'].default_value = 6
    bump = g.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .25
    g.links.new(tex.outputs['Fac'], bump.inputs['Height']); g.links.new(bump.outputs['Normal'], g.nodes['Principled BSDF'].inputs['Normal'])
    s = MATS['string'].node_tree.nodes['Principled BSDF']
    s.inputs['Sheen Weight'].default_value = .4


# ------------------------------------------------------------------ build
def build():
    path, tR = frame_path()

    def prof(region, t, p):
        if region == 'hoop':
            side = abs(math.sin(t))                          # 0 at top / bottom, 1 at 3 and 9 o'clock
            low = max(0.0, (abs(t) - 2.0) / (tR - 2.0)) if abs(t) > 2.0 else 0.0
            return profile(.0062, .0117 + .0006 * side + .0007 * low)
        if region == 'arm':
            u = (p.y - Z_SHAFT) / (Z_JUNCTION - Z_SHAFT)
            return profile(.0072 + .0004 * u, .0124)
        return profile(.0072, .0122)

    def mat(label, region, t):
        if region == 'hoop':
            if label in ('fstripe', 'bstripe'):
                return 'stripe'
            if 1.05 < abs(t) < 2.05 and label != 'inner':
                return 'accent'
            return 'frame'
        if region == 'arm':
            return 'frame' if label == 'inner' else 'accent'
        return 'frame'

    meshes = {'frame': Mesh(), 'accent': Mesh(), 'stripe': Mesh()}
    sweep(meshes, path, prof, mat)

    # throat bridge between the inner edges of the two arms, bowed slightly toward the handle
    arm_pts = [p for p, r, _ in path if r == 'arm' and p.x > 0]
    arm_x = min(arm_pts, key=lambda q: abs(q.y - Z_BRIDGE)).x
    xe = arm_x - .002
    bpath = [(Vector((x, Z_BRIDGE - .005 * (1 - (x / xe) ** 2))), 'bridge', 0.0) for x in
             [xe - 2 * xe * i / 48 for i in range(49)]]
    sweep(meshes, bpath, lambda r, t, p: profile(.0062, .0113), lambda l, r, t: 'frame')

    # string-bed boundary: inner edges of hoop, arms, top edge of the bridge
    inner = []
    for i, (p, region, t) in enumerate(path):
        if region in ('hoop', 'arm') and p.y > Z_BRIDGE - .02:
            a = path[max(0, i - 1)][0]; b = path[min(len(path) - 1, i + 1)][0]
            T = (b - a).normalized()
            inner.append(p - Vector((T.y, -T.x)) * .0062)
    bridge_top = [Vector((q.x, q.y + .0062)) for q, _, _ in bpath]
    segs = list(zip(inner, inner[1:])) + list(zip(bridge_top, bridge_top[1:]))

    def hits_v(x):
        zs = []
        for a, b in segs:
            if (a.x - x) * (b.x - x) <= 0 and a.x != b.x:
                zs.append(a.y + (b.y - a.y) * (x - a.x) / (b.x - a.x))
        return zs

    def hits_h(z):
        xs = []
        for a, b in segs:
            if (a.y - z) * (b.y - z) <= 0 and a.y != b.y:
                xs.append(a.x + (b.x - a.x) * (z - a.y) / (b.y - a.y))
        return xs

    dx = .0127
    mains_x = [(i - (N_MAINS - 1) / 2) * dx for i in range(N_MAINS)]
    z_lo = Z_BRIDGE + .0062 + .0095
    z_hi = ZC + A - .0062 - .0085
    dz = (z_hi - z_lo) / (N_CROSSES - 1)
    cross_z = [z_lo + j * dz for j in range(N_CROSSES)]
    mains, crosses, grom = Mesh(), Mesh(), Mesh()
    ends = []
    for i, x in enumerate(mains_x):
        zs = hits_v(x)
        top = max(zs)
        bot = max(z for z in zs if z < ZC)
        zz = [bot - .005] + [z for z in [cross_z[0] + k * dz / 2 for k in range(-8, 2 * N_CROSSES + 8)]
                             if bot - .005 < z < top + .005] + [top + .005]
        pts = [(x, WEAVE * (-1) ** i * math.cos(math.pi * (z - cross_z[0]) / dz), z) for z in zz]
        tube(mains, pts, STRING_R, 6)
        ends += [((x, 0, top), (0, 0, 1)), ((x, 0, bot), (0, 0, -1))]
    for j, z in enumerate(cross_z):
        xs = hits_h(z)
        right = min(v for v in xs if v > 0)
        left = max(v for v in xs if v < 0)
        xx = [left - .005] + [x for x in [mains_x[0] + k * dx / 2 for k in range(-8, 2 * N_MAINS + 8)]
                              if left - .005 < x < right + .005] + [right + .005]
        pts = [(x, -WEAVE * (-1) ** j * math.cos(math.pi * (x - mains_x[0]) / dx), z) for x in xx]
        tube(crosses, pts, STRING_R, 6)
        ends += [((right, 0, z), (1, 0, 0)), ((left, 0, z), (-1, 0, 0))]
    for (p, d) in ends:                                  # grommet collars where the strings enter the frame
        p, d = Vector(p), Vector(d)
        tube(grom, [p - d * .0012, p + d * .0004], .00155, 8)

    # bumper guard over the top, grommet strip down the sides (sit on the outer face)
    bump, gstrip = {'b': Mesh()}, {'g': Mesh()}
    hoop = [(p, r, t) for p, r, t in path if r == 'hoop']

    def offset_prof(n0, hn, hd):
        def f(region, t, p):
            pts, lab = profile(hn, hd, stripe=.0003, corner=.8)
            return [(nn + n0, yy) for nn, yy in pts], lab
        return f
    top = [h for h in hoop if abs(h[2]) < .62]
    sides = [h for h in hoop if .58 < abs(h[2]) < tR - .25]
    sweep(bump, top, offset_prof(.0062 + .0016, .0019, .0089), lambda l, r, t: 'b')
    right_side = [h for h in sides if h[2] > 0]
    left_side = [h for h in sides if h[2] < 0]
    for part in (right_side, left_side):
        sweep(gstrip, part, offset_prof(.0062 + .0008, .0010, .0060), lambda l, r, t: 'g')

    # grip: wound overgrip (sawtooth ridge along a helix), finishing tape, butt cap + end logo
    base = octagon(.0158, .0172)
    nrm = []
    for i, p in enumerate(base):
        a, b = base[i - 1], base[(i + 1) % len(base)]
        t2 = (b - a).normalized()
        nrm.append(Vector((t2.y, -t2.x)))
    grip = Mesh()
    rings = []
    nz = int((GRIP_Z1 - GRIP_Z0) / .0017)
    for r in range(nz + 1):
        z = GRIP_Z0 + (GRIP_Z1 - GRIP_Z0) * r / nz
        ring = []
        for p, n in zip(base, nrm):
            th = math.atan2(p.y, p.x) / math.tau
            ph = ((z - GRIP_Z0) / .0215 + th) % 1.0
            d = .0005 + .0009 * ph ** 1.3
            ring.append(p + n * d)
        rings.append((ring, z))
    loft(grip, rings)
    tape = Mesh()
    tr = [p + n * .0016 for p, n in zip(base, nrm)]
    loft(tape, [([p + n * .0012 for p, n in zip(base, nrm)], GRIP_Z1 - .002), (tr, GRIP_Z1 + .006),
                ([p + n * .0008 for p, n in zip(base, nrm)], GRIP_Z1 + .011)])
    cap = Mesh()
    loft(cap, [([p + n * .0021 for p, n in zip(base, nrm)], -.0035), ([p + n * .0026 for p, n in zip(base, nrm)], .002),
               ([p + n * .0020 for p, n in zip(base, nrm)], .009), ([p + n * .0012 for p, n in zip(base, nrm)], .0135)])
    logo = Mesh()
    loft(logo, [([p * .62 for p in base], -.0042), ([p * .62 for p in base], -.0034)])

    # string dampener: a small rubber button between the two centre mains above the bridge
    damp = Mesh()
    zc = z_lo + .012
    dpoly = chaikin([Vector((-.0105, -.0055)), Vector((.0105, -.0055)), Vector((.0105, .0055)), Vector((-.0105, .0055))], 3)
    for sgn in (-1, 1):
        rings = [[damp.add_v((p.x * k, sgn * y, zc + p.y * k)) for p in dpoly] for (y, k) in ((.0011, 1.0), (.0040, 1.0), (.0050, .8))]
        n = len(dpoly)
        for a, b in zip(rings, rings[1:]):
            for j in range(n):
                damp.f.append((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
        damp.f.append(tuple(rings[0])); damp.f.append(tuple(reversed(rings[-1])))

    parts = [('Frame', meshes['frame'], 'frame'), ('FrameAccent', meshes['accent'], 'accent'),
             ('FrameStripe', meshes['stripe'], 'stripe'), ('Bumper', bump['b'], 'bumper'),
             ('GrommetStrip', gstrip['g'], 'grommet'), ('Grommets', grom, 'grommet'),
             ('StringsMains', mains, 'string'), ('StringsCrosses', crosses, 'string'),
             ('Grip', grip, 'grip'), ('GripTape', tape, 'tape'), ('ButtCap', cap, 'frame'),
             ('ButtLogo', logo, 'accent'), ('Dampener', damp, 'damp')]
    return [M.obj(name, mat) for name, M, mat in parts]


# ------------------------------------------------------------------ studio (renders only)
def tennis_ball(coll):
    r = .0335
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=r)
    me = bpy.data.meshes.new('Ball'); bm.to_mesh(me); bm.free(); me.shade_smooth()
    m = bpy.data.materials.new('M_ball'); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.42, .72, .012, 1); b.inputs['Roughness'].default_value = .95
    b.inputs['Sheen Weight'].default_value = 1.0; b.inputs['Sheen Roughness'].default_value = .6
    b.inputs['Sheen Tint'].default_value = (.9, 1, .6, 1)
    nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 600; tex.inputs['Detail'].default_value = 8
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .5
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    me.materials.append(m)
    ball = bpy.data.objects.new('Ball', me); coll.objects.link(ball)
    seam = Mesh()
    a, bb = .68, .32
    pts = []
    for i in range(241):
        th = i * math.tau / 240
        v = Vector((a * math.cos(th) + bb * math.cos(3 * th), a * math.sin(th) - bb * math.sin(3 * th),
                    2 * math.sqrt(a * bb) * math.sin(2 * th))).normalized() * (r + .0002)
        pts.append(v)
    tube(seam, pts, .0016, 8)
    sme = bpy.data.meshes.new('Seam'); sme.from_pydata(seam.v, [], seam.f); sme.shade_smooth()
    sm = bpy.data.materials.new('M_seam'); sb = sm.node_tree.nodes['Principled BSDF']
    sb.inputs['Base Color'].default_value = (.85, .86, .8, 1); sb.inputs['Roughness'].default_value = .8
    sme.materials.append(sm)
    so = bpy.data.objects.new('Seam', sme); coll.objects.link(so); so.parent = ball
    return ball


def studio():
    sc = bpy.context.scene
    coll = bpy.data.collections.new('Studio'); sc.collection.children.link(coll)
    M = Mesh()                                           # seamless sweep: floor curving up into a back wall
    prof = [(y, 0.0) for y in [-3 + i * .2 for i in range(21)]]
    for k in range(1, 13):
        a = math.radians(90 * k / 12)
        prof.append((1.0 + math.sin(a) * 1.2, 1.2 - math.cos(a) * 1.2))
    prof += [(2.2, 1.2 + i * .4) for i in range(1, 8)]
    rows = [[M.add_v((x, y, z)) for (y, z) in prof] for x in (-5, 5)]
    for j in range(len(prof) - 1):
        M.f.append((rows[0][j], rows[1][j], rows[1][j + 1], rows[0][j + 1]))
    me = bpy.data.meshes.new('Sweep'); me.from_pydata(M.v, [], M.f); me.shade_smooth()
    m = bpy.data.materials.new('M_sweep'); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.16, .165, .175, 1); b.inputs['Roughness'].default_value = .6
    me.materials.append(m)
    coll.objects.link(bpy.data.objects.new('Sweep', me))
    for name, loc, energy, size, col in (('Key', (-1.3, -1.6, 1.9), 95, 1.4, (1, .97, .92)),
                                          ('Fill', (1.6, -1.3, .9), 22, 1.6, (.9, .95, 1)),
                                          ('Rim', (.7, 1.3, 1.6), 70, .8, (1, 1, 1))):
        L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = col
        o = bpy.data.objects.new(name, L); coll.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, .35)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('W'); sc.world = w
    w.node_tree.nodes['Background'].inputs[0].default_value = (.025, .027, .032, 1)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    return coll


def shot(name, cam_loc, target, lens, pose, ball=None, dof=None, res=(1600, 1000)):
    sc = bpy.context.scene
    ROOT_EMPTY.matrix_world = pose
    for o in [BALL] + list(BALL.children):
        o.hide_render = ball is None
    if ball is not None:
        BALL.location = ball
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = lens; cam.data.clip_start = .01
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.use_dof = dof is not None
    if dof:
        cam.data.dof.focus_distance = (Vector(target) - Vector(cam_loc)).length
        cam.data.dof.aperture_fstop = dof
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, 'previews', name + '.png')
    bpy.ops.render.render(write_still=True)
    print('SHOT', name)


# ------------------------------------------------------------------ export
def export_glb(objs):
    """GLB in Roblox studs (racket STUDS_LONG long), Y up; one mesh per part"""
    s = STUDS_LONG / .686
    ROOT_EMPTY.matrix_world = Matrix.Identity(4)
    tmp = []
    for o in objs:
        name = o.name
        o.name = name + '_src'
        me = o.data.copy()
        me.transform(Matrix.Scale(s, 4))
        c = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(c)
        tmp.append(c)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for c in tmp:
        c.select_set(True)
    bpy.context.view_layer.objects.active = tmp[0]
    path = os.path.join(OUT, 'TennisRacket.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_materials='EXPORT')
    tris = {c.name: sum(len(p.vertices) - 2 for p in c.data.polygons) for c in tmp}
    for c in tmp:
        bpy.data.objects.remove(c)
    for o in objs:
        o.name = o.name[:-4]
    return path, tris


# ------------------------------------------------------------------ main
bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(os.path.join(OUT, 'previews'), exist_ok=True)
RACKET = bpy.data.collections.new('Racket'); bpy.context.scene.collection.children.link(RACKET)
ROOT_EMPTY = bpy.data.objects.new('TennisRacket', None); RACKET.objects.link(ROOT_EMPTY)
make_materials()
OBJS = build()
glb, tris = export_glb(OBJS)
print('GLB', glb, 'tris', sum(tris.values()), tris)
assert max(tris.values()) <= 20000, 'a part is over the Roblox 20k triangle MeshPart limit'

if 'norender' not in ARGS:
    studio_coll = studio()
    BALL = tennis_ball(studio_coll)
    only = ARGS[ARGS.index('shots') + 1].split(',') if 'shots' in ARGS else None
    hd = .0125
    lying = lambda yaw, x, y: Matrix.Translation((x, y, .0195)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-90), 4, 'X')
    upright = lambda yaw: Matrix.Rotation(math.radians(yaw), 4, 'Z')
    SHOTS = [
        ('hero', dict(cam_loc=(.56, .64, .74), target=(-.2, .13, .0), lens=40, pose=lying(28, -.05, -.18),
                      ball=(.03, .33, .0335))),
        ('front', dict(cam_loc=(0, -2.95, .40), target=(0, 0, .35), lens=75, pose=upright(10))),
        ('angle', dict(cam_loc=(1.15, -2.55, .62), target=(0, 0, .35), lens=85, pose=upright(-38))),
        ('strings', dict(cam_loc=(.16, -.36, .5), target=(.0, .0, .43), lens=100, pose=upright(14), dof=3.2)),
        ('grip', dict(cam_loc=(.2, -.34, .2), target=(0, 0, .1), lens=100, pose=upright(-24), dof=4.0)),
    ]
    for name, kw in SHOTS:
        if only is None or name in only:
            shot(name, **kw)
print('RACKET_OK')
