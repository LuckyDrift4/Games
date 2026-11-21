"""Plot Isles (detailed): eight identical player plot islands in a tropical sea, joined to a main road island.

Layout: a long road island runs east-west; four plots north of it, four south, each reached by a plank bridge. The
spawn hub at the west end has a lighthouse, coin fountain, Shop / Index / Rebirth huts and leaderboards.
Each plot: stepped beach, paved spine from its gate (laser lock + owner billboard) to a conveyor with a spawn portal
and exit tunnel, eight pedestal pads with collect buttons, tiki torches, palms, flowers, beach props.
Sea: transparent water over sand shelves (turquoise shallows), foam lines, islets, boats, buoys.
Roblox space, studs, front = -Z. Terrain and paths are stud Plastic; organic props SmoothPlastic.
"""
import math
import random

from studmap.core import Group, Prop, cf, ngon, shade, yaw_to
from studmap import kit

NAME = 'PlotIsles'

WATER = '#45b8ee'
DEEP = '#2471b6'
SHELF = '#d8cf9c'
FOAM = '#f4fbff'
WET = '#d9c38f'
SAND = '#f1dfae'
GRASS = '#72d457'
GRASS_LT = '#86e066'
GRASS_DK = '#5fc24a'
ROAD = '#6f5142'
TILE = '#9a7560'
TILE_LT = '#a9826b'
KERB = '#d8d4e6'
STONE = '#8d8aa8'
METAL = '#4b4b5e'
WOOD = '#b27a4a'
WOOD_DK = '#8a5a34'
GOLD = '#f5c53a'

XS = [-165, -55, 55, 165]
ROW_Z = 95
HW, HD = 48, 60                 # plot dry-sand half extents
GW, GD = 42, 54                 # plot grass half extents
ACCENTS = ['#ff5d6c', '#ff9f43', '#ffd23c', '#5fd35a', '#4d96ff', '#9d79f2', '#ff7ad1', '#3fd6c6']


def smooth(P):
    for p in P.parts:
        if p.mat == 'plastic':
            p.mat = 'smooth'
        p.studs = False
    return P


def nocollide(P):
    for p in P.parts:
        p.collide = False
    return P


# ------------------------------------------------------------------ small props
def palm(h=17.0, seed=0, name='Palm'):
    """curved banded trunk, drooping 3-segment fronds, coconuts"""
    rng = random.Random(seed)
    P = Prop(name)
    n = 7
    lean = rng.uniform(.22, .38) * h
    pts = [(lean * (k / n) ** 2, h * k / n) for k in range(n + 1)]
    for k in range(n):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(x1 - x0, y1 - y0))
        w = 1.9 - k * .1
        P.box((w, L + .25, w), ((x0 + x1) / 2, (y0 + y1) / 2, 0), '#b98a5c' if k % 2 else '#a8784f', roll=-ang)
        P.box((w + .25, .35, w + .25), (x1, y1 - .2, 0), '#8f6440', roll=-ang)
    tx, ty = pts[-1]
    P.box((2.6, 1.6, 2.6), (tx, ty + .3, 0), '#6b8f3a', yaw=45)
    for k in range(8):
        a = k * 45 + rng.uniform(-12, 12)
        yaw = -a - 90
        x, y, z = tx, ty + .6, 0.0
        for s, (L, w, pitch) in enumerate(((3.4, 2.6, -8), (3.2, 2.0, -28), (2.8, 1.3, -52))):
            p, yw = math.radians(pitch), math.radians(yaw)
            d = (-math.cos(p) * math.sin(yw), math.sin(p), -math.cos(p) * math.cos(yw))
            c = (x + d[0] * L / 2, y + d[1] * L / 2, z + d[2] * L / 2)
            col = ('#3fbf4f', '#4fcd58', '#62d965')[s] if k % 2 else ('#36ad46', '#45bd4f', '#56cb5b')[s]
            P.box((w, .3, L + .2), c, col, yaw=yaw, pitch=pitch)
            x, y, z = x + d[0] * L, y + d[1] * L, z + d[2] * L
    for k in range(3):
        r = math.radians(k * 120 + 20)
        P.ball(1.1, (tx + math.cos(r) * 1.0, ty - .6, math.sin(r) * 1.0), '#7a5235')
    return smooth(P)


def flowers(seed=0, name='Flowers'):
    rng = random.Random(seed)
    P = Prop(name)
    cols = ['#ff6fa8', '#ffd23c', '#ffffff', '#b48cff', '#ff5d5d', '#ff9f43']
    for _ in range(rng.randint(4, 7)):
        x, z = rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2)
        h = rng.uniform(.6, 1.2)
        P.box((.25, h, .25), (x, h / 2, z), '#3fa83c')
        P.box((.8, .5, .8), (x, h + .2, z), rng.choice(cols), yaw=rng.uniform(0, 90))
        P.box((1.0, .2, .5), (x, .25, z), '#4fbf45', yaw=rng.uniform(0, 180))
    return nocollide(smooth(P))


def tuft(seed=0, name='GrassTuft'):
    rng = random.Random(seed)
    P = Prop(name)
    for _ in range(rng.randint(3, 5)):
        h = rng.uniform(1.0, 1.9)
        P.box((.3, h, .3), (rng.uniform(-.6, .6), h / 2 - .1, rng.uniform(-.6, .6)), rng.choice((GRASS_LT, GRASS_DK, '#9ae874')),
              pitch=rng.uniform(-18, 18), roll=rng.uniform(-18, 18))
    return nocollide(smooth(P))


def rock(seed=0, s=1.0):
    return smooth(kit.rock(seed=seed, s=s, color='#a3a1b8'))


def tiki(name='TikiTorch'):
    P = Prop(name)
    P.box((.7, 6.4, .7), (0, 3.0, 0), WOOD)
    for y in (1.6, 4.2):
        P.box((.9, .3, .9), (0, y, 0), WOOD_DK)
    P.box((1.6, 1.0, 1.6), (0, 6.6, 0), '#5a3a26', yaw=45)
    P.box((1.1, 1.6, 1.1), (0, 7.8, 0), '#ff7a1a', yaw=45, mat='neon', collide=False, shadow=False, name='TikiFlame')
    P.box((.55, 2.2, .55), (0, 8.2, 0), '#ffd23c', yaw=45, mat='neon', collide=False, shadow=False, name='TikiFlame')
    return P


