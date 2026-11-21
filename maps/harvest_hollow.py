"""Harvest Hollow: round canyon farm hub (stud style).

Six identical fenced farm plots face a hex market plaza in the middle of a grass bowl ringed by terracotta canyon
walls with grass caps, terraces and pines. Roblox space: X east, Y up, Z south, studs. Front of every prop = -Z.
"""
import math
import random

from studmap.core import Group, Prop, cf, ngon, shade, yaw_to
from studmap import kit

NAME = 'HarvestHollow'

GRASS = '#6cd34c'
CAP = '#7ddf55'
CLIFF = '#c8655c'
CLIFF_DK = '#a9524f'
PLAZA_RIM = '#8d89cf'
PLAZA = '#f3a86f'
PLAZA_DK = '#e48f5a'
FIELD_BASE = '#3c9f3a'
FIELD = '#5ad84e'
SOIL = '#d0744a'
SOIL_DK = '#b7603c'
PATH = '#ecc98f'
STONE = '#9d9ab8'
GOLD = '#f5c53a'

R_WALL = 205            # inner radius of the canyon wall foot
PLOT_R = 122            # plot centre distance from the plaza centre
PLOT_W, PLOT_D = 80, 68
PLOT_ANGLES = [30 + 60 * k for k in range(6)]
ACCENTS = ['#ff8fb0', '#58a6ff', '#ffd23c', '#b48cff', '#ff9f43', '#4fd1c5']


def polar(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


# ------------------------------------------------------------------ props
def plot_prop(accent):
    P = Prop('Plot')
    hw, hd = PLOT_W / 2, PLOT_D / 2
    # sand path from the gate to the barn
    P.span(-3.5, 3.5, -0.3, 0.2, -hd, 4, PATH, name='Path')
    # crop field: dark bed + bright tiles + sprouts
    x0, x1, z0, z1 = -hw + 6, -6, -hd + 6, -6
    P.span(x0, x1, -0.3, 0.4, z0, z1, FIELD_BASE, name='Field')
    cols, rows = 4, 3
    px, pz = (x1 - x0) / cols, (z1 - z0) / rows
    for i in range(cols):
        for j in range(rows):
            cx, cz = x0 + px * (i + .5), z0 + pz * (j + .5)
            P.span(cx - px / 2 + .7, cx + px / 2 - .7, 0.4, 0.9, cz - pz / 2 + .7, cz + pz / 2 - .7, FIELD, name='FieldTile')
            P.box((.6, 2.0, .6), (cx, 1.9, cz), '#3fa83c', name='Crop')
            P.box((1.8, .5, .8), (cx - .5, 2.8, cz), '#7be05e', roll=25, name='Crop')
            P.box((1.8, .5, .8), (cx + .5, 2.6, cz), '#7be05e', roll=-25, name='Crop')
    # tilled soil checker
    sx0, sz0, t = 2, 4, 6
    for i in range(5):
        for j in range(4):
            P.span(sx0 + i * t, sx0 + (i + 1) * t, -0.3, 0.5, sz0 + j * t, sz0 + (j + 1) * t,
                   SOIL if (i + j) % 2 == 0 else SOIL_DK, name='Soil')
    # barn back-left, doors toward the gate
    P.put(kit.barn(), cf(-20, 0, 16))
    # market stall front-right
    P.put(kit.stall(accent), cf(22, 0, -18))
    P.put(kit.crate(), cf(30.5, 0, -12, yaw=12))
    P.put(kit.crate(.8), cf(30, 2.6, -12, yaw=40))
    P.put(kit.barrel(), cf(13.5, 0, -14))
    # water tank right side
    P.put(kit.water_tank(), cf(33, 0, -1))
    # hay + barrels by the barn
    P.put(kit.hay(), cf(-7, 0, 26, yaw=90))
    P.put(kit.barrel(), cf(-7.5, 0, 21))
    # fence with a gate gap at the front
    gap = 6 / PLOT_W
    kit.fence_loop(P, [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)], gaps=[(0, .5 - gap, .5 + gap)])
    for x in (-6.4, 6.4):
        P.box((1.4, 7.0, 1.4), (x, 3.0, -hd), kit.WHITE, name='GatePost')
        P.box((2.0, .8, 2.0), (x, 6.8, -hd), accent, name='GatePost')
    P.box((14.2, 1.0, 1.0), (0, 6.2, -hd), kit.WHITE, name='GateBeam')
    # owner sign + claim pad outside the gate
    P.put(kit.sign(accent), cf(-12, 0, -hd - 4))
    P.span(-4.5, 4.5, -0.3, 0.6, -hd - 13, -hd - 4, PLAZA_RIM, name='ClaimPad')
    P.span(-3.5, 3.5, 0.6, 0.75, -hd - 12, -hd - 5, accent, mat='neon', name='ClaimPadGlow')
    return P


