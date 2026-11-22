"""Tennis stadium (realistic look, no brands): a centre-court stadium with packed stands, navy walls, a blue hard court
on a green surround, umpire chair, players' benches, light towers and two big screens, plus a lobby plaza with the
spawn, a fountain and two outer courts with bleachers.

Every court is a Model under Courts with the parts the game's server looks for: Origin (centre of the net on the
court surface, LookVector toward side 2), PadBot / Pad1 / Pad2 (stand on them to play), NetWall, Exit and
Scoreboard screens. Court sizes come from the game's Config (78 x 36 doubles court, 21 run-off, 15 at the sides).
Roblox space, studs, front = -Z. SmoothPlastic everywhere (no studs).
"""
import math
import random

from studmap.core import Group, Prop, cf

NAME = 'TennisStadium'

L, W, WS, SL = 78.0, 36.0, 27.0, 21.0
RUN_BACK, RUN_SIDE = 21.0, 15.0
AX, AZ = W / 2 + RUN_SIDE, L / 2 + RUN_BACK            # apron half extents: 33 x 60
SURF = 0.15                                            # court surface height (court space y = 0)

GRASS = '#5f9e4f'
APRON = '#4f8f6e'          # green surround
COURT = '#2f63b0'          # blue court
LINE = '#f4f6f8'
NAVY = '#16264f'
NAVY_LT = '#22386e'
CONCRETE = '#a6a9ad'
CONCRETE_DK = '#7d8186'
SEAT = '#1d3f8f'
SEAT_ALT = '#2b55b5'
PLAZA = '#d9d3c7'
PLAZA_DK = '#c6bfb1'
METAL = '#3a3f48'
WHITE = '#f4f5f7'
SKIN = ['#f1c27d', '#e0ac69', '#c68642', '#8d5524', '#ffdbac', '#f5d0a9']
SHIRTS = ['#e8e8e8', '#1c1c1c', '#d33b3b', '#2d6cdf', '#f2c230', '#2f9e5b', '#ff7f2a', '#7d4cc9', '#ffffff',
          '#9ec9ff', '#ff9bc1', '#5a5a5a', '#14326b', '#c9d64a']


def smooth(P):
    for p in P.parts:
        if p.mat == 'plastic':
            p.mat = 'smooth'
        p.studs = False
    return P


# ------------------------------------------------------------------ court surface, lines and net
def court_floor(name='CourtFloor'):
    """apron + blue court + every line, in court space (origin = net centre on the surface)"""
    P = Prop(name)
    P.span(-AX, AX, -0.5, SURF - 0.05, -AZ, AZ, APRON, name='Apron')
    P.span(-W / 2, W / 2, SURF - 0.1, SURF, -L / 2, L / 2, COURT, name='Court')
    lw, top = 0.35, SURF + 0.05

    def line(x0, x1, z0, z1):
        P.span(x0, x1, SURF - 0.02, top, z0, z1, LINE, name='Line', collide=False, shadow=False)
    for x in (-W / 2, W / 2, -WS / 2, WS / 2):
        line(x - lw / 2, x + lw / 2, -L / 2, L / 2)
    for z in (-L / 2, L / 2):
        line(-W / 2, W / 2, z - lw / 2, z + lw / 2)
    for z in (-SL, SL):
        line(-WS / 2, WS / 2, z - lw / 2, z + lw / 2)
    line(-lw / 2, lw / 2, -SL, SL)
    for s in (-1, 1):
        line(-lw / 2, lw / 2, s * L / 2 - (1.2 if s > 0 else 0), s * L / 2 + (0 if s > 0 else 1.2))
    return smooth(P)