def umbrella(c1='#ff5d6c', c2='#ffffff', name='BeachUmbrella'):
    P = Prop(name)
    P.box((.35, 8.6, .35), (0, 3.8, 0), '#f4f3fa', pitch=6)
    top = (0, 8.1, -.45)
    for k in range(8):
        a = k * 45
        r = math.radians(a)
        P.box((2.2, .25, 4.6), (top[0] + math.sin(r) * 2.1, top[1] - .7, top[2] - math.cos(r) * 2.1), c1 if k % 2 else c2,
              yaw=-a, pitch=-18)
    P.ball(.8, (top[0], top[1] + .2, top[2]), c1)
    for i, c in enumerate((c1, '#ffffff', c1)):
        P.span(1.4 + i * 1.2, 2.6 + i * 1.2, .8, .95, -3.2, 3.2, c, name='Towel')
    P.span(-4.2, -2.2, .8, 1.7, -2.6, 2.4, '#4d96ff', name='Chair')
    P.box((2.0, .4, 2.6), (-3.2, 2.4, 2.6), '#4d96ff', pitch=55, name='Chair')
    return nocollide(smooth(P))


def lifebuoy(name='Lifebuoy'):
    P = Prop(name)
    P.box((.6, 6, .6), (0, 3, 0), WOOD)
    for k in range(8):
        a = k * 45
        r = math.radians(a)
        P.box((1.0, .6, .5), (math.cos(r) * 1.4, 4.6 + math.sin(r) * 1.4, -.55), '#ff5d5d' if k % 2 else '#ffffff', roll=a + 90)
    return smooth(P)


def surfboard(color='#4d96ff', name='Surfboard'):
    P = Prop(name)
    P.box((1.9, 6.6, .35), (0, 2.8, 0), '#ffffff', roll=8, pitch=-6)
    P.box((.45, 6.4, .4), (0, 2.8, 0), color, roll=8, pitch=-6)
    return smooth(P)


def starfish(seed=0, name='Starfish'):
    rng = random.Random(seed)
    P = Prop(name)
    c = rng.choice(('#ff8f4d', '#ff6fa8', '#ffd23c'))
    for k in range(5):
        a = k * 72
        r = math.radians(a)
        P.box((.45, .25, 1.2), (math.sin(r) * .55, .12, -math.cos(r) * .55), c, yaw=-a)
    return nocollide(smooth(P))


def shell(seed=0, name='Shell'):
    rng = random.Random(seed)
    P = Prop(name)
    P.wedge((.9, .5, .9), (0, .25, 0), rng.choice(('#ffffff', '#ffd6e5', '#ffe9c4')), yaw=rng.uniform(0, 360))
    return nocollide(smooth(P))


def boat(color='#ffffff', stripe='#ff5d5d', name='Boat'):
    P = Prop(name)
    P.span(-2.2, 2.2, -.2, .5, -5.5, 5.5, WOOD_DK, name='Hull')
    for s in (-1, 1):
        P.span(s * 2.2 - .35, s * 2.2 + .35, -.2, 2.2, -5.5, 5.5, color, name='Hull')
        P.span(s * 2.2 - .4, s * 2.2 + .4, 1.4, 1.9, -5.5, 5.5, stripe, name='Hull')
    P.span(-2.55, 2.55, -.2, 2.2, 5.5, 6.2, color, name='Hull')
    P.wedge((4.4, 2.4, 2.6), (0, 1.0, -6.8), color, yaw=180, name='Bow')
    P.span(-1.85, 1.85, .5, 1.2, -1, 1, WOOD, name='Seat')
    P.span(-1.85, 1.85, .5, 1.2, 3, 4.4, WOOD, name='Seat')
    for s in (-1, 1):
        P.box((.3, .3, 7), (s * 3.2, 1.7, .2), WOOD, yaw=s * 12, roll=s * 20, name='Oar')
    return smooth(P)


def buoy(name='Buoy'):
    P = Prop(name)
    P.cyl(2.2, 1.0, (0, -1.0, 0), '#ff5d5d')
    P.cyl(.5, 1.05, (0, -.2, 0), '#ffffff')
    P.box((.3, 2.6, .3), (0, 1.3, 0), '#f4f3fa')
    P.box((.7, .7, .7), (0, 2.9, 0), '#ffe066', mat='neon', collide=False, shadow=False)
    return P


def lamp():
    return smooth(kit.lamp('#fff1b0', '#5d5a78'))


def bench():
    return smooth(kit.bench())


def planter(seed=0):
    P = Prop('Planter')
    P.span(-3, 3, 0, 1.8, -1.5, 1.5, '#c9a589')
    P.span(-3.3, 3.3, 1.8, 2.2, -1.8, 1.8, '#e3c7ab')
    P.span(-2.6, 2.6, 2.2, 2.4, -1.1, 1.1, '#6b4a33')
    P.put(flowers(seed), cf(0, 2.4, 0))
    return smooth(P)


def bin_():
    P = Prop('Bin')
    P.span(-.9, .9, 0, 2.6, -.9, .9, '#5fb3ff').span(-1.05, 1.05, 2.6, 3.0, -1.05, 1.05, '#3f7fcf')
    return smooth(P)


# ------------------------------------------------------------------ plot pieces
def pad(accent):
    P = Prop('Pad')
    P.span(-8, 8, 1.4, 1.95, -8, 8, STONE, name='PadBase')
    P.span(-7.2, 7.2, 1.95, 2.45, -7.2, 7.2, '#d9c3a5', name='PadMid')
    P.span(-6.2, 6.2, 2.45, 2.65, -6.2, 6.2, '#f2e2c6', name='PadTop')
    P.span(-5.4, 5.4, 2.65, 2.78, 4.6, 5.4, accent, mat='neon', collide=False, name='PadRing')
    P.span(-5.4, 5.4, 2.65, 2.78, -5.4, -4.6, accent, mat='neon', collide=False, name='PadRing')
    P.span(4.6, 5.4, 2.65, 2.78, -4.6, 4.6, accent, mat='neon', collide=False, name='PadRing')
    P.span(-5.4, -4.6, 2.65, 2.78, -4.6, 4.6, accent, mat='neon', collide=False, name='PadRing')
    P.cyl(.15, 1.8, (0, 2.72, 0), shade(accent, .8), name='PadCentre')
    for x in (-7.4, 7.4):
        for z in (-7.4, 7.4):
            P.span(x - .5, x + .5, 1.95, 4.9, z - .5, z + .5, '#ffffff', name='PadPost')
            P.span(x - .65, x + .65, 4.9, 5.5, z - .65, z + .65, accent, mat='neon', collide=False, name='PadPostLight')
    return P


