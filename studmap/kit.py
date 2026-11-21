"""Reusable stud props (local space: origin = bottom centre, front = -Z). Everything is plain Parts with studs."""
import math
import random

from .core import Prop, cf, shade

WOOD = '#d9813f'
WOOD_DK = '#b4602c'
WHITE = '#f4f3fa'
ROCK = '#9d9ab8'
LEAF = '#3fae4e'
LEAF_LT = '#5dc65a'
TRUNK = '#8a5432'


def pine(h=18.0, seed=0, dark=LEAF, light=LEAF_LT, name='Pine'):
    """stacked square tiers, every other one turned 45 degrees, two greens"""
    rng = random.Random(seed)
    P = Prop(name)
    P.box((1.6, h * 0.34 + 0.6, 1.6), (0, h * 0.17 - 0.3, 0), TRUNK)
    n = 5
    w0 = h * rng.uniform(.48, .56)
    y = h * 0.2
    step = h * 0.74 / n
    for i in range(n):
        t = i / (n - 1)
        w = w0 * (1 - 0.72 * t)
        th = step * 1.25
        P.box((w, th, w), (0, y + th / 2, 0), dark if i % 2 == 0 else light, yaw=(45 if i % 2 else 0) + rng.uniform(-6, 6))
        y += step
    P.box((w0 * 0.16, h * 0.12, w0 * 0.16), (0, y + h * 0.04, 0), light, yaw=45)
    return P


def bush(seed=0, s=1.0, dark=LEAF, light=LEAF_LT, name='Bush'):
    rng = random.Random(seed)
    P = Prop(name)
    for i in range(3):
        w = rng.uniform(2.6, 3.8) * s
        P.box((w, w * .8, w), (rng.uniform(-1.2, 1.2) * s, w * .38 - .2, rng.uniform(-1.2, 1.2) * s),
              dark if i % 2 else light, yaw=rng.uniform(0, 90))
    return P


def rock(seed=0, s=1.0, color=ROCK, name='Rock'):
    rng = random.Random(seed)
    P = Prop(name)
    big = rng.uniform(3.2, 4.4) * s
    P.box((big, big * .8, big * 1.1), (0, big * .32, 0), color, yaw=rng.uniform(0, 90), pitch=rng.uniform(-6, 6))
    for _ in range(rng.randint(1, 2)):
        w = big * rng.uniform(.45, .65)
        a = rng.uniform(0, math.tau)
        P.box((w, w * .8, w), (math.cos(a) * big * .6, w * .3, math.sin(a) * big * .6), shade(color, .86),
              yaw=rng.uniform(0, 90), roll=rng.uniform(-8, 8))
    return P


def fence_loop(P, pts, gaps=(), color=WHITE, gap_post=6.0, h=3.4, closed=True):
    """white picket-style fence along a polyline of (x, z); gaps = [(segment index, t0, t1)] openings (0..1 along it)"""
    posts = set()

    def post(x, z):
        k = (round(x, 2), round(z, 2))
        if k in posts:
            return
        posts.add(k)
        P.box((0.8, h + 0.5, 0.8), (x, (h + 0.5) / 2 - 0.5, z), color, name='FencePost')
        P.box((1.1, 0.4, 1.1), (x, h + 0.2, z), color, name='FencePost')

    def run(a, b):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        n = max(1, math.ceil(L / gap_post))
        yaw = math.degrees(math.atan2(dx, dz))
        for i in range(n + 1):
            post(a[0] + dx * i / n, a[1] + dz * i / n)
        mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        for yy in (h * 0.42, h * 0.84):
            P.box((0.35, 0.55, L), (mx, yy, mz), color, yaw=yaw, name='FenceRail')

    segs = list(zip(pts, pts[1:] + (pts[:1] if closed else [])))
    for si, (a, b) in enumerate(segs):
        cuts = sorted([(t0, t1) for (i, t0, t1) in gaps if i == si])
        t = 0.0
        for t0, t1 in cuts:
            run((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0))
            t = t1
        run((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), b)
    return P


