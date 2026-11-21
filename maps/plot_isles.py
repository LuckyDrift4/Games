"""Plot Isles: eight player plot islands in a bright sea, joined by a main road island (smooth low-poly style).

Every plot is identical: sand beach, grass top, a road spine from its bridge to a conveyor at the back, and eight
pads (two columns of four) on short side paths. The main road runs east-west between the two rows of plots with a
spawn plaza and shop at its west end. SmoothPlastic everywhere (no studs). Roblox space, studs, front = -Z.
"""
import math
import random

from studmap.core import Group, Prop, cf, yaw_to
from studmap import kit

NAME = 'PlotIsles'

SEA = '#45b6ef'
SHALLOW = '#82d6f8'
SAND = '#f0dcae'
SAND_DK = '#d9c08e'
GRASS = '#74d65a'
ROAD = '#7d5d4c'
PAD = '#c9a589'
PAD_IN = '#e3c7ab'
BELT = '#3d8ef0'

PLOT_W, PLOT_D = 96, 120
XS = [-165, -55, 55, 165]
ROW_Z = 95                       # plot centre distance north / south of the road


def smooth(P):
    for p in P.parts:
        if p.mat == 'plastic':
            p.mat = 'smooth'
        p.studs = False
    return P


def palm(h=16.0, seed=0, name='Palm'):
    rng = random.Random(seed)
    P = Prop(name)
    lean = rng.uniform(.18, .32)
    n = 6
    x = 0.0
    for k in range(n):
        y = k * h / n
        P.box((1.7 - k * .12, h / n + .4, 1.7 - k * .12), (x, y + h / n / 2, 0), '#a8784f' if k % 2 else '#b98a5c',
              roll=-math.degrees(lean) * .8)
        x += lean * h / n
    top = (x, h, 0)
    for k in range(7):
        a = k * 360 / 7 + rng.uniform(-10, 10)
        L = rng.uniform(6.5, 8.5)
        r = math.radians(a)
        P.box((L, .4, 2.2), (top[0] + math.cos(r) * L * .42, h - .6, top[2] + math.sin(r) * L * .42),
              '#3fbf4f' if k % 2 else '#56d25a', yaw=-a, roll=-24)
    for k in range(3):
        r = math.radians(k * 120 + 30)
        P.ball(1.1, (top[0] + math.cos(r) * .9, h - 1.4, top[2] + math.sin(r) * .9), '#7a5235')
    return smooth(P)