def round_button(glow, name):
    P = Prop(name)
    P.cyl(.7, 1.6, (0, 1.75, 0), METAL)
    P.cyl(.3, 1.1, (0, 2.25, 0), glow, mat='neon', name=name + 'Glow')
    return P


def conveyor(accent):
    """belt along X at the plot back: legs, frame, rails, belt with stripes, arrows, rollers, portal + exit tunnel"""
    P = Prop('Conveyor')
    x0, x1, w = -32, 32, 2.4
    for x in range(-30, 31, 8):
        for z in (-w - .3, w + .3):
            P.span(x - .45, x + .45, 1.4, 2.8, z - .45, z + .45, METAL, name='ConveyorLeg')
    for s in (-1, 1):
        P.span(x0, x1, 2.6, 3.4, min(s * w, s * (w + .8)), max(s * w, s * (w + .8)), METAL, name='ConveyorFrame')
        P.span(x0, x1, 3.4, 4.6, min(s * (w + .3), s * (w + .8)), max(s * (w + .3), s * (w + .8)), accent, name='ConveyorRail')
        for x in range(-28, 29, 8):
            P.span(x - .3, x + .3, 4.6, 5.0, min(s * (w + .25), s * (w + .85)), max(s * (w + .25), s * (w + .85)), '#ffffff',
                   name='ConveyorRail')
    P.span(x0, x1, 2.8, 3.3, -w, w, '#2f5fd0', name='ConveyorBelt')
    for k in range(16):
        x = x0 + 2 + k * 4
        P.span(x - .5, x + .5, 3.3, 3.38, -w + .2, w - .2, '#6fa8ff', name='BeltStripe')
    for x in (-20, -4, 12, 28):
        P.put(kit.chevron('#bfe9ff', .55), cf(x, 3.38, 0, yaw=-90))
    for x in (x0 - .7, x1 + .7):
        P.cyl(2 * w + .2, .9, (x, 3.0, 0), '#9a98b5', axis='z', name='Roller')
    px = x0 - 4                                               # spawn portal (left end)
    P.span(px - 2.6, px + 2.6, 1.4, 2.6, -5, 5, STONE, name='PortalBase')
    for z in (-4.2, 4.2):
        P.span(px - .9, px + .9, 2.6, 11, z - .9, z + .9, '#efe9ff', name='PortalFrame')
        P.span(px - 1.1, px + 1.1, 12.6, 13.4, z - 1.1, z + 1.1, accent, name='PortalFrame')
    P.span(px - 1.1, px + 1.1, 11, 12.6, -5.3, 5.3, '#efe9ff', name='PortalFrame')
    P.span(px - .3, px + .3, 2.6, 11, -3.3, 3.3, '#b05cff', mat='neon', tr=.25, collide=False, name='PortalSwirl')
    P.span(px - .45, px + .45, 4.4, 9.2, -2.2, 2.2, '#ffd2ff', mat='neon', tr=.2, collide=False, name='PortalSwirl')
    ex = x1 + 4                                               # exit tunnel (right end)
    P.span(ex - 3, ex + 3, 1.4, 9, -5, 5, '#6c6c84', name='ExitTunnel')
    P.span(ex - 3.15, ex - 3.0, 2.6, 7, -3.4, 3.4, '#1c1b29', name='ExitHole')
    for k in range(6):
        P.span(ex - 3.3, ex - 3.15, 7.4, 8.6, -5 + k * 10 / 6, -5 + (k + 1) * 10 / 6, '#ffd23c' if k % 2 else '#1c1b29',
               name='HazardStripe')
    P.span(ex - 3.4, ex + 3.4, 9, 9.8, -5.4, 5.4, accent, name='ExitTunnel')
    P.span(-2.5, 2.5, 1.4, 4.2, -w - 4.6, -w - 2.6, '#9a98b5', name='ControlBox')
    for i, c in enumerate(('#ff5d5d', '#5dff6a', '#ffd23c')):
        P.span(-1.8 + i * 1.3, -1.0 + i * 1.3, 3.2, 3.6, -w - 4.8, -w - 4.6, c, mat='neon', name='ControlButton')
    return P


def gate(accent):
    P = Prop('Gate')
    for s in (-1, 1):
        x = s * 8.5
        P.span(x - 1.5, x + 1.5, 1.4, 3.2, -1.5, 1.5, STONE, name='GatePillar')
        P.span(x - 1.1, x + 1.1, 3.2, 11.0, -1.1, 1.1, '#f6f2ff', name='GatePillar')
        for y in (5.0, 8.4):
            P.span(x - 1.25, x + 1.25, y, y + .7, -1.25, 1.25, accent, name='GateBand')
        P.span(x - 1.5, x + 1.5, 12.6, 13.4, -1.5, 1.5, accent, name='GateCap')
        P.box((1.2, 1.2, 1.2), (x, 14.2, 0), accent, yaw=45, mat='neon', collide=False, name='GateLight')
    P.span(-10, 10, 11.0, 12.6, -1.0, 1.0, '#f6f2ff', name='GateBeam')
    P.span(-6.5, 6.5, 8.4, 10.8, -1.1, -.8, accent, name='GateBanner')
    for y in (3.2, 5.6, 7.9):
        P.span(-7.4, 7.4, y - .15, y + .15, -.15, .15, '#ff2b4a', mat='neon', tr=.3, collide=False, shadow=False, name='LockLaser')
    return P