def gable_roof(w, d, rise, color=WOOD, ridge=WOOD_DK, overhang=1.0, slat=2.0, name='Roof'):
    """roof sitting on y = 0, ridge along Z: solid gable wedges + striped slats + ridge cap"""
    P = Prop(name)
    half = w / 2 + overhang
    L = d + 2 * overhang
    P.wedge((L, rise, half), (-half / 2, rise / 2, 0), shade(color, .82), yaw=90)
    P.wedge((L, rise, half), (half / 2, rise / 2, 0), shade(color, .82), yaw=-90)
    a = math.atan2(rise, half)
    slope = math.hypot(rise, half)
    n = max(2, round(L / slat))
    sw = L / n
    t = 0.45
    for side in (-1, 1):
        cx = side * half / 2 - side * math.sin(a) * t / 2
        cy = rise / 2 + math.cos(a) * t / 2 + 0.02
        for i in range(n):
            z = -L / 2 + sw * (i + .5)
            P.box((sw, t, slope + 0.2), (cx, cy, z), color if i % 2 == 0 else shade(color, .9),
                  yaw=-90 * side, pitch=-math.degrees(a))
    P.box((1.4, 1.0, L + 0.4), (0, rise + 0.3, 0), ridge)
    return P


def plank_wall(P, x0, x1, y0, y1, z, color, t=1.0, row=1.5, axis='x'):
    """wall of horizontal planks in two alternating shades (axis = direction the planks run)"""
    n = max(1, round((y1 - y0) / row))
    rh = (y1 - y0) / n
    for i in range(n):
        c = color if i % 2 == 0 else shade(color, .9)
        y = y0 + rh * (i + .5)
        if axis == 'x':
            P.box((x1 - x0, rh, t), ((x0 + x1) / 2, y, z), c, name='Wall')
        else:
            P.box((t, rh, x1 - x0), (z, y, (x0 + x1) / 2), c, name='Wall')
    return P


def hay(name='HayBale'):
    P = Prop(name)
    P.box((3.6, 2.4, 2.4), (0, 1.2, 0), '#f2c84b')
    P.box((3.7, 2.5, 0.35), (0, 1.2, -0.5), '#d9a93a')
    P.box((3.7, 2.5, 0.35), (0, 1.2, 0.5), '#d9a93a')
    return P


def crate(s=1.0, name='Crate'):
    P = Prop(name)
    a = 2.6 * s
    P.box((a, a, a), (0, a / 2, 0), '#c98a4b')
    for z in (-a / 2, a / 2):
        P.box((a + .1, .4 * s, .2), (0, a - .2 * s, z), '#9b6232')
        P.box((a + .1, .4 * s, .2), (0, .2 * s, z), '#9b6232')
    return P


def barrel(name='Barrel'):
    P = Prop(name)
    P.cyl(3.2, 1.25, (0, 1.6, 0), '#b8743d')
    for y in (.6, 2.6):
        P.cyl(.35, 1.32, (0, y, 0), '#6e6f80')
    return P


def barn(w=18.0, d=24.0, h=9.0, rise=6.0, wood='#d9773f', trim=WHITE, door='#d24a4a', name='Barn'):
    """long barn, gable end with a wide doorway facing -Z; doors swung open"""
    P = Prop(name)
    P.span(-w / 2, w / 2, -0.4, 0.4, -d / 2, d / 2, '#a8683c', name='Floor')
    dw, dh = 8.0, 7.0
    zf, zb = -d / 2 + .5, d / 2 - .5
    plank_wall(P, -w / 2, w / 2, 0.4, h, zb, wood)                                  # back
    plank_wall(P, -d / 2, d / 2, 0.4, h, -w / 2 + .5, wood, axis='z')              # sides
    plank_wall(P, -d / 2, d / 2, 0.4, h, w / 2 - .5, wood, axis='z')
    plank_wall(P, -w / 2 + 1, -dw / 2, 0.4, h, zf, wood)                            # front beside the door
    plank_wall(P, dw / 2, w / 2 - 1, 0.4, h, zf, wood)
    P.span(-dw / 2, dw / 2, dh, h, zf - .5, zf + .5, wood, name='Wall')
    for x in (-w / 2 + .5, w / 2 - .5):                                              # corner trims
        for z in (zf, zb):
            P.span(x - .7, x + .7, 0, h + .2, z - .7, z + .7, trim, name='Trim')
    P.span(-dw / 2 - .8, dw / 2 + .8, dh, dh + .8, zf - .8, zf - .3, trim, name='Trim')
    for x in (-dw / 2 - .4, dw / 2 + .4):
        P.span(x - .4, x + .4, 0, dh, zf - .8, zf - .3, trim, name='Trim')
    P.span(-dw - 1.2, dw + 1.2, dh + 1.0, dh + 1.6, zf - 1.4, zf - .8, '#5d5a78', name='DoorRail')
    for side in (-1, 1):                                                             # sliding doors pushed open
        x = side * (dw * .75 + .6)
        P.span(x - dw / 4, x + dw / 4, .2, dh + .9, zf - 1.5, zf - 1.0, door, name='Door')
        P.span(x - dw / 4, x + dw / 4, dh + .2, dh + .9, zf - 1.7, zf - 1.4, trim, name='Door')
        P.span(x - dw / 4, x + dw / 4, .2, .9, zf - 1.7, zf - 1.4, trim, name='Door')
        for xx in (x - dw / 4 + .25, x + dw / 4 - .25):
            P.span(xx - .25, xx + .25, .2, dh + .9, zf - 1.7, zf - 1.4, trim, name='Door')
        dg = math.degrees(math.atan2(dh - 1.0, dw / 2 - .5))
        L = math.hypot(dh - 1.0, dw / 2 - .5) - .3
        for s in (1, -1):
            P.box((L, .45, .3), (x, (dh + 1.1) / 2, zf - 1.55), trim, roll=s * dg, name='Door')
    P.span(-w / 2 - .2, w / 2 + .2, h, h + .5, -d / 2 - .2, d / 2 + .2, shade(wood, .8), name='Trim')
    P.put(gable_roof(w + .4, d + .4, rise, '#c95f37', WOOD_DK), cf(0, h + .5, 0))
    P.box((3.2, 3.2, .6), (0, h + .5 + rise * .45, -d / 2 - 1.3), trim, name='Window')
    P.box((2.2, 2.2, .7), (0, h + .5 + rise * .45, -d / 2 - 1.3), '#4a3a52', name='Window')
    for x, z in ((-3, 6), (-2, 2), (3, 7), (2.4, 9.6)):
        P.put(hay(), cf(x, .4, z, yaw=(x * 37) % 90))
    return P