def net(name='Net'):
    P = Prop(name)
    post_x = 21.0
    for s in (-1, 1):
        P.cyl(3.6, 0.28, (s * post_x, SURF + 1.8, 0), '#1f4d3a', name='NetPost')
        P.cyl(0.25, 0.4, (s * post_x, SURF + 3.65, 0), '#1f4d3a', name='NetPostCap')
        # the net body for this half, and its white tape sagging from 3.5 at the post to 3.0 in the middle
        P.span(s * post_x if s < 0 else 0, 0 if s < 0 else s * post_x, SURF, SURF + 3.0, -0.05, 0.05, '#20242c',
               name='NetMesh', tr=0.35, collide=False, shadow=False)
        ln = math.hypot(post_x, 0.5)
        roll = math.degrees(math.atan2(0.5, post_x)) * s
        P.box((ln, 0.3, 0.14), (s * post_x / 2, SURF + 3.1, 0), WHITE, roll=roll, name='NetTape', collide=False)
        P.box((ln, 0.12, 0.08), (s * post_x / 2, SURF + 0.1, 0), WHITE, name='NetCord', collide=False)
    P.box((0.3, 3.0, 0.16), (0, SURF + 1.5, 0), WHITE, name='CenterStrap', collide=False)
    return smooth(P)


def umpire_chair(name='UmpireChair'):
    """tall umpire chair (front toward +X, the court), with a seated umpire"""
    P = Prop(name)
    h = 7.5
    for dx in (-1.2, 1.2):
        for dz in (-1.2, 1.2):
            P.box((0.3, h, 0.3), (dx, h / 2, dz), METAL)
    P.box((3.2, 0.4, 3.2), (0, h, 0), NAVY_LT)
    P.box((2.6, 0.4, 2.4), (-0.2, h + 1.2, 0), NAVY)
    P.box((0.4, 2.8, 2.6), (-1.4, h + 2.0, 0), NAVY)
    P.box((1.6, 0.3, 3.4), (1.5, h + 1.3, 0), '#d8dde6')   # desk
    for i in range(6):                                    # ladder at the back
        P.box((0.2, 0.15, 1.8), (-2.2, 1 + i * 1.2, 0), METAL)
    P.box((0.2, h, 0.2), (-2.2, h / 2, -0.9), METAL)
    P.box((0.2, h, 0.2), (-2.2, h / 2, 0.9), METAL)
    # umpire: navy blazer, white shirt, cap
    y = h + 1.4
    P.box((1.0, 2.0, 2.0), (-0.3, y + 1.0, 0), NAVY, name='Umpire')
    P.box((0.9, 1.0, 1.0), (-0.3, y + 2.5, 0), SKIN[0], name='UmpireHead', mat='smooth')
    P.box((1.0, 0.25, 1.1), (-0.25, y + 3.1, 0), WHITE, name='UmpireCap')
    P.box((1.2, 0.6, 0.6), (0.4, y + 1.2, 0.8), NAVY, name='UmpireArm')
    P.box((1.2, 0.6, 0.6), (0.4, y + 1.2, -0.8), NAVY, name='UmpireArm')
    P.box((2.2, 0.9, 1.9), (0.7, y, 0), '#2b2f38', name='UmpireLegs')
    return smooth(P)


def bench(name='PlayerBench'):
    """players' chair under a shade, with a towel and a drinks cooler (front toward +X)"""
    P = Prop(name)
    P.box((1.8, 0.3, 2.0), (0, 1.6, 0), NAVY_LT)
    P.box((0.3, 2.0, 2.0), (-0.9, 2.6, 0), NAVY_LT)
    for dz in (-0.8, 0.8):
        P.box((0.2, 1.6, 0.2), (0.6, 0.8, dz), METAL)
        P.box((0.2, 1.6, 0.2), (-0.6, 0.8, dz), METAL)
    P.box((0.6, 1.1, 0.2), (-0.7, 2.6, 0.95), WHITE, name='Towel')
    P.box((1.4, 1.2, 1.2), (0.2, 0.6, 2.2), '#d23c3c', name='Cooler')
    P.box((1.5, 0.2, 1.3), (0.2, 1.3, 2.2), WHITE, name='CoolerLid')
    P.cyl(6.0, 0.12, (-0.3, 3.0, 0), METAL, name='ShadePole')
    P.box((4.5, 0.3, 4.5), (-0.3, 6.0, 0), WHITE, name='Shade')
    return smooth(P)


def screen(name='Scoreboard', w=44.0, h=20.0, legs=14.0):
    """big video screen on a frame; the part named Scoreboard shows the live score (front face)"""
    P = Prop(name)
    P.box((w, h, 1.6), (0, legs + h / 2, 0.8), '#101418', name='ScreenFrame')
    P.box((w - 3, h - 2.5, 0.4), (0, legs + h / 2, -0.1), '#0a1228', name='Scoreboard', mat='smooth')
    for x in (-w * 0.36, w * 0.36):
        P.box((1.4, legs, 1.4), (x, legs / 2, 1.2), METAL, name='ScreenLeg')
    return smooth(P)