def billboard(accent):
    P = Prop('OwnerBoard')
    for x in (-5, 5):
        P.span(x - .5, x + .5, 1.4, 6.0, -.5, .5, WOOD_DK, name='BoardPost')
    P.span(-7, 7, 6, 13, -.4, .4, '#ffffff', name='Board')
    P.span(-6.3, 6.3, 6.6, 12.4, -.7, -.4, shade(accent, .85), mat='smooth', name='BoardFace')
    P.span(-7.4, 7.4, 13, 13.6, -.6, .6, accent, name='Board')
    return P


def plot_island(accent):
    """local frame: bridge lands at -Z (front), conveyor at the back (+Z)"""
    rng = random.Random(1234)                     # every plot identical; only the accent colour differs
    P = Prop('Plot')
    P.span(-HW - 6, HW + 6, -8, -3.5, -HD - 6, HD + 6, SHELF, mat='smooth', name='SandShelf')
    P.span(-HW - 3, HW + 3, -3.5, .2, -HD - 3, HD + 3, WET, name='WetSand')
    P.span(-HW, HW, .2, .8, -HD, HD, SAND, name='Sand')
    P.span(-GW, GW, .8, 1.4, -GD, GD, GRASS, name='Grass')
    # irregular edges: sand bumps over the wet sand, grass bumps over the dry sand (adjacent, never overlapping)
    for (top, bot, col, xs, zs, mouth) in ((.8, .2, SAND, HW, HD, 10), (1.4, .8, GRASS, GW, GD, 8)):
        for (ax, fixed, out) in (('x', -zs, -1), ('x', zs, 1), ('z', -xs, -1), ('z', xs, 1)):
            lo, hi = (-xs, xs) if ax == 'x' else (-zs, zs)
            s = lo + rng.uniform(2, 6)
            while s < hi - 6:
                w, d = rng.uniform(4, 9), rng.uniform(1, 2.6)
                if not (ax == 'x' and fixed < 0 and -mouth < s + w / 2 < mouth):
                    if ax == 'x':
                        P.span(s, s + w, bot, top, min(fixed, fixed + out * d), max(fixed, fixed + out * d), col, name='Edge')
                    else:
                        P.span(min(fixed, fixed + out * d), max(fixed, fixed + out * d), bot, top, s, s + w, col, name='Edge')
                s += w + rng.uniform(5, 13)
    for (ax, lo, hi, fixed) in (('x', -HW - 3, HW + 3, -HD - 3.4), ('x', -HW - 3, HW + 3, HD + 3.4),
                                ('z', -HD - 2, HD + 2, -HW - 3.4), ('z', -HD - 2, HD + 2, HW + 3.4)):
        s = lo
        while s < hi - 2:
            w = rng.uniform(3, 8)
            if ax == 'x':
                P.span(s, min(hi, s + w), -1.7, -1.25, fixed - .4, fixed + .4, FOAM, mat='smooth', tr=.15, collide=False, name='Foam')
            else:
                P.span(fixed - .4, fixed + .4, -1.7, -1.25, s, min(hi, s + w), FOAM, mat='smooth', tr=.15, collide=False, name='Foam')
            s += w + rng.uniform(1.5, 4)

    occ = []

    def keep(x0, x1, z0, z1):
        occ.append((min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)))

    def free(x, z, r):
        return all(not (a - r < x < b + r and c - r < z < d + r) for (a, b, c, d) in occ)

    # paved spine: base + running-bond tiles + kerbs
    z0s, z1s = -HD - 3, 39
    P.span(-4.6, 4.6, .6, 1.55, z0s, z1s, ROAD, name='PathBase')
    z, row = z0s + .2, 0
    while z < z1s - .4:
        L = min(2.6, z1s - .2 - z)
        x, k = -4.3, 0
        while x < 4.1:
            w = 1.5 if (k == 0 and row % 2) else 3.0
            w = min(w, 4.3 - x)
            P.span(x + .12, x + w - .12, 1.55, 1.72, z + .12, z + L - .12, TILE if (row + k) % 3 else TILE_LT, name='PathTile')
            x += w
            k += 1
        z += L
        row += 1
    for s in (-1, 1):
        P.span(min(s * 4.6, s * 5.4), max(s * 4.6, s * 5.4), .6, 1.9, -GD, z1s, KERB, name='Kerb')
    keep(-6, 6, -HD - 4, 42)
    # rows of pads with side paths and collect buttons
    for z in (-32, -12, 8, 28):
        for s in (-1, 1):
            P.span(min(s * 5.4, s * 15.4), max(s * 5.4, s * 15.4), .6, 1.6, z - 2.2, z + 2.2, ROAD, name='SidePath')
            for k in range(3):
                xa, xb = s * (5.7 + k * 3.2), s * (8.6 + k * 3.2)
                P.span(min(xa, xb), max(xa, xb), 1.6, 1.74, z - 1.9, z + 1.9, TILE if k % 2 else TILE_LT, name='PathTile')
            P.put(pad(accent), cf(s * 23.5, 0, z))
            P.put(round_button('#5dff6a', 'CollectButton'), cf(s * 13.0, 0, z + 4.4))
            keep(s * 15, s * 32, z - 8.6, z + 8.6)
            keep(s * 5, s * 16, z - 3, z + 6)
    P.put(conveyor(accent), cf(0, 0, 45))
    keep(-41, 41, 38, 51)
    P.put(gate(accent), cf(0, 0, -GD + 3))
    P.put(round_button('#ff2b4a', 'LockButton'), cf(9.5, 0, -GD + 8))
    P.put(billboard(accent), cf(-17, 0, -GD + 2))
    keep(-25, -9, -GD - 1, -GD + 5)
    keep(-12, 12, -GD + 1, -GD + 11)
    for z in (-44, -22, -2, 18):
        for s in (-1, 1):
            P.put(tiki(), cf(s * 6.8, 1.4, z))
    for (x, z, h) in ((-38, -48, 17), (37, -47, 15), (-39, -2, 18), (38, 6, 16), (-38, 30, 15), (38, 34, 17),
                      (-44, 57, 16), (44, 57.5, 18), (-46, -20, 14), (46, 20, 15)):
        y = 1.4 if abs(x) <= GW and abs(z) <= GD else .8
        P.put(palm(h, seed=rng.randrange(9999)), cf(x, y, z, yaw=rng.uniform(0, 360)))
        keep(x - 3, x + 3, z - 3, z + 3)
    for (x, z) in ((-34, -52), (33, -40), (-35, 20), (34, 47), (-35, 46), (35, -8)):
        P.put(smooth(kit.bush(seed=rng.randrange(999), s=.85)), cf(x, 1.4, z))
        keep(x - 3, x + 3, z - 3, z + 3)
    for (x, z) in ((-47, -58), (47, -55), (-46, 58.5), (47.5, -2), (-47.5, 40)):
        P.put(rock(rng.randrange(999), rng.uniform(.6, 1.0)), cf(x, .5, z, yaw=rng.uniform(0, 90)))
    P.put(umbrella(accent), cf(-45, 0, -32, yaw=90))
    P.put(umbrella('#4d96ff'), cf(45, 0, 30, yaw=-90))
    P.put(lifebuoy(), cf(-46, .8, 14, yaw=90))
    P.put(surfboard(accent), cf(46, .8, -14, yaw=-80))
    P.put(surfboard('#ffd23c'), cf(46.4, .8, -10, yaw=-100))
    for k in range(12):
        side = rng.choice('nswe')
        if side in 'ns':
            x, z = rng.uniform(-HW + 2, HW - 2), (HD - 2.5) * (1 if side == 's' else -1)
        else:
            x, z = (HW - 2.5) * (1 if side == 'e' else -1), rng.uniform(-HD + 4, HD - 4)
        if abs(x) < 8 and z < 0:
            continue
        P.put(starfish(k) if k % 2 else shell(k), cf(x, .8, z, yaw=rng.uniform(0, 360)))
    for (x, z, s) in ((-41.5, 41, 1.0), (-41.5, 37.6, .8), (41.5, 41, 1.0)):
        P.put(smooth(kit.crate(s)), cf(x, 1.4, z, yaw=rng.uniform(-15, 15)))
    P.put(kit.barrel(), cf(-38.5, 1.4, 52))
    P.put(kit.barrel(), cf(39, 1.4, 52.5))
    patches = []
    for _ in range(26):
        for _try in range(30):
            x, z = rng.uniform(-GW + 3, GW - 3), rng.uniform(-GD + 3, GD - 3)
            w, d = rng.uniform(4, 9), rng.uniform(3, 7)
            if not free(x, z, max(w, d) / 2 + .5):
                continue
            if any(abs(x - a) < (w + c) / 2 + .5 and abs(z - b) < (d + e) / 2 + .5 for (a, b, c, e) in patches):
                continue
            patches.append((x, z, w, d))
            P.span(x - w / 2, x + w / 2, 1.4, 1.5, z - d / 2, z + d / 2, rng.choice((GRASS_LT, GRASS_DK)), name='GrassPatch')
            break
    for k in range(18):
        for _try in range(30):
            x, z = rng.uniform(-GW + 2, GW - 2), rng.uniform(-GD + 2, GD - 2)
            if free(x, z, 3):
                P.put(flowers(rng.randrange(9999)) if k % 2 == 0 else tuft(rng.randrange(9999)), cf(x, 1.5, z))
                keep(x - 2.5, x + 2.5, z - 2.5, z + 2.5)
                break
    return P