def awning(P, w, depth, y, x=0.0, z=0.0, colors=('#ff8fb0', WHITE), stripes=7, pitch=22.0):
    """striped awning sloping down toward -Z from (x, y, z), scalloped hem"""
    sw = w / stripes
    a = math.radians(pitch)
    cz = z - math.cos(a) * depth / 2
    cy = y - math.sin(a) * depth / 2
    for i in range(stripes):
        P.box((sw, .4, depth), (x - w / 2 + sw * (i + .5), cy, cz), colors[i % 2], pitch=pitch, name='Awning')
    hz, hy = z - math.cos(a) * depth - .1, y - math.sin(a) * depth
    for i in range(stripes):
        P.box((sw * .8, 1.0, .3), (x - w / 2 + sw * (i + .5), hy - .5, hz), colors[i % 2], name='Awning')
    return P


def stall(accent='#ff8fb0', name='Stall', goods=('#e2483f', '#f39a2b', '#f4d03f', '#7bc043')):
    """market stall: counter with produce crates, posts, striped awning, blank sign"""
    P = Prop(name)
    w, d = 12.0, 6.0
    P.span(-w / 2, w / 2, 0, 3.4, -d / 2, -d / 2 + 2.4, WOOD, name='Counter')
    P.span(-w / 2 - .3, w / 2 + .3, 3.4, 3.9, -d / 2 - .3, -d / 2 + 2.7, WOOD_DK, name='Counter')
    for i in range(4):
        x = -w / 2 + 1.6 + i * (w - 3.2) / 3
        P.span(x - 1.2, x + 1.2, 3.9, 4.7, -d / 2 + .2, -d / 2 + 2.2, '#c98a4b', name='Crate')
        for k in range(3):
            P.box((.9, .9, .9), (x - .7 + k * .7, 5.1, -d / 2 + 1.2 + (k % 2) * .3), goods[i % len(goods)], name='Goods')
    for x in (-w / 2, w / 2):
        for z in (-d / 2 + .3, d / 2 - .3):
            P.span(x - .45, x + .45, 0, 9.5, z - .45, z + .45, WOOD_DK, name='Post')
    plank_wall(P, -w / 2, w / 2, 0, 9.5, d / 2 - .3, WOOD, t=.6)
    awning(P, w + 1.4, d + 1.8, 10.0, z=d / 2, colors=(accent, WHITE), stripes=7)
    P.span(-4, 4, 11.0, 13.4, d / 2 - .6, d / 2 - .1, WHITE, name='Sign')
    P.span(-3.4, 3.4, 11.3, 13.1, d / 2 - .8, d / 2 - .5, accent, name='Sign')
    return P


def lamp(glow='#ffe08a', post='#5d5a78', name='Lamp'):
    P = Prop(name)
    P.box((1.6, .8, 1.6), (0, .2, 0), post)
    P.box((.7, 9.0, .7), (0, 4.6, 0), post)
    P.box((1.8, .4, 1.8), (0, 9.2, 0), post)
    for dx, dz in ((-.7, -.7), (.7, -.7), (-.7, .7), (.7, .7)):
        P.box((.25, 1.8, .25), (dx, 10.3, dz), post)
    P.box((1.1, 1.6, 1.1), (0, 10.3, 0), glow, mat='neon', collide=False, shadow=False, name='LampGlow')
    P.box((2.0, .4, 2.0), (0, 11.4, 0), post)
    P.box((.8, .6, .8), (0, 11.9, 0), post)
    return P