def plot_island(accent):
    """local: road enters at -Z (front, toward the main road), conveyor at the back (+Z)"""
    P = Prop('Plot')
    hw, hd = PLOT_W / 2, PLOT_D / 2
    P.span(-hw - 4, hw + 4, -1.6, -1.3, -hd - 4, hd + 4, SHALLOW, name='Shallows')
    P.span(-hw, hw, -6, .8, -hd, hd, SAND, name='Beach')
    P.span(-hw + 5, hw - 5, .8, 1.4, -hd + 5, hd - 5, GRASS, name='Grass')
    P.span(-hw + 2, hw - 2, -1.2, .8, -hd - 1.4, -hd, SAND_DK, name='BeachEdge')
    # road spine + side paths + pads
    P.span(-4, 4, 1.4, 1.6, -hd, hd - 22, ROAD, name='Road')
    for row in range(4):
        z = -hd + 24 + row * 21
        for s in (-1, 1):
            P.span(s * 4, s * 16, 1.4, 1.6, z - 2.5, z + 2.5, ROAD, name='Road')
            P.span(s * 16, s * 30, 1.4, 1.9, z - 7, z + 7, PAD, name='Pad')
            P.span(s * 17, s * 29, 1.9, 2.1, z - 6, z + 6, PAD_IN, name='PadTop')
    # conveyor across the back
    cz = hd - 15
    P.span(-30, 30, 1.4, 3.4, cz - 3.4, cz + 3.4, '#4b4b5e', name='ConveyorFrame')
    P.span(-29, 29, 3.4, 3.7, cz - 2.4, cz + 2.4, BELT, name='ConveyorBelt')
    for k in range(10):
        x = -26 + k * 5.8
        P.span(x - .6, x + .6, 3.7, 3.8, cz - 2.4, cz + 2.4, '#8cc4ff', name='BeltStripe')
    for s in (-1, 1):
        P.cyl(6.2, 1.8, (s * 30.5, 3.0, cz), '#6c6c84', axis='z', name='Roller')
        P.span(s * 31, s * 35, 1.4, 6.0, cz - 3.6, cz + 3.6, accent, name='ConveyorEnd')
        P.span(s * 31.6, s * 34.4, 6.0, 6.6, cz - 3.0, cz + 3.0, '#ffffff', name='ConveyorEnd')
    P.span(-4, 4, 1.4, 1.6, cz - 6.5, cz - 3.4, ROAD, name='Road')
    # entrance arch posts with the plot accent
    for s in (-1, 1):
        P.span(s * 6 - 1, s * 6 + 1, 1.4, 9, -hd + 3, -hd + 5, '#ffffff', name='GatePost')
        P.span(s * 6 - 1.3, s * 6 + 1.3, 9, 10, -hd + 2.7, -hd + 5.3, accent, name='GatePost')
    P.span(-7, 7, 8, 9, -hd + 3.2, -hd + 4.8, accent, name='GateBeam')
    # owner sign and greenery
    P.put(smooth(kit.sign(accent)), cf(-14, 1.4, -hd + 8, yaw=180))
    rng = random.Random(hash(accent) & 0xffff)
    for (x, z) in ((-38, -46), (38, -50), (-40, 40), (40, 38), (-38, -2), (39, 6)):
        P.put(palm(rng.uniform(13, 18), seed=rng.randrange(999)), cf(x, 1.4, z, yaw=rng.uniform(0, 360)))
    for (x, z) in ((-33, -52), (34, -38), (-35, 24), (33, 52)):
        P.put(smooth(kit.bush(seed=rng.randrange(999), s=.9)), cf(x, 1.4, z))
    return smooth(P)


def shop_hut():
    P = Prop('Shop')
    P.span(-10, 10, 1.4, 2.2, -8, 8, '#e9d6b8', name='Floor')
    for s in (-1, 1):
        P.span(s * 9.4 - .6, s * 9.4 + .6, 2.2, 10, -7, 7, '#f6efe0', name='Wall')
    P.span(-9.4, 9.4, 2.2, 10, 6.4, 7.6, '#f6efe0', name='Wall')
    P.span(-8, 8, 2.2, 5.6, -7.6, -5.6, '#4fb3e8', name='Counter')
    P.span(-8.4, 8.4, 5.6, 6.2, -8, -5.2, '#ffffff', name='Counter')
    P.put(kit.gable_roof(20, 16, 5.0, '#ff8f6b', '#e06a4a', slat=2.4), cf(0, 10, 0))
    kit.awning(P, 20, 4, 9.6, z=-7.6, colors=('#ff8f6b', '#ffffff'), stripes=7, pitch=22)
    return smooth(P)