# ------------------------------------------------------------------ hub pieces
def lighthouse(name='Lighthouse'):
    P = Prop(name)
    P.poly(ngon(13, 8, 22.5), 2.6, 3.4, STONE, name='LighthouseBase')
    P.poly(ngon(10.5, 8, 22.5), 3.4, .8, '#b3b0cc', name='LighthouseBase')
    y = 3.4
    for k in range(6):
        P.cyl(7.0, 7.2 - k * .42, (0, y + 3.5, 0), '#e8453c' if k % 2 == 0 else '#ffffff', name='LighthouseTower')
        y += 7.0
    P.span(-1.6, 1.6, 3.4, 8.4, -7.6, -6.2, '#3a2a22', name='LighthouseDoor')
    P.span(-2.2, 2.2, 8.4, 9.2, -7.9, -6.0, '#ffffff', name='LighthouseDoor')
    for (yy, a) in ((15, 0), (24, 120), (33, 240)):
        r = math.radians(a)
        P.box((1.6, 2.4, 1.0), (math.sin(r) * -6.4, yy, -math.cos(r) * 6.4), '#2b3a55', yaw=-a, name='LighthouseWindow')
    P.poly(ngon(7.8, 8, 22.5), y + 1.0, 1.0, '#5d5a78', name='Gallery')
    for k in range(16):
        a = math.radians(k * 22.5)
        P.box((.3, 2.0, .3), (math.cos(a) * 7.4, y + 2.0, math.sin(a) * 7.4), '#ffffff', name='GalleryRail')
    for k in range(8):
        a = k * 45 + 22.5
        r = math.radians(a)
        P.box((5.6, .3, .3), (math.cos(r) * 6.85, y + 2.9, math.sin(r) * 6.85), '#ffffff', yaw=-a + 90, name='GalleryRail')
    P.cyl(.6, 4.4, (0, y + 1.3, 0), '#5d5a78', name='LanternRoom')
    P.cyl(5.6, 3.8, (0, y + 4.4, 0), '#bfe9ff', mat='glass', tr=.55, name='LanternGlass')
    for k in range(6):
        a = math.radians(k * 60)
        P.box((.4, 5.6, .4), (math.cos(a) * 3.85, y + 4.4, math.sin(a) * 3.85), '#5d5a78', name='LanternFrame')
    P.ball(3.0, (0, y + 4.4, 0), '#fff4a8', mat='neon', collide=False, shadow=False, name='LighthouseLight')
    for (h, r, yy) in ((1.0, 4.6, 7.7), (1.2, 3.4, 8.8), (1.2, 2.2, 10.0)):
        P.cyl(h, r, (0, y + yy, 0), '#e8453c', name='LighthouseRoof')
    P.ball(1.6, (0, y + 11.2, 0), GOLD, name='LighthouseTop')
    return P