def bench(name='Bench'):
    P = Prop(name)
    for x in (-2.4, 2.4):
        P.box((.5, 1.6, 1.8), (x, .8, 0), '#6e6f80')
    P.box((6.0, .4, 1.8), (0, 1.8, 0), WOOD)
    P.box((6.0, 1.2, .3), (0, 2.8, .8), WOOD)
    return P


def water_tank(glow='#5fe3ff', name='WaterTank'):
    P = Prop(name)
    P.poly([(math.cos(math.radians(22.5 + i * 45)) * 4.4, math.sin(math.radians(22.5 + i * 45)) * 4.4) for i in range(8)],
           1.0, 1.4, '#7c7a99', name='TankBase')
    for i in range(8):
        a = math.radians(i * 45)
        P.box((3.5, 3.6, .8), (math.cos(a) * 3.4, 2.8, math.sin(a) * 3.4), '#9f9dbb', yaw=-i * 45 + 90, name='TankWall')
    P.cyl(.3, 3.3, (0, 4.0, 0), '#4cc3ea', tr=.15, name='Water')
    P.cyl(.4, 3.9, (0, 4.7, 0), glow, mat='neon', collide=False, shadow=False, name='TankGlow')
    return P


def sign(accent='#ffd23c', name='Sign'):
    """blank sign board on two posts (add a SurfaceGui label in Studio)"""
    P = Prop(name)
    for x in (-2.6, 2.6):
        P.box((.6, 6.0, .6), (x, 2.6, 0), WOOD_DK)
    P.box((7.2, 3.2, .6), (0, 5.0, -.1), WOOD)
    P.box((6.2, 2.4, .2), (0, 5.0, -.5), accent, mat='smooth')
    return P


def leafy_tree(h=14.0, seed=0, leaf=LEAF_LT, leaf_dk=LEAF, trunk=TRUNK, name='Tree'):
    """voxel broadleaf: trunk + one big canopy cube + 3-4 smaller cubes round it, two greens"""
    rng = random.Random(seed)
    P = Prop(name)
    th = h * .45
    P.box((1.8, th + .6, 1.8), (0, th / 2 - .3, 0), trunk)
    s = h * .5
    cy = th + s * .42
    P.box((s, s * .85, s), (0, cy, 0), leaf, yaw=rng.uniform(-8, 8))
    for k in range(rng.choice((3, 4))):
        w = s * rng.uniform(.5, .66)
        a = rng.uniform(0, 6.283)
        P.box((w, w * .85, w), (math.cos(a) * s * .45, cy + rng.uniform(-s * .25, s * .3), math.sin(a) * s * .45),
              leaf_dk if k % 2 == 0 else leaf, yaw=rng.uniform(0, 90))
    return P


def arch(width=40.0, h=22.0, color='#f4f3fa', trim='#8d89cf', glow='#5fe3ff', name='Arch'):
    """two stacked-block towers and a beam with a neon strip across a track (opening = width)"""
    P = Prop(name)
    for side in (-1, 1):
        x = side * (width / 2 + 3)
        P.box((7, 2, 7), (x, 1, 0), trim)
        P.box((6, h - 4, 6), (x, h / 2, 0), color)
        P.box((7.4, 1.6, 7.4), (x, h * .35, 0), trim)
        P.box((7.4, 2.4, 7.4), (x, h - 1, 0), trim)
        P.box((4.4, 3, 4.4), (x, h + 1.5, 0), color, yaw=45)
        P.box((2, 2, 2), (x, h + 3.8, 0), glow, mat='neon', collide=False, shadow=False)
    P.box((width + 6, 3, 4), (0, h - 1.5, 0), color)
    P.box((width + 6.4, .8, 4.4), (0, h + .2, 0), trim)
    P.box((width - 2, .8, .4), (0, h - 1.5, -2.2), glow, mat='neon', collide=False, shadow=False)
    return P


def chevron(color='#7dff6a', s=1.0, name='SpeedPad'):
    """flat neon arrow pointing to -Z"""
    P = Prop(name)
    for side in (-1, 1):
        P.box((1.6 * s, .3, 7 * s), (side * 2.2 * s, .15, 0), color, yaw=side * 40, mat='neon', collide=False, shadow=False)
    return P