def shop_prop(accent, roof='#c95f37', name='Shop'):
    P = Prop(name)
    w, d, h = 16.0, 12.0, 8.0
    P.span(-w / 2 - 1, w / 2 + 1, 0, 1.0, -d / 2 - 2.5, d / 2 + 1, kit.WOOD_DK, name='Deck')
    kit.plank_wall(P, -w / 2, w / 2, 1.0, h, d / 2 - .5, kit.WOOD)
    kit.plank_wall(P, -d / 2, d / 2, 1.0, h, -w / 2 + .5, kit.WOOD, axis='z')
    kit.plank_wall(P, -d / 2, d / 2, 1.0, h, w / 2 - .5, kit.WOOD, axis='z')
    P.span(-w / 2 + 1, w / 2 - 1, 1.0, 4.4, -d / 2, -d / 2 + 1.6, kit.WOOD, name='Counter')
    P.span(-w / 2 + .6, w / 2 - .6, 4.4, 4.9, -d / 2 - .3, -d / 2 + 1.9, kit.WOOD_DK, name='Counter')
    for x in (-w / 2 + .5, w / 2 - .5):
        P.span(x - .5, x + .5, 1.0, h, -d / 2 - .1, -d / 2 + .9, kit.WOOD_DK, name='Post')
    for i, c in enumerate(('#e2483f', '#f39a2b', '#f4d03f', '#7bc043')):
        x = -4.5 + i * 3
        P.span(x - 1.2, x + 1.2, 4.9, 5.7, -d / 2 + .2, -d / 2 + 1.6, '#c98a4b', name='Crate')
        P.box((1.6, .8, 1.0), (x, 6.0, -d / 2 + .9), c, name='Goods')
    P.span(-w / 2 - .3, w / 2 + .3, h, h + .5, -d / 2 - .3, d / 2 + .3, shade(kit.WOOD, .8), name='Trim')
    P.put(kit.gable_roof(w + .6, d + .6, 5.5, roof, kit.WOOD_DK), cf(0, h + .5, 0))
    kit.awning(P, w + 1.2, 4.0, h - .4, z=-d / 2 - .2, colors=(accent, kit.WHITE), stripes=7, pitch=24)
    P.span(-4.5, 4.5, h + 1.6, h + 4.6, -d / 2 - 1.6, -d / 2 - 1.0, kit.WHITE, name='Sign')
    P.span(-3.8, 3.8, h + 2.0, h + 4.2, -d / 2 - 1.8, -d / 2 - 1.5, accent, mat='smooth', name='Sign')
    return P


