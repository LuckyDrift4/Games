"""Sky Sprint: floating stud islands with a long runway (stud style).

A hub island cluster (spawn, egg pad, rebirth pad, shop) opens onto a straight runway that runs north (-Z) across
three zones on floating chunks: Meadow, Golden Fields, Frost. Zone arches mark each change; the finish island has a
podium. Islands are grid cells (24 studs) with grass drips over dirt sides. Roblox space, studs, front = -Z.
"""
import math
import random

from studmap.core import Group, Prop, cf, shade, yaw_to
from studmap.islands import Cells
from studmap import kit

NAME = 'SkySprint'
C = 24.0

ZONES = [  # (first j, last j, name, grass, dirt, lane colour, tree kind, leaf, leaf dark)
    (5, 12, 'Meadow', '#6fd94f', '#b47b50', '#f6d84a', 'leafy', '#62d34f', '#45b545'),
    (13, 20, 'GoldenFields', '#f3cd4f', '#b47b50', '#ff9f43', 'leafy', '#ffb347', '#ff8a3d'),
    (21, 28, 'Frost', '#eef5ff', '#8f8db0', '#8fd3ff', 'pine', '#f7fbff', '#3f9a6a'),
]
HUB_GRASS = '#6fd94f'
RED = '#e8453c'
SAND = '#ecd29a'


def zone_of(j):
    for z in ZONES:
        if z[0] <= j <= z[1]:
            return z
    return ZONES[0] if j < 5 else ZONES[-1]


def zc(j):
    return -j * C


def egg_statue():
    P = Prop('EggStatue')
    P.box((9, 2, 9), (0, 1, 0), '#8d89cf')
    P.box((7, 2, 7), (0, 3, 0), '#b3b0cc')
    for (w, h, y) in ((6.0, 2.4, 5.2), (7.0, 3.2, 8.0), (6.4, 3.0, 11.1), (4.6, 2.4, 13.8), (2.6, 1.4, 15.7)):
        P.box((w, h, w), (0, y, 0), '#fff3d6')
    for (x, y, z, c) in ((3.5, 8.6, -1, '#ff8fb0'), (-1.5, 11.2, -3.2, '#58a6ff'), (-3.5, 7.4, 1.5, '#ffd23c'),
                         (1.2, 13.6, 2.3, '#7bd389')):
        P.box((1.6, 1.6, 1.6), (x, y, z), c)
    return P