def coin_fountain(name='CoinFountain'):
    P = Prop(name)
    P.poly(ngon(13, 8, 22.5), 2.2, 1.6, STONE, name='FountainBase')
    for i in range(8):
        a = i * 45
        r = math.radians(a)
        P.box((9.4, 2.4, 1.6), (math.cos(r) * 11.6, 3.4, math.sin(r) * 11.6), '#c9c6e0', yaw=-a + 90, name='FountainWall')
        P.box((10.0, .6, 2.2), (math.cos(r) * 11.6, 4.9, math.sin(r) * 11.6), '#efeaff', yaw=-a + 90, name='FountainRim')
    P.cyl(.4, 10.9, (0, 3.6, 0), '#46c4ee', tr=.25, collide=False, name='FountainWater')
    P.poly(ngon(5.0, 8, 22.5), 6.6, 3.0, '#8d89cf', name='Pedestal')
    P.poly(ngon(3.6, 8, 22.5), 8.4, 1.8, '#b3b0cc', name='Pedestal')
    P.box((1.4, 3.6, 1.4), (0, 10.2, 0), '#b3b0cc', name='CoinStand')
    P.cyl(1.6, 6.5, (0, 18.0, 0), GOLD, axis='z', name='GiantCoin')
    P.cyl(1.9, 4.8, (0, 18.0, 0), '#ffd866', axis='z', name='GiantCoin')
    P.box((1.6, 4.4, 2.0), (0, 18.0, 0), '#e0a92a', name='GiantCoin')
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        P.box((.7, 3.0, .7), (math.cos(a) * 8.0, 5.0, math.sin(a) * 8.0), '#9ff0ff', mat='neon', collide=False, shadow=False,
              name='WaterJet')
    return P


def hut(roof, accent, icon, name):
    P = Prop(name)
    w, d, h = 18.0, 14.0, 9.0
    P.span(-w / 2 - 1, w / 2 + 1, 1.4, 2.4, -d / 2 - 3, d / 2 + 1, '#e3c7ab', name='Deck')
    for s in (-1, 1):
        P.span(s * (w / 2 - .6) - .6, s * (w / 2 - .6) + .6, 2.4, h, -d / 2, d / 2, '#fbf4e6', name='Wall')
    P.span(-w / 2, w / 2, 2.4, h, d / 2 - 1.2, d / 2, '#fbf4e6', name='Wall')
    for x in (-w / 2, w / 2):
        P.span(x - .7, x + .7, 2.4, h + .4, -d / 2 - .7, -d / 2 + .7, accent, name='Trim')
    P.span(-w / 2 + 1, w / 2 - 1, 2.4, 5.8, -d / 2, -d / 2 + 2, accent, name='Counter')
    P.span(-w / 2 + .6, w / 2 - .6, 5.8, 6.4, -d / 2 - .4, -d / 2 + 2.4, '#ffffff', name='Counter')
    P.span(-w / 2 - .4, w / 2 + .4, h, h + .6, -d / 2 - .4, d / 2 + .4, '#ffffff', name='Trim')
    P.put(kit.gable_roof(w + .8, d + .8, 6.0, roof, shade(roof, .75), slat=2.4), cf(0, h + .6, 0))
    kit.awning(P, w + 1.4, 4.4, h - .4, z=-d / 2 - .3, colors=(roof, '#ffffff'), stripes=7, pitch=22)
    P.span(-5, 5, h + 1.8, h + 5.0, -d / 2 - 1.8, -d / 2 - 1.2, '#ffffff', name='Sign')
    P.span(-4.3, 4.3, h + 2.2, h + 4.6, -d / 2 - 2.0, -d / 2 - 1.8, accent, mat='smooth', name='Sign')
    P.put(icon, cf(0, h + 12, 0))
    return smooth(P)


def icon_basket():
    P = Prop('IconShop')
    P.span(-3, 3, 0, 2.6, -2, 2, '#ff5d6c').span(-3.4, 3.4, 2.6, 3.2, -2.4, 2.4, '#ff8f9b')
    for k in range(3):
        P.span(-2.2 + k * 1.8, -1.6 + k * 1.8, .6, 2.2, -2.15, -2.0, '#c9344a')
    P.box((.5, 3.2, .5), (-2.4, 4.6, 0), '#8a8aa0', roll=-25).box((.5, 3.2, .5), (2.4, 4.6, 0), '#8a8aa0', roll=25)
    P.box((3.2, .5, .5), (0, 6.0, 0), '#8a8aa0')
    return P


def icon_book():
    P = Prop('IconIndex')
    for s in (-1, 1):
        P.box((3.6, .7, 5.0), (s * 1.75, 2.4, 0), '#4d96ff', roll=-s * 14)
        P.box((3.2, .5, 4.4), (s * 1.6, 2.95, 0), '#ffffff', roll=-s * 14)
    P.box((.7, .9, 5.0), (0, 2.1, 0), '#2f6fd0')
    return P


def icon_rebirth():
    P = Prop('IconRebirth')
    for k in range(9):
        a = k * 36
        r = math.radians(a)
        P.box((1.9, .9, .9), (math.cos(r) * 2.8, 3 + math.sin(r) * 2.8, 0), '#b05cff', roll=a + 90, mat='neon')
    P.box((1.6, 1.6, .9), (2.8, 1.4, 0), '#b05cff', roll=45, mat='neon')
    return P


def leaderboard(accent, name='Leaderboard'):
    P = Prop(name)
    for x in (-7, 7):
        P.span(x - .8, x + .8, 1.4, 16, -.8, .8, '#5d5a78', name='BoardPost')
    P.span(-8.5, 8.5, 5, 17, -.5, .5, accent, mat='neon', name='BoardFrame')
    P.span(-7.8, 7.8, 5.6, 16.4, -.8, -.5, '#24233a', mat='smooth', name='BoardScreen')
    P.span(-2.4, 2.4, 17, 17.6, -.6, .6, GOLD, name='Crown')
    for i, x in enumerate((-1.8, 0, 1.8)):
        P.box((1.0, 1.8 if i == 1 else 1.2, 1.0), (x, 18.4 if i == 1 else 18.2, 0), GOLD, name='Crown')
    return P