def sprout_statue():
    """plaza centrepiece: octagon fountain with a golden sprout on a stepped pedestal"""
    P = Prop('SproutFountain')
    P.poly(ngon(13, 8, 22.5), 0.8, 1.2, STONE, name='FountainBase')
    for i in range(8):
        a = i * 45
        x, z = polar(11.6, a)
        P.box((9.6, 2.6, 1.6), (x, 1.9, z), '#b3b0cc', yaw=-a + 90, name='FountainWall')
        P.box((10.2, .6, 2.2), (x, 3.5, z), '#d6d4ea', yaw=-a + 90, name='FountainRim')
    P.cyl(.4, 10.8, (0, 2.4, 0), '#46c4ee', tr=.2, collide=False, name='Water')
    P.poly(ngon(5.2, 8, 22.5), 4.2, 3.6, '#8d89cf', name='Pedestal')
    P.poly(ngon(3.8, 8, 22.5), 6.2, 2.0, '#b3b0cc', name='Pedestal')
    P.span(-2.6, 2.6, 6.2, 9.6, -2.6, 2.6, GOLD, name='Pot')
    P.span(-3.0, 3.0, 9.6, 10.4, -3.0, 3.0, '#ffd866', name='Pot')
    P.span(-2.2, 2.2, 10.4, 10.8, -2.2, 2.2, '#7a4a2a', name='PotSoil')
    P.box((1.2, 9.0, 1.2), (0, 15.0, 0), '#4fbf45', name='Stem')
    P.box((5.4, 1.0, 3.0), (-2.6, 15.0, 0), '#6fe05a', roll=28, name='Leaf')
    P.box((5.4, 1.0, 3.0), (2.6, 17.6, 0), '#6fe05a', roll=-28, name='Leaf')
    P.box((2.6, 2.6, 2.6), (0, 20.2, 0), GOLD, yaw=45, pitch=35, name='Bud')
    for i in range(4):
        x, z = polar(8.4, i * 90 + 45)
        P.box((.8, 3.2, .8), (x, 4.2, z), '#9ff0ff', mat='neon', collide=False, shadow=False, name='Jet')
    return P