def light_tower(h, name='LightTower'):
    P = Prop(name)
    P.box((2.0, h, 2.0), (0, h / 2, 0), METAL)
    P.box((10, 6, 1.2), (0, h + 3, 0), '#2a2f38', name='LampRack')
    for i in range(4):
        for j in range(2):
            P.box((2.0, 2.0, 0.4), (-3.6 + i * 2.4, h + 1.6 + j * 2.6, -0.7), '#fff6d8', mat='neon', name='Lamp')
    return smooth(P)


# ------------------------------------------------------------------ the stands
def stands(rng, rows=18, gap_south=16.0, people=True, wall_h=4.5):
    """four tiers of stepped stands around the apron, a navy wall in front, a roof band on top. The south end
    (+Z, behind side 1) has the entrance gap. Returns (Prop, outer half extents)."""
    P = Prop('Stands')
    rd, rh = 2.6, 1.45                       # row depth and rise
    x0, z0 = AX + 1.0, AZ + 1.0              # inside face of the walls
    # walls with a lighter band (blank boards, no logos)
    for s in (-1, 1):
        P.span(s * x0, s * (x0 + 1), 0, wall_h, -z0 - 1, z0 + 1, NAVY, name='Wall')
        P.span(s * (x0 - 0.05), s * (x0 + 0.02), 1.4, 3.0, -z0, z0, NAVY_LT, name='WallBoard', collide=False)
    for s in (-1, 1):
        if s > 0:
            for a, b in ((-x0 - 1, -gap_south / 2), (gap_south / 2, x0 + 1)):
                P.span(a, b, 0, wall_h, s * z0, s * (z0 + 1), NAVY, name='Wall')
        else:
            P.span(-x0 - 1, x0 + 1, 0, wall_h, s * z0, s * (z0 + 1), NAVY, name='Wall')
    seats = []
    for i in range(rows):
        d = 2.0 + i * rd
        top = wall_h + 0.6 + i * rh
        # long sides (east / west) run past the corners
        for s in (-1, 1):
            xa, xb = s * (x0 + d), s * (x0 + d + rd)
            za = z0 + d + rd
            P.span(xa, xb, 0, top, -za, za, CONCRETE if i % 2 else CONCRETE_DK, name='Terrace')
            seats.append(('x', s, (xa + xb) / 2, -za, za, top))
        # ends (north / south)
        for s in (-1, 1):
            za, zb = s * (z0 + d), s * (z0 + d + rd)
            xa = x0 + d
            if s > 0 and i < rows:
                for a, b in ((-xa, -gap_south / 2), (gap_south / 2, xa)):
                    P.span(a, b, 0, top, za, zb, CONCRETE if i % 2 else CONCRETE_DK, name='Terrace')
                seats.append(('z', s, (za + zb) / 2, -xa, -gap_south / 2, top))
                seats.append(('z', s, (za + zb) / 2, gap_south / 2, xa, top))
            else:
                P.span(-xa, xa, 0, top, za, zb, CONCRETE if i % 2 else CONCRETE_DK, name='Terrace')
                seats.append(('z', s, (za + zb) / 2, -xa, xa, top))
    # seats (one long strip per row and side) and the crowd
    crowd = 0
    for axis, s, c, a, b, top in seats:
        ln = b - a
        mid = (a + b) / 2
        col = SEAT if int(abs(top) * 10) % 2 else SEAT_ALT
        back = c + s * 0.9
        if axis == 'x':
            P.span(c - 0.8, c + 0.8, top, top + 0.5, a, b, col, name='SeatRow', collide=False)
            P.span(back - 0.15, back + 0.15, top, top + 1.6, a, b, col, name='SeatBack', collide=False)
        else:
            P.span(a, b, top, top + 0.5, c - 0.8, c + 0.8, col, name='SeatRow', collide=False)
            P.span(a, b, top, top + 1.6, back - 0.15, back + 0.15, col, name='SeatBack', collide=False)
        if not people:
            continue
        n = int(ln // 2.3)
        for k in range(n):
            if rng.random() > 0.8:
                continue
            u = a + (k + 0.5) * ln / n + rng.uniform(-0.25, 0.25)
            shirt = rng.choice(SHIRTS)
            skin = rng.choice(SKIN)
            lean = rng.uniform(-0.15, 0.15)
            if axis == 'x':
                P.box((0.9, 1.7, 1.4), (c + s * 0.2 + lean, top + 1.3, u), shirt, name='Fan', collide=False, shadow=False)
                P.box((0.8, 0.8, 0.8), (c + s * 0.15 + lean, top + 2.6, u), skin, name='FanHead', collide=False, shadow=False)
            else:
                P.box((1.4, 1.7, 0.9), (u, top + 1.3, c + s * 0.2 + lean), shirt, name='Fan', collide=False, shadow=False)
                P.box((0.8, 0.8, 0.8), (u, top + 2.6, c + s * 0.15 + lean), skin, name='FanHead', collide=False, shadow=False)
            crowd += 1
    # roof band around the top and the back walls of the top row
    d = 2.0 + rows * rd
    top = wall_h + 0.6 + rows * rh
    ox, oz = x0 + d, z0 + d
    for s in (-1, 1):
        P.span(s * ox, s * (ox + 1.5), 0, top + 9, -oz - 1.5, oz + 1.5, NAVY, name='BackWall')
        P.span(s * (ox - 6), s * (ox + 1.5), top + 9, top + 11, -oz - 1.5, oz + 1.5, NAVY_LT, name='Roof')
        if s > 0:
            for a, b in ((-ox - 1.5, -gap_south / 2), (gap_south / 2, ox + 1.5)):
                P.span(a, b, 0, top + 9, s * oz, s * (oz + 1.5), NAVY, name='BackWall')
            P.span(-gap_south / 2, gap_south / 2, top - 2, top + 9, s * oz, s * (oz + 1.5), NAVY, name='BackWall')
        else:
            P.span(-ox - 1.5, ox + 1.5, 0, top + 9, s * oz, s * (oz + 1.5), NAVY, name='BackWall')
        P.span(-ox - 1.5, ox + 1.5, top + 9, top + 11, s * (oz - 6), s * (oz + 1.5), NAVY_LT, name='Roof')
    # outside facade: vertical ribs, a bright band under the roof and a glass concourse strip
    H = top + 9
    for s in (-1, 1):
        for k in range(-int(oz // 12), int(oz // 12) + 1):
            P.span(s * (ox + 1.5), s * (ox + 2.3), 0, H, k * 12 - 0.8, k * 12 + 0.8, NAVY_LT, name='FacadeRib')
        P.span(s * (ox + 1.5), s * (ox + 1.7), H - 4, H - 2.5, -oz, oz, WHITE, name='FacadeBand')
        P.span(s * (ox + 1.5), s * (ox + 1.7), 10, 14, -oz, oz, '#6fa8dc', name='Concourse', mat='glass', tr=0.2)
        for k in range(-int(ox // 12), int(ox // 12) + 1):
            if s > 0 and abs(k * 12) < gap_south / 2 + 2:
                continue
            P.span(k * 12 - 0.8, k * 12 + 0.8, 0, H, s * (oz + 1.5), s * (oz + 2.3), NAVY_LT, name='FacadeRib')
        P.span(-ox, ox, H - 4, H - 2.5, s * (oz + 1.5), s * (oz + 1.7), WHITE, name='FacadeBand')
        if s < 0:
            P.span(-ox, ox, 10, 14, s * (oz + 1.5), s * (oz + 1.7), '#6fa8dc', name='Concourse', mat='glass', tr=0.2)
        else:
            for a, b in ((-ox, -gap_south / 2 - 1), (gap_south / 2 + 1, ox)):
                P.span(a, b, 10, 14, s * (oz + 1.5), s * (oz + 1.7), '#6fa8dc', name='Concourse', mat='glass', tr=0.2)
    # the entrance tunnel roof over the south gap (a bridge under the stands)
    P.span(-gap_south / 2 - 0.5, gap_south / 2 + 0.5, 9.0, 10.0, z0, oz, CONCRETE_DK, name='TunnelRoof')
    P.span(-gap_south / 2 - 1, -gap_south / 2, 0, 10, z0, oz, CONCRETE_DK, name='TunnelWall')
    P.span(gap_south / 2, gap_south / 2 + 1, 0, 10, z0, oz, CONCRETE_DK, name='TunnelWall')
    return smooth(P), (ox + 1.5, oz + 1.5, top), crowd


def pad(color, name):
    P = Prop(name)
    P.box((9, 0.6, 9), (0, 0.3, 0), '#2b2f38', name=name)
    P.box((7.6, 0.2, 7.6), (0, 0.65, 0), color, mat='neon', name='PadGlow', collide=False)
    return smooth(P)


def tree(rng, name='Tree'):
    P = Prop(name)
    h = rng.uniform(9, 13)
    P.cyl(h, 0.45, (0, h / 2, 0), '#6b4a2f', name='Trunk')
    for k in range(3):
        s = rng.uniform(6, 8.5) - k * 1.2
        P.ball(s, (rng.uniform(-1, 1), h + k * 2.0 - 1, rng.uniform(-1, 1)), ['#3f8a3a', '#4fa046', '#5bb04f'][k],
               name='Leaves', collide=False)
    return smooth(P)


def planter(rng):
    P = Prop('Planter')
    P.box((10, 2, 10), (0, 1, 0), '#8f8a80')
    P.box((9, 0.3, 9), (0, 2.05, 0), '#4b3a2a')
    P.put(tree(rng), cf(0, 2.2, 0))
    return smooth(P)


def lamp():
    P = Prop('Lamp')
    P.cyl(12, 0.25, (0, 6, 0), METAL)
    P.box((2.6, 0.4, 0.8), (0.9, 12, 0), METAL)
    P.box((1.6, 0.3, 0.6), (1.6, 11.7, 0), '#fff2c4', mat='neon', collide=False)
    return smooth(P)


def plaza_bench():
    P = Prop('Bench')
    P.box((6, 0.4, 1.8), (0, 1.5, 0), '#a8774d')
    P.box((6, 1.4, 0.3), (0, 2.4, 0.8), '#a8774d')
    for x in (-2.4, 2.4):
        P.box((0.4, 1.5, 1.6), (x, 0.75, 0), METAL)
    return smooth(P)


def fountain():
    P = Prop('Fountain')
    P.cyl(1.6, 13, (0, 0.8, 0), '#bfb8ab', name='Rim')
    P.cyl(1.4, 12, (0, 0.95, 0), '#58b6e0', name='Water', mat='glass', tr=0.25, collide=False)
    P.cyl(4, 2, (0, 2, 0), '#bfb8ab', name='Column')
    P.cyl(0.8, 5, (0, 4.2, 0), '#bfb8ab', name='Bowl')
    P.cyl(0.6, 4.4, (0, 4.6, 0), '#58b6e0', name='BowlWater', mat='glass', tr=0.25, collide=False)
    P.ball(5.0, (0, 6.5, 0), '#e8f12e', name='BigBall', mat='smooth')    # a giant tennis ball statue
    for k in range(8):
        a = k / 8 * math.pi * 2
        P.box((0.3, 2.2, 0.3), (math.cos(a) * 7, 2.1, math.sin(a) * 7), '#bfe9ff', mat='neon', name='Jet',
              collide=False, tr=0.3)
    return smooth(P)


def court_model(root, name, origin, rng, pads_at, exit_at, people=True, center=False):
    """one playable court: floor + lines + net + chair + benches (+ stadium when center) and the game parts"""
    M = root.add(Group(name, 'Model'))
    ox, oy, oz = origin
    M.place(court_floor(), cf(ox, oy, oz), cls=None)
    M.place(net(), cf(ox, oy, oz), cls=None)
    M.place(umpire_chair(), cf(ox - (W / 2 + 6), oy, oz), cls=None)
    for s in (-1, 1):
        M.place(bench(), cf(ox - (W / 2 + 7), oy, oz + s * 6), cls=None)
    g = Prop('Game')
    g.box((2, 0.2, 2), (0, SURF, 0), '#ffffff', name='Origin', tr=1, collide=False, shadow=False)
    g.box((2 * AX + 2, 14, 0.6), (0, SURF + 7, 0), '#ffffff', name='NetWall', tr=1, collide=False, shadow=False)
    for p in g.parts:
        p.studs = False
        p.mat = 'smooth'
    M.place(g, cf(ox, oy, oz), cls=None)
    for nm, (px, pz), col in zip(('PadBot', 'Pad1', 'Pad2'), pads_at, ('#ffd233', '#4696ff', '#ff7846')):
        M.place(pad(col, nm), cf(px, oy, pz), cls=None)
    ex = Prop('Exit')
    ex.box((4, 0.2, 4), (0, 0.1, 0), '#ffffff', name='Exit', tr=1, collide=False, shadow=False)
    M.place(smooth(ex), cf(exit_at[0], oy + 0.5, exit_at[1]), cls=None)
    info = {}
    if center:
        S, outer, crowd = stands(rng, rows=18, people=people)
        M.place(S, cf(ox, oy, oz), cls=None)
        top = outer[2]
        M.place(screen(), cf(ox, oy + top - 12, oz - outer[1] + 4, yaw=180), cls=None)
        M.place(screen(), cf(ox, oy + top - 12, oz + outer[1] - 4), cls=None)
        for sx in (-1, 1):
            for sz in (-1, 1):
                M.place(light_tower(top + 16), cf(ox + sx * (outer[0] - 3), oy, oz + sz * (outer[1] - 3),
                                                  yaw=45 * sx * sz + (180 if sz < 0 else 0)), cls=None)
        info = dict(outer=outer, crowd=crowd)
    return M, info


def outer_court_dressing(M, origin, rng, bleacher_side):
    """windscreen fence around an outer court with a gate toward the plaza, and bleachers on the far side"""
    ox, oy, oz = origin
    P = Prop('Fence')
    fx, fz, h = AX + 0.5, AZ + 0.5, 7
    gate = -bleacher_side
    for s in (-1, 1):
        P.span(-fx - 0.3, fx + 0.3, 0, h, s * fz - 0.15, s * fz + 0.15, '#1f4d3a', name='Windscreen')
        if s == gate:
            for a, b in ((-fz, -6), (6, fz)):
                P.span(s * fx - 0.15, s * fx + 0.15, 0, h, a, b, '#1f4d3a', name='Windscreen')
        else:
            P.span(s * fx - 0.15, s * fx + 0.15, 0, h, -fz, fz, '#1f4d3a', name='Windscreen')
        for k in range(-5, 6):
            P.cyl(h + 0.6, 0.18, (s * fx, (h + 0.6) / 2, k * fz / 5.5), METAL, name='FencePost')
    # bleachers: 6 rows along the far side, with a few fans
    for i in range(6):
        x = bleacher_side * (fx + 2 + i * 2.4)
        top = 1.0 + i * 1.2
        P.span(x - 1.2, x + 1.2, 0, top, -30, 30, '#9aa0a8' if i % 2 else '#858b93', name='Bleacher')
        P.span(x - 0.6, x + 0.6, top, top + 0.35, -30, 30, SEAT_ALT, name='BleacherSeat', collide=False)
        for k in range(26):
            if rng.random() < 0.45:
                z = -29 + k * 2.3
                P.box((0.9, 1.7, 1.4), (x + bleacher_side * 0.2, top + 1.2, z), rng.choice(SHIRTS), name='Fan',
                      collide=False, shadow=False)
                P.box((0.8, 0.8, 0.8), (x + bleacher_side * 0.15, top + 2.5, z), rng.choice(SKIN), name='FanHead',
                      collide=False, shadow=False)
    M.place(smooth(P), cf(ox, oy, oz), cls=None)


def build():
    rng = random.Random(7)
    root = Group(NAME, 'Model')
    world = root.add(Group('World', 'Folder'))
    courts = root.add(Group('Courts', 'Folder'))

    base = Prop('Ground')
    base.span(-450, 450, -1, 0, -300, 520, GRASS, name='Grass')
    world.place(smooth(base), cf(), cls=None)

    # centre court: net centre at the world origin, side 1 (+Z) toward the plaza
    _, info = court_model(courts, 'Center Court', (0, 0, 0), rng,
                          pads_at=((0, 136), (-15, 136), (15, 136)), exit_at=(0, 150), center=True)
    outer = info['outer']

    # plaza south of the stadium
    pz0, pz1 = outer[1] + 2, 330
    P = Prop('Plaza')
    P.span(-100, 100, -0.4, 0.1, pz0, pz1, PLAZA, name='PlazaFloor')
    for k in range(int((pz1 - pz0) // 12)):
        P.span(-100, 100, 0.05, 0.16, pz0 + k * 12 + 5.8, pz0 + k * 12 + 6.2, PLAZA_DK, name='PlazaJoint',
               collide=False, shadow=False)
    P.span(-9, 9, -0.4, 0.1, AZ + 1, pz0, PLAZA_DK, name='TunnelFloor')
    P.span(-100, 100, -0.4, 0.1, pz1, pz1 + 10, PLAZA_DK, name='PlazaEdge')
    world.place(smooth(P), cf(), cls=None)
    spawn = Prop('Spawn')
    spawn.box((12, 1, 12), (0, 0.5, 0), '#f4f5f7', shape='spawn', name='SpawnLocation', mat='smooth', studs=False)
    world.place(spawn, cf(0, 0, 200, yaw=0), cls=None)
    world.place(fountain(), cf(0, 0.1, 255))
    for x in (-80, -40, 40, 80):
        for z in (pz0 + 30, 260, 310):
            world.place(planter(rng), cf(x, 0.1, z))
    for x in (-60, -20, 20, 60):
        world.place(lamp(), cf(x, 0.1, pz0 + 50, yaw=90 if x > 0 else -90))
        world.place(lamp(), cf(x, 0.1, 290, yaw=90 if x > 0 else -90))
    for x in (-50, 50):
        for z in (225, 285):
            world.place(plaza_bench(), cf(x, 0.1, z, yaw=180 if x > 0 else 0))
    # entrance arch with a sign (text added by the place builder: part "Sign")
    A = Prop('Entrance')
    for s in (-1, 1):
        A.box((3, 22, 3), (s * 14, 11, 0), NAVY)
    A.box((34, 5, 2), (0, 22, 0), NAVY_LT)
    A.box((30, 3.6, 0.4), (0, 22, -1.2), '#0f1a38', name='Sign', mat='smooth')
    world.place(smooth(A), cf(0, 0.1, pz0 + 4, yaw=180))

    # two outer courts beside the plaza
    for name, sx in (('Court 2', -1), ('Court 3', 1)):
        ox, oz = sx * 140, 230
        M, _ = court_model(courts, name, (ox, 0, oz), rng,
                           pads_at=((sx * 88, oz), (sx * 88, oz - 16), (sx * 88, oz + 16)),
                           exit_at=(sx * 80, oz), center=False)
        outer_court_dressing(M, (ox, 0, oz), rng, bleacher_side=sx)
        M.place(screen(w=20, h=9, legs=6), cf(ox, 0, oz - AZ - 4, yaw=180), cls=None)
        F = Prop('CourtPath')
        F.span(min(sx * 100, sx * 105), max(sx * 100, sx * 105), -0.4, 0.1, oz - 8, oz + 8, PLAZA_DK, name='Path')
        world.place(smooth(F), cf(), cls=None)

    # trees around the stadium outside
    for k in range(40):
        a = k / 40 * math.pi * 2
        r = 150 + rng.uniform(0, 30)
        x, z = math.cos(a) * r * 1.1, math.sin(a) * r * 0.85 - 20
        if z > outer[1] - 10 and abs(x) < 190:
            continue
        world.place(tree(rng), cf(x, 0, z))

    views = [
        dict(name='stadium', pos=[150, 120, 210], target=[0, 5, 0], fov=55),
        dict(name='tv_camera', pos=[0, 19, 69], target=[0, 0, -4], fov=52),
        dict(name='court_side', pos=[52, 30, 36], target=[0, 2, -5], fov=60),
        dict(name='stands', pos=[-20, 12, 40], target=[40, 18, -40], fov=70),
        dict(name='plaza', pos=[0, 30, 330], target=[0, 6, 160], fov=60),
        dict(name='outer_court', pos=[60, 40, 300], target=[140, 0, 230], fov=60),
        dict(name='plan', pos=[0, 900, 120.01], target=[0, 0, 120], fov=45),
    ]
    print('crowd', info['crowd'])
    return root, views, dict(center=[0, 0, 100], radius=360)