def build():
    rng = random.Random(9)
    root = Group(NAME, 'Model')
    world, plots, hub = root.folder('World'), root.folder('Plots'), root.folder('Hub')

    W = Prop('World')
    W.span(-800, 800, -12, -1.5, -800, 800, SEA, mat='smooth', name='Sea')
    # main road island along X with a spawn plaza at the west end
    W.span(-228, 232, -1.6, -1.3, -28, 28, SHALLOW, mat='smooth', name='Shallows')
    W.span(-232, 228, -6, .8, -24, 24, SAND, mat='smooth', name='Beach')
    W.span(-236, 224, .8, 1.4, -20, 20, GRASS, mat='smooth', name='Grass')
    W.span(-230, 220, 1.4, 1.6, -7, 7, ROAD, mat='smooth', name='MainRoad')
    W.span(-290, -228, -1.6, -1.3, -38, 38, SHALLOW, mat='smooth', name='Shallows')
    W.span(-286, -232, -6, .8, -34, 34, SAND, mat='smooth', name='Beach')
    W.span(-282, -236, .8, 1.4, -30, 30, GRASS, mat='smooth', name='Grass')
    W.span(-276, -242, 1.4, 1.7, -24, 24, '#e3c7ab', mat='smooth', name='SpawnPlaza')
    # bridges from the road to each plot across the water gap
    for x in XS:
        for s in (-1, 1):
            z0, z1 = s * 7, s * (ROW_Z - PLOT_D / 2)
            W.span(x - 4, x + 4, 1.4, 1.6, min(z0, z1), max(z0, z1), ROAD, mat='smooth', name='Road')
            zb0, zb1 = s * 23, s * (ROW_Z - PLOT_D / 2)
            W.span(x - 5, x + 5, .6, 1.4, min(zb0, zb1), max(zb0, zb1), '#a8784f', mat='smooth', name='Bridge')
            for zz in (s * 26, s * 32):
                for xs in (-4.4, 4.4):
                    W.span(x + xs - .6, x + xs + .6, -4, 3.6, zz - .6, zz + .6, '#8a5f3c', mat='smooth', name='BridgePost')
            for xs in (-4.4, 4.4):
                W.span(x + xs - .3, x + xs + .3, 3.0, 3.6, min(zb0, zb1), max(zb0, zb1), '#8a5f3c', mat='smooth', name='BridgeRail')
    world.place(W, cf(), cls=None)

    accents = ['#ff6b6b', '#ffb347', '#ffd93d', '#6bcB77', '#4d96ff', '#9d79f2', '#ff8fd1', '#4fd1c5']
    k = 0
    for s in (-1, 1):
        for x in XS:
            z = s * ROW_Z
            plots.place(plot_island(accents[k]), cf(x, 0, z, yaw=yaw_to(x, z, x, 0)), name='Plot%d' % (k + 1))
            k += 1

    sp = Prop('SpawnLocation')
    sp.box((12, 1, 12), (0, .5, 0), '#ffffff', shape='spawn', mat='smooth', name='SpawnLocation')
    hub.place(sp, cf(-249, 1.7, 0), cls=None)
    hub.place(shop_hut(), cf(-266, 0, 0, yaw=-90), name='Shop')
    for (x, z) in ((-278, 26), (-240, 28), (-280, -26), (-238, -27), (-120, 15), (0, -16), (110, 16), (210, -15)):
        hub.place(palm(rng.uniform(14, 19), seed=rng.randrange(999)), cf(x, 1.4, z, yaw=rng.uniform(0, 360)), name='Palm')
    for (x, z) in ((-200, 14), (-60, -15), (60, 15), (170, -14)):
        hub.place(smooth(kit.bush(seed=rng.randrange(999))), cf(x, 1.4, z), name='Bush')
    for x in (-210, -110, 0, 110, 200):
        for s in (-1, 1):
            hub.place(smooth(kit.lamp('#fff2b3', '#6c6c84')), cf(x, 1.4, s * 10), name='Lamp')

    views = [
        dict(name='overview', pos=[-120, 260, 330], target=[-10, 0, -10], fov=55),
        dict(name='plot_closeup', pos=[-120, 60, -10], target=[-165, 2, -100], fov=60),
        dict(name='spawn', pos=[-214, 16, 34], target=[-262, 5, 0], fov=60),
        dict(name='road_view', pos=[-226, 8, 0], target=[0, 4, 0], fov=65),
        dict(name='plan', pos=[0, 900, 0.01], target=[0, 0, 0], fov=40),
    ]
    return root, views, dict(center=[0, 0, 0], radius=340)