# ------------------------------------------------------------------ build
def build():
    rng = random.Random(11)
    root = Group(NAME, 'Model')
    ground = root.folder('Ground')
    canyon = root.folder('Canyon')
    plaza = root.folder('Plaza')
    plots = root.folder('Plots')
    nature = root.folder('Nature')

    G = Prop('Ground')
    G.span(-420, 420, -4, 0, -420, 420, GRASS, name='Grass')
    ground.place(G, cf(), cls=None)

    # ---- canyon wall ring: radial blocks, neighbours never share a height (no z-fighting caps)
    N = 60
    hs = []
    for i in range(N):
        choices = [34, 38, 42, 46, 50]
        if hs:
            choices = [c for c in choices if c != hs[-1]]
        if i == N - 1:
            choices = [c for c in choices if c != hs[0]]
        hs.append(rng.choice(choices))
    W = Prop('CanyonWall')
    for i in range(N):
        a = i * 360 / N
        r_in = R_WALL + rng.uniform(-3, 5)
        D = 64
        h = hs[i]
        w = 2 * math.pi * (r_in + D) / N + 3
        blk = Prop('Cliff')
        blk.span(-w / 2, w / 2, -2, h, -D / 2, D / 2, CLIFF if i % 2 else shade(CLIFF, .95), name='Cliff')
        blk.span(-w / 2, w / 2, h, h + 2.6, -D / 2 - 1.6, D / 2, CAP, name='GrassCap')
        blk.span(-w / 2 + 1, w / 2 - 1, -1, 7 + (i % 3) * 2, -D / 2 - 1.4, -D / 2 + 2, CLIFF_DK, name='CliffBase')
        if rng.random() < .45:                                     # buttress step with its own grass cap
            bw = w * rng.uniform(.35, .55)
            bh = h * rng.uniform(.45, .7)
            bx = rng.uniform(-w / 4, w / 4)
            blk.span(bx - bw / 2, bx + bw / 2, -1, bh, -D / 2 - 5, -D / 2 + 2, shade(CLIFF, 1.04), name='Cliff')
            blk.span(bx - bw / 2 - .4, bx + bw / 2 + .4, bh, bh + 2.0, -D / 2 - 5.8, -D / 2 + 2, CAP, name='GrassCap')
        x, z = polar(r_in + D / 2, a)
        W.put(blk, cf(x, 0, z, yaw=yaw_to(x, z, 0, 0)))
    # land behind the rim: a ring of backfill blocks (alternate heights, no coplanar tops) + square plateau corners
    N2 = 48
    for i in range(N2):
        a = (i + .5) * 360 / N2
        h = 31.4 if i % 2 else 31.8
        w = 2 * math.pi * 352 / N2 + 2
        x, z = polar(307, a)
        bf = Prop('Backfill')
        bf.span(-w / 2, w / 2, -2, h, -45, 45, CLIFF_DK, name='Cliff')
        bf.span(-w / 2, w / 2, h, h + 2, -45, 45, CAP, name='GrassCap')
        W.put(bf, cf(x, 0, z, yaw=yaw_to(x, z, 0, 0)))
    for x0, x1, z0, z1 in ((-420, 420, -420, -240), (-420, 420, 240, 420), (-420, -240, -240, 240), (240, 420, -240, 240)):
        W.span(x0, x1, 0, 31, z0, z1, CLIFF_DK, name='Plateau')
        W.span(x0, x1, 31, 33, z0, z1, CAP, name='PlateauGrass')
    canyon.place(W, cf(), cls=None)

    # ---- terraces against the wall, with pines and rocks on top
    taken = []                                                      # (x, z, r) for scatter
    for k, a in enumerate((8, 52, 104, 158, 200, 248, 292, 338)):
        tw = rng.uniform(34, 48)
        th = rng.choice((10, 14, 18))
        T = Prop('Terrace')
        T.span(-tw / 2, tw / 2, -1, th, -14, 14, shade(CLIFF, 1.02), name='Cliff')
        T.span(-tw / 2 - .5, tw / 2 + .5, th, th + 2.2, -14.8, 14, CAP, name='GrassCap')
        T.span(-tw / 3, tw / 3, -1, 6, -21, -13, CLIFF_DK, name='Cliff')
        T.span(-tw / 3 - .4, tw / 3 + .4, 6, 7.8, -21.6, -13, CAP, name='GrassCap')
        for j in range(rng.choice((2, 3))):
            T.put(kit.pine(rng.uniform(15, 22), seed=k * 10 + j), cf(rng.uniform(-tw / 2 + 5, tw / 2 - 5), th + 2.2,
                                                                     rng.uniform(-6, 8)))
        T.put(kit.rock(seed=k, s=.9), cf(rng.uniform(-tw / 4, tw / 4), 7.8, -17))
        x, z = polar(R_WALL - 12, a)
        canyon.place(T, cf(x, 0, z, yaw=yaw_to(x, z, 0, 0)), name='Terrace')
        taken.append((x, z, 30))

    # ---- plaza
    PZ = Prop('Plaza')
    PZ.poly(ngon(54, 6, 0), 0.8, 1.6, PLAZA_RIM, name='PlazaRim')
    PZ.poly(ngon(47, 6, 0), 1.4, 1.0, PLAZA, name='PlazaFloor')
    PZ.poly(ngon(22, 6, 30), 1.7, 0.6, PLAZA_DK, name='PlazaInlay')
    plaza.place(PZ, cf(), cls=None)
    plaza.place(sprout_statue(), cf(0, 1.7, 0))
    for (a, accent, nm) in ((0, '#ffd23c', 'SellShop'), (120, '#5fd35a', 'SeedShop'), (240, '#58a6ff', 'UpgradeShop')):
        x, z = polar(33, a)
        plaza.place(shop_prop(accent, name=nm), cf(x, 1.4, z, yaw=yaw_to(x, z, 0, 0)), name=nm)
    for a in PLOT_ANGLES:
        for side in (-1, 1):
            x, z = polar(43, a + side * 9)
            plaza.place(kit.lamp(), cf(x, 1.4, z), name='Lamp')
    for a in (60, 180, 300):
        x, z = polar(30, a)
        plaza.place(kit.bench(), cf(x, 1.4, z, yaw=yaw_to(x, z, 0, 0) + 180), name='Bench')
    sx, sz = polar(20, 270)
    S = Prop('SpawnLocation')
    S.box((10, 1, 10), (0, 0.5, 0), PLAZA_RIM, shape='spawn', name='SpawnLocation')
    plaza.place(S, cf(sx, 1.7, sz, yaw=yaw_to(sx, sz, 0, -200)), cls=None)
    taken.append((0, 0, 62))

    # ---- plots (identical, only the accent colour changes)
    for i, a in enumerate(PLOT_ANGLES):
        x, z = polar(PLOT_R, a)
        plots.place(plot_prop(ACCENTS[i]), cf(x, 0, z, yaw=yaw_to(x, z, 0, 0)), name='Plot%d' % (i + 1))

    def in_plot(x, z, pad=6):
        for a in PLOT_ANGLES:
            px, pz = polar(PLOT_R, a)
            yw = math.radians(yaw_to(px, pz, 0, 0))
            dx, dz = x - px, z - pz
            lx = dx * math.cos(yw) - dz * math.sin(yw)      # inverse yaw
            lz = dx * math.sin(yw) + dz * math.cos(yw)
            if abs(lx) < PLOT_W / 2 + pad and -PLOT_D / 2 - 18 - pad < lz < PLOT_D / 2 + pad:
                return True
        return False

    def free(x, z, r):
        if math.hypot(x, z) > R_WALL - 8 - r or in_plot(x, z, r):
            return False
        for (tx, tz, tr) in taken:
            if math.hypot(x - tx, z - tz) < tr + r:
                return False
        return True

    # ---- pine groves between the plots and along the wall foot (odd clusters)
    n_trees = 0
    for a in [k * 60 for k in range(6)] + [k * 60 + 30 for k in range(6)]:
        for attempt in range(40):
            r = rng.uniform(150, 188)
            cx, cz = polar(r, a + rng.uniform(-8, 8))
            if free(cx, cz, 10):
                break
        else:
            continue
        for j in range(rng.choice((3, 5))):
            for _ in range(20):
                x, z = cx + rng.uniform(-11, 11), cz + rng.uniform(-11, 11)
                if free(x, z, 3.5):
                    h = rng.uniform(14, 24)
                    nature.place(kit.pine(h, seed=rng.randrange(9999)), cf(x, 0, z, yaw=rng.uniform(0, 90)), name='Pine')
                    taken.append((x, z, 4.5))
                    n_trees += 1
                    break
        rx, rz = cx + rng.uniform(-8, 8), cz + rng.uniform(-8, 8)
        if free(rx, rz, 3):
            nature.place(kit.rock(seed=rng.randrange(999)), cf(rx, 0, rz), name='Rock')
            taken.append((rx, rz, 4))
    # bushes and rocks scattered at the wall foot
    for k in range(26):
        a = rng.uniform(0, 360)
        x, z = polar(rng.uniform(180, 194), a)
        if free(x, z, 3):
            P = kit.rock(seed=k, s=rng.uniform(.8, 1.3)) if k % 2 else kit.bush(seed=k)
            nature.place(P, cf(x, 0, z, yaw=rng.uniform(0, 90)), name=P.name)
            taken.append((x, z, 4))

    views = [
        dict(name='overview', pos=list(polar(235, 245))[:1] + [150] + list(polar(235, 245))[1:], target=[0, 0, 10], fov=60),
        dict(name='spawn_view', pos=[0, 7.5, -18], target=[0, 5, -110], fov=70),
        dict(name='plot_closeup', pos=[46, 42, -58], target=[0, 2, -118], fov=55),
        dict(name='plaza', pos=[58, 30, 52], target=[0, 6, 0], fov=60),
        dict(name='canyon_wall', pos=[-60, 26, 60], target=[-150, 20, 120], fov=60),
        dict(name='plan', pos=[0, 950, 0.01], target=[0, 0, 0], fov=33),
    ]
    return root, views