def islet(seed, r):
    rng = random.Random(seed)
    P = Prop('Islet')
    P.poly(ngon(r + 6, 8, 22.5), -3.5, 4.5, SHELF, name='SandShelf', mat='smooth')
    P.poly(ngon(r + 2.5, 8, 22.5), .2, 3.7, WET, name='WetSand')
    P.poly(ngon(r, 8, 22.5), .8, .6, SAND, name='Sand')
    P.poly(ngon(r * .62, 8, 22.5 + rng.uniform(-8, 8)), 1.4, .6, GRASS, name='Grass')
    for _ in range(rng.choice((1, 2, 3))):
        a = rng.uniform(0, 6.28)
        P.put(palm(rng.uniform(13, 18), seed=rng.randrange(999)), cf(math.cos(a) * r * .3, 1.4, math.sin(a) * r * .3,
                                                                       yaw=rng.uniform(0, 360)))
    P.put(rock(rng.randrange(99)), cf(r * .7, .6, -r * .3))
    return P


# ------------------------------------------------------------------ build
def build():
    rng = random.Random(9)
    root = Group(NAME, 'Model')
    sea, island, plots, hub, deco = (root.folder(n) for n in ('Sea', 'MainIsland', 'Plots', 'Hub', 'Decoration'))

    S = Prop('Sea')
    S.span(-1020, 1020, -10, -8, -1020, 1020, DEEP, mat='smooth', name='SeaFloor')
    S.span(-1020, 1020, -1.7, -1.5, -1020, 1020, WATER, mat='smooth', tr=.32, collide=False, name='Water')
    sea.place(S, cf(), cls=None)

    # ---- main road island + spawn hub island (adjacent pieces, never overlapping)
    M = Prop('MainIsland')
    xh0, xh1, zh = -306, -200, 46
    xr1, zr = 230, 24
    M.span(xh0 - 3, xh1, -3.5, .2, -zh - 3, zh + 3, WET, name='WetSand')
    M.span(xh1, xr1 + 3, -3.5, .2, -zr - 3, zr + 3, WET, name='WetSand')
    M.span(xh0, xh1, .2, .8, -zh, zh, SAND, name='Sand')
    M.span(xh1, xr1, .2, .8, -zr, zr, SAND, name='Sand')
    M.span(xh0 + 6, xh1, .8, 1.4, -zh + 6, zh - 6, GRASS, name='Grass')
    M.span(xh1, xr1 - 6, .8, 1.4, -zr + 5, zr - 5, GRASS, name='Grass')
    M.span(xh0 - 9, xh1, -8, -3.5, -zh - 9, zh + 9, SHELF, mat='smooth', name='SandShelf')
    M.span(xh1, xr1 + 9, -8, -3.5, -zr - 4, zr + 4, SHELF, mat='smooth', name='SandShelf')
    for (x0, x1, z) in ((xh0 - 3, xh1, -zh - 3.4), (xh0 - 3, xh1, zh + 3.4), (xh1 + 12, xr1 + 3, -zr - 3.4), (xh1 + 12, xr1 + 3, zr + 3.4)):
        s = x0
        while s < x1 - 2:
            w = rng.uniform(3, 8)
            M.span(s, min(x1, s + w), -1.7, -1.25, z - .4, z + .4, FOAM, mat='smooth', tr=.15, collide=False, name='Foam')
            s += w + rng.uniform(1.5, 4)
    hx = -252
    for (r, top, t, c) in ((34, 1.6, 1.0, '#e3c7ab'), (30, 1.8, .4, '#f0dcc3'), (20, 2.0, .3, '#d6b79a'), (16, 2.2, .3, '#f6e8d4')):
        M.poly(ngon(r, 8, 22.5, hx, 0), top, t, c, name='Plaza')
    rx0, rx1, rw = -218, 226, 7.0
    M.span(rx0, rx1, .6, 1.55, -rw, rw, ROAD, name='RoadBase')
    x, col = rx0 + .2, 0
    while x < rx1 - .4:
        z, k = -rw + .3, 0
        while z < rw - .3:
            w = min(3.4 if (col + k) % 2 else 2.6, rw - .3 - z)
            M.span(x + .14, x + 2.86, 1.55, 1.72, z + .14, z + w - .14, TILE if (col + k) % 3 else TILE_LT, name='RoadTile')
            z += w
            k += 1
        x += 3.0
        col += 1
    for s in (-1, 1):
        M.span(rx0, rx1, .6, 1.9, min(s * rw, s * (rw + .9)), max(s * rw, s * (rw + .9)), KERB, name='Kerb')
        M.span(rx0 + 18, rx1, .8, 1.6, min(s * (rw + .9), s * (rw + 4.5)), max(s * (rw + .9), s * (rw + 4.5)), '#ead9c2',
               name='Sidewalk')
    island.place(M, cf(), cls=None)

    # ---- bridges: plank deck, rails, rope, posts down to the sea floor, lanterns
    for x in XS:
        for s in (-1, 1):
            B = Prop('Bridge')
            z0, z1 = zr - 1, ROW_Z - HD + 2
            n = int((z1 - z0) / .9)
            for k in range(n):
                zz = z0 + k * .9
                B.span(-5.2, 5.2, 1.05, 1.45, zz + .06, zz + .84, WOOD if k % 2 else shade(WOOD, .9), name='BridgePlank')
            B.span(-5.4, 5.4, .5, 1.05, z0, z1, WOOD_DK, name='BridgeBeam')
            for zz in (z0 + 1.2, (z0 + z1) / 2, z1 - 1.2):
                for xs in (-5.4, 5.4):
                    B.span(xs - .5, xs + .5, -8, 4.4, zz - .5, zz + .5, WOOD_DK, name='BridgePost')
                    B.span(xs - .6, xs + .6, 4.4, 4.8, zz - .6, zz + .6, WOOD, name='BridgePost')
            for xs in (-5.4, 5.4):
                B.span(xs - .3, xs + .3, 3.8, 4.2, z0 + 1.7, z1 - 1.7, WOOD, name='BridgeRail')
                B.span(xs - .15, xs + .15, 2.5, 2.8, z0 + 1.7, z1 - 1.7, '#e8d8b0', name='BridgeRope')
                B.box((.9, 1.2, .9), (xs, 5.6, z1 - 1.2), '#ffe08a', mat='neon', collide=False, name='BridgeLantern')
                B.box((1.3, .3, 1.3), (xs, 6.35, z1 - 1.2), '#5d5a78', name='BridgeLantern')
            island.place(B, cf(x, 0, 0, yaw=0 if s > 0 else 180), name='Bridge')

    # ---- plots
    k = 0
    for s in (-1, 1):
        for x in XS:
            z = s * ROW_Z
            plots.place(plot_island(ACCENTS[k]), cf(x, 0, z, yaw=yaw_to(x, z, x, 0)), name='Plot%d' % (k + 1))
            k += 1

    # ---- hub
    sp = Prop('SpawnLocation')
    sp.box((12, 1, 12), (0, .5, 0), '#ffffff', shape='spawn', mat='smooth', name='SpawnLocation')
    hub.place(sp, cf(hx - 22, 2.2, 0), cls=None)
    hub.place(coin_fountain(), cf(hx + 4, 0, 0, yaw=90), name='CoinFountain')
    hub.place(lighthouse(), cf(-287, 0, -27), name='Lighthouse')
    hub.place(hut('#ff5d6c', '#ffd23c', icon_basket(), 'ShopHut'), cf(hx - 2, 0, -31, yaw=180), name='Shop')
    hub.place(hut('#4d96ff', '#bfe9ff', icon_book(), 'IndexHut'), cf(hx - 2, 0, 31), name='Index')
    hub.place(hut('#9d79f2', '#ffd2ff', icon_rebirth(), 'RebirthHut'), cf(-289, 0, 17, yaw=-90), name='Rebirth')
    for z in (-30, 30):
        hub.place(leaderboard('#ffd23c' if z < 0 else '#4d96ff'), cf(-224, 1.4, z, yaw=yaw_to(-224, z, hx, 0)), name='Leaderboard')
    hub.place(kit.arch(16, 18, glow='#ffd23c'), cf(-212, 1.4, 0, yaw=90), name='WelcomeArch')
    for a in range(8):
        r = math.radians(a * 45 + 22.5)
        hub.place(lamp(), cf(hx + math.cos(r) * 31.5, 1.6, math.sin(r) * 31.5), name='Lamp')
    PI = Prop('Pier')
    for k2 in range(28):
        zz = zh + k2 * 1.0
        PI.span(-4, 4, 1.0, 1.4, zz + .06, zz + .94, WOOD if k2 % 2 else shade(WOOD, .9), name='PierPlank')
    for zz in (zh + 4, zh + 14, zh + 26):
        for xs in (-4, 4):
            PI.span(xs - .5, xs + .5, -8, 3.2, zz - .5, zz + .5, WOOD_DK, name='PierPost')
    island.place(PI, cf(-262, 0, 0), name='Pier')
    deco.place(boat(), cf(-252, -1.5, zh + 20, yaw=8), name='Boat')
    for xx in range(-190, 225, 34):
        for s in (-1, 1):
            if any(abs(xx - px) < 12 or abs(xx + 8 - px) < 12 for px in XS):
                continue
            deco.place(lamp(), cf(xx, 1.6, s * 10), name='Lamp')
            if (xx // 34) % 2 == 0:
                deco.place(bench(), cf(xx + 8, 1.6, s * 10.2, yaw=0 if s < 0 else 180), name='Bench')
            else:
                deco.place(planter(rng.randrange(999)), cf(xx + 8, 1.6, s * 10.2), name='Planter')
                deco.place(bin_(), cf(xx - 5, 1.6, s * 10.4), name='Bin')
    for xx in range(-180, 226, 26):
        for s in (-1, 1):
            if any(abs(xx - px) < 14 for px in XS):
                continue
            deco.place(palm(rng.uniform(13, 17), seed=rng.randrange(9999)), cf(xx + rng.uniform(-4, 4), 1.4, s * 16.5,
                                                                                yaw=rng.uniform(0, 360)), name='Palm')
    for (x, z, h) in ((-298, 38, 17), (-212, 38, 16), (-212, -38, 18), (-299, -2, 15), (-240, 42, 14), (-266, -42, 16)):
        deco.place(palm(h, seed=rng.randrange(9999)), cf(x, 1.4 if abs(z) < 40 else .8, z, yaw=rng.uniform(0, 360)), name='Palm')
    for _ in range(14):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(36.5, 39)
        x, z = hx + math.cos(a) * r, math.sin(a) * r
        if abs(z) < 34 and x > hx + 20:
            continue
        deco.place(flowers(rng.randrange(999)), cf(x, 1.4, z), name='Flowers')

    # ---- sea: islets, boats, buoys
    for k2, (x, z, r) in enumerate(((-420, -170, 14), (-400, 175, 11), (330, -180, 16), (340, 150, 12), (-20, -250, 10),
                                    (60, 255, 13), (-150, 260, 9), (170, -262, 11))):
        deco.place(islet(k2 * 7 + 1, r), cf(x, 0, z), name='Islet')
    for (x, z, yw, c) in ((262, 8, 80, '#ffd23c'), (-110, 212, 200, '#4d96ff'), (115, -214, 30, '#ff5d6c')):
        deco.place(boat(stripe=c), cf(x, -1.5, z, yaw=yw), name='Boat')
    for x in range(-300, 301, 75):
        for z in (-190, 190):
            deco.place(buoy(), cf(x + rng.uniform(-8, 8), -1.5, z + rng.uniform(-6, 6)), name='Buoy')

    views = [
        dict(name='overview', pos=[-150, 230, 300], target=[-20, 0, -10], fov=55),
        dict(name='plot_closeup', pos=[-118, 46, -32], target=[-165, 4, -98], fov=60),
        dict(name='plot_pads', pos=[-150, 15, -112], target=[-178, 3, -146], fov=70),
        dict(name='conveyor', pos=[-152, 18, -122], target=[-168, 4, -142], fov=65),
        dict(name='spawn', pos=[-276, 9, 6], target=[-200, 8, 0], fov=70),
        dict(name='hub', pos=[-196, 50, 70], target=[-262, 8, -6], fov=60),
        dict(name='road', pos=[-150, 10, 2], target=[60, 4, 0], fov=65),
        dict(name='plan', pos=[0, 950, 0.01], target=[0, 0, 0], fov=42),
    ]
    return root, views, dict(center=[-30, 0, 0], radius=360)