def build():
    rng = random.Random(5)
    root = Group(NAME, 'Model')
    land, track, hub, deco = root.folder('Islands'), root.folder('Track'), root.folder('Hub'), root.folder('Nature')

    cells = Cells(C, seed=3)
    # hub: 7 x 5 cells, corners cut, a stepped-down outer ring
    for i in range(-3, 4):
        for j in range(0, 5):
            if abs(i) == 3 and j in (0, 4):
                continue
            outer = abs(i) == 3 or j == 0
            cells.add(i, j, top=(-2 if outer and (i + j) % 2 else 0), grass=HUB_GRASS)
    for (i, j) in ((-4, 2), (4, 2), (0, -1), (-1, -1), (1, -1)):
        cells.add(i, j, top=-4, grass=HUB_GRASS)
    # runway: 3 cells wide
    for j in range(5, 29):
        z = zone_of(j)
        cells.rect(-1, 1, j, j, top=0, grass=z[3], dirt=z[4])
    # side islands: groups of cells along the runway, some raised, some floating apart
    j = 5
    side_spots = []
    while j < 28:
        for side in (-1, 1):
            if rng.random() < .75:
                n = rng.choice((2, 2, 3))
                top = rng.choice((0, 0, 4, 8))
                inner = 2 if rng.random() < .7 else 3
                z = zone_of(j)
                for jj in range(j, min(28, j + n) + 1):
                    for ii in range(inner, inner + rng.choice((1, 2))):
                        cells.add(side * ii, jj, top=top, grass=z[3], dirt=z[4])
                        side_spots.append((side * ii, jj, top))
                if rng.random() < .4:                               # a lone floating chunk further out
                    jj = j + rng.randrange(n)
                    cells.add(side * 5, jj, top=rng.choice((10, 14)), grass=z[3], dirt=z[4])
                    side_spots.append((side * 5, jj, None))
        j += rng.choice((3, 4))
    # finish island
    for i in range(-2, 3):
        for jj in range(29, 33):
            if abs(i) == 2 and jj == 32:
                continue
            cells.add(i, jj, top=0, grass='#eef5ff', dirt='#8f8db0')
    I = Prop('Islands')
    cells.build(I)
    land.place(I, cf(), cls=None)

    # ---- runway lanes per zone, start / zone / finish arches, speed chevrons
    for (j0, j1, nm, grass, dirt, lane, *_rest) in ZONES:
        z0, z1 = zc(j0) + C / 2, zc(j1) - C / 2
        T = Prop(nm + 'Lane')
        T.span(-5, 5, -.2, .35, z1, z0, RED, name='RedLane')
        for s in (-1, 1):
            T.span(s * 5, s * 17, -.2, .3, z1, z0, lane, name='SideLane')
            T.span(s * 17, s * 18.2, -.2, .4, z1, z0, '#ffffff', name='EdgeLine')
        for jj in range(j0, j1 + 1, 2):
            T.put(kit.chevron(), cf(0, .35, zc(jj)))
        track.place(T, cf(), name=nm)
    for (jb, nm, glow) in ((5, 'StartArch', '#7dff6a'), (13, 'GoldenArch', '#ffb347'), (21, 'FrostArch', '#8fe8ff'),
                           (29, 'FinishArch', '#ff6ad5')):
        track.place(kit.arch(38, 22, glow=glow), cf(0, 0, zc(jb) + C / 2), name=nm)
    S = Prop('StartLine')
    for k in range(12):
        for r in range(2):
            S.span(-16.8 + k * 2.8, -14.0 + k * 2.8, -.2, .4, zc(5) + C / 2 - 3 + r * 1.5 - 1.5, zc(5) + C / 2 - 3 + r * 1.5,
                   '#ffffff' if (k + r) % 2 == 0 else '#26243a', name='StartLine')
    track.place(S, cf(), cls=None)

    # ---- hub: sand paths, pads, shop, spawn, lamps
    H = Prop('HubGround')
    H.span(-4, 4, -.2, .3, -108, 6, SAND, name='Path')
    H.span(-40, 40, -.2, .3, -52, -44, SAND, name='Path')
    # egg pad (ice-blue glass grid), west
    H.span(-60, -36, -.2, .5, -60, -36, '#8d89cf', name='EggPad')
    for a in range(4):
        for b in range(4):
            x, z = -58 + a * 5.5, -58 + b * 5.5
            H.span(x + .4, x + 5.1, .5, .8, z + .4, z + 5.1, '#bfe9ff', mat='smooth', name='EggPadGlass')
    # rebirth pad, east
    H.span(36, 60, -.2, .5, -60, -36, '#f4f3fa', name='RebirthPad')
    for k in range(8):
        a = k * 45
        H.box((7.2, .3, 1.0), (48 + math.cos(math.radians(a)) * 8.6, .65, -48 + math.sin(math.radians(a)) * 8.6),
              '#b48cff', yaw=-a + 90, mat='neon', collide=False, name='RebirthRing')
    hub.place(H, cf(), cls=None)
    hub.place(egg_statue(), cf(-48, .8, -48, yaw=30), name='EggStatue')
    O = Prop('RebirthObelisk')
    O.box((4, 1.5, 4), (0, .75, 0), '#8d89cf').box((2.6, 12, 2.6), (0, 7.5, 0), '#f4f3fa', yaw=45)
    O.box((2, 3, 2), (0, 15, 0), '#b48cff', yaw=45, mat='neon', collide=False)
    hub.place(O, cf(48, .5, -48), name='RebirthObelisk')
    hub.place(kit.stall('#e8453c', name='Shop'), cf(30, 0, -14, yaw=yaw_to(30, -14, 0, -14)), name='Shop')
    hub.place(kit.sign('#bfe9ff'), cf(-48, 0, -31, yaw=180), name='EggSign')
    hub.place(kit.sign('#b48cff'), cf(48, 0, -31, yaw=180), name='RebirthSign')
    for z in (-20, -70, -96):
        for s in (-1, 1):
            hub.place(kit.lamp(), cf(s * 8, 0, z), name='Lamp')
    sp = Prop('SpawnLocation')
    sp.box((12, 1, 12), (0, .5, 0), '#8d89cf', shape='spawn', name='SpawnLocation')
    hub.place(sp, cf(0, 0, 0), cls=None)
    for (x, z) in ((-60, -6), (-62, -86), (62, -88), (-30, 2), (36, 4)):
        deco.place(kit.leafy_tree(rng.uniform(13, 17), seed=rng.randrange(999)), cf(x, 0, z, yaw=rng.uniform(0, 90)), name='Tree')
    for (x, z) in ((-20, -10), (20, -84), (-24, -90), (58, -20)):
        deco.place(kit.bush(seed=rng.randrange(999)), cf(x, 0, z), name='Bush')

    # ---- trees and dressing on verges and side islands
    def tree(z, x, y, s=1.0):
        if z[6] == 'pine':
            return kit.pine(rng.uniform(14, 20) * s, seed=rng.randrange(9999), dark=z[8], light=z[7], name='Pine')
        return kit.leafy_tree(rng.uniform(12, 17) * s, seed=rng.randrange(9999), leaf=z[7], leaf_dk=z[8],
                              trunk='#8a5432' if z[2] == 'Meadow' else '#7a3f2a')

    for j in range(5, 29):
        z = zone_of(j)
        for s in (-1, 1):
            if rng.random() < .55:
                x = s * rng.uniform(24, 32)
                deco.place(tree(z, x, 0), cf(x, 0, zc(j) + rng.uniform(-8, 8), yaw=rng.uniform(0, 90)), name='Tree')
            elif rng.random() < .5:
                x = s * rng.uniform(22, 32)
                P = kit.bush(seed=rng.randrange(999), dark=z[8], light=z[7]) if z[6] != 'pine' else kit.rock(seed=rng.randrange(99))
                deco.place(P, cf(x, 0, zc(j) + rng.uniform(-8, 8)), name=P.name)
    for (i, j, top) in side_spots:
        if top is None:
            continue
        z = zone_of(j)
        if rng.random() < .6:
            deco.place(tree(z, 0, 0), cf(i * C + rng.uniform(-6, 6), top, zc(j) + rng.uniform(-6, 6), yaw=rng.uniform(0, 90)),
                       name='Tree')
        if rng.random() < .35:
            deco.place(kit.rock(seed=rng.randrange(999), color='#8fa0c8'), cf(i * C + rng.uniform(-7, 7), top,
                                                                                zc(j) + rng.uniform(-7, 7)), name='Rock')

    # ---- finish podium + trophy
    F = Prop('FinishPodium')
    for k, (w, y) in enumerate(((40, 1.6), (28, 5.2), (16, 8.8))):
        F.span(-w / 2, w / 2, y - 1.8 - (1.6 if k == 0 else 0), y + 1.8, -w / 2, w / 2, ('#8d89cf', '#b3b0cc', '#f4f3fa')[k])
    F.span(-3, 3, 10.6, 13.0, -3, 3, '#f5c53a')
    F.box((2.4, 6, 2.4), (0, 16, 0), '#f5c53a')
    F.box((10, 7, 10), (0, 22.5, 0), '#f5c53a', yaw=45)
    F.box((11.4, 1.4, 11.4), (0, 26.6, 0), '#ffd866', yaw=45)
    F.box((6, 1, 6), (0, 19.4, 0), '#ffd866', yaw=45)
    for s in (-1, 1):
        F.box((1.6, 6, 1.6), (s * 6.8, 22.6, 0), '#f5c53a')
        F.box((3.2, 1.6, 1.6), (s * 5.8, 25.0, 0), '#f5c53a')
    F.box((2.2, 2.2, 2.2), (0, 28.6, 0), '#ff6ad5', yaw=45, mat='neon', collide=False)
    track.place(F, cf(0, 0, zc(31)), name='FinishPodium')

    views = [
        dict(name='overview', pos=[150, 105, 110], target=[0, 0, -230], fov=58),
        dict(name='hub', pos=[78, 46, 52], target=[0, 0, -50], fov=60),
        dict(name='runway', pos=[0, 9, -140], target=[0, 6, -320], fov=70),
        dict(name='golden_fields', pos=[70, 36, -300], target=[0, 0, -420], fov=60),
        dict(name='finish', pos=[46, 30, -640], target=[0, 10, -744], fov=62),
        dict(name='underside', pos=[-230, -24, -150], target=[-40, -4, -300], fov=55),
        dict(name='plan', pos=[0, 1250, -335.01], target=[0, 0, -335], fov=33),
    ]
    return root, views, dict(center=[0, 0, -340], radius=480)
