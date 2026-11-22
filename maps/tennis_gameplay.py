"""Tennis game layer: only the Parts the game's scripts use, laid out to match the Blender-made stadium
(out/tennis_stadium_blender), plus plain fallback floors so the place is playable before the stadium is imported.

Courts/<name>: Origin (centre of the net on the court surface, LookVector toward side 2), PadBot / Pad1 / Pad2,
NetWall, Exit, Scoreboard (the score screens, in front of the modelled screens). World/Fallback is removed by
TennisStadiumInstall when the Blender stadium is built. Roblox space, studs.
"""
from studmap.core import Group, Prop, cf

NAME = 'TennisGameplay'

L, W, WS, SL = 78.0, 36.0, 27.0, 21.0
AX, AZ = 33.0, 60.0
SURF = 0.15             # court surface of the Blender stadium (court space y = 0)
PLAZA_Y = 0.12


def smooth(P):
    for p in P.parts:
        if p.mat == 'plastic':
            p.mat = 'smooth'
        p.studs = False
    return P


def fallback_court(ox, oz):
    """a flat court a little BELOW the Blender court surface (no z-fighting when both are there)"""
    P = Prop('FallbackCourt')
    P.span(ox - AX, ox + AX, -.6, .05, oz - AZ, oz + AZ, '#4a8b6a', name='Apron')
    P.span(ox - W / 2, ox + W / 2, -.1, .08, oz - L / 2, oz + L / 2, '#2f63b0', name='Court', collide=False)
    lw = .35
    for x in (-W / 2, W / 2, -WS / 2, WS / 2):
        P.span(ox + x - lw / 2, ox + x + lw / 2, -.05, .1, oz - L / 2, oz + L / 2, '#f4f6f8', name='Line', collide=False)
    for z in (-L / 2, L / 2):
        P.span(ox - W / 2, ox + W / 2, -.05, .1, oz + z - lw / 2, oz + z + lw / 2, '#f4f6f8', name='Line', collide=False)
    for z in (-SL, SL):
        P.span(ox - WS / 2, ox + WS / 2, -.05, .1, oz + z - lw / 2, oz + z + lw / 2, '#f4f6f8', name='Line', collide=False)
    P.span(ox - lw / 2, ox + lw / 2, -.05, .1, oz - SL, oz + SL, '#f4f6f8', name='Line', collide=False)
    P.span(ox - 21, ox + 21, .05, 3.2, oz - .05, oz + .05, '#20242c', name='Net', tr=.35, collide=False)
    return smooth(P)


def court(root, name, origin, pads, exit_at, boards):
    M = root.add(Group(name, 'Model'))
    ox, oz = origin
    g = Prop('Game')
    g.box((2, .2, 2), (ox, SURF, oz), '#ffffff', name='Origin', tr=1, collide=False, shadow=False)
    g.box((2 * AX + 2, 14, .6), (ox, SURF + 7, oz), '#ffffff', name='NetWall', tr=1, collide=False, shadow=False)
    for nm, (px, pz), col in zip(('PadBot', 'Pad1', 'Pad2'), pads, ('#ffd233', '#4696ff', '#ff7846')):
        g.box((9, .6, 9), (px, .3, pz), col, name=nm, mat='neon')
    g.box((4, .2, 4), (exit_at[0], .6, exit_at[1]), '#ffffff', name='Exit', tr=1, collide=False, shadow=False)
    for (x, y, z, w, h, yaw) in boards:
        g.box((w, h, .4), (x, y, z), '#0a1228', name='Scoreboard', yaw=yaw, mat='smooth', collide=False)
    M.place(smooth(g), cf(), cls=None)


def build():
    root = Group(NAME, 'Model')
    world = root.add(Group('World', 'Folder'))
    fallback = world.add(Group('Fallback', 'Folder'))
    courts = root.add(Group('Courts', 'Folder'))

    F = Prop('Fallback')
    F.span(-460, 460, -2, -.1, -320, 540, '#5c9a4c', name='FallbackGround')
    F.span(-100, 100, -.5, .02, 114, 330, '#c9c2b4', name='FallbackPlaza')
    F.span(-9, 9, -.5, .02, AZ, 114, '#9da1a6', name='FallbackTunnel')
    fallback.place(smooth(F), cf(), cls=None)
    for (ox, oz) in ((0, 0), (-140, 230), (140, 230)):
        fallback.place(fallback_court(ox, oz), cf(), cls=None)

    g = Prop('Spawn')
    g.box((12, .2, 12), (0, .3, 200), '#ffffff', shape='spawn', name='SpawnLocation', mat='smooth', studs=False, tr=1,
          collide=False)
    # the entrance sign face on the Blender gate (the place builder writes CENTER COURT on it)
    g.box((30, 3.6, .2), (0, PLAZA_Y + 22, 121.35), '#0f1a38', name='Sign', yaw=180, mat='smooth')
    world.place(g, cf(), cls=None)

    court(courts, 'Center Court', (0, 0), pads=((0, 136), (-15, 136), (15, 136)), exit_at=(0, 150),
          boards=((0, 33.7, -85.55, 40, 17, 180), (0, 33.7, 85.55, 40, 17, 0)))
    for name, sx in (('Court 2', -1), ('Court 3', 1)):
        ox, oz = sx * 140, 230
        court(courts, name, (ox, oz), pads=((sx * 88, oz), (sx * 88, oz - 16), (sx * 88, oz + 16)),
              exit_at=(sx * 80, oz), boards=((ox, 11.0, oz - 62.55, 19.4, 8.4, 180),))

    views = [dict(name='plan', pos=[0, 900, 120.01], target=[0, 0, 120], fov=45)]
    return root, views, dict(center=[0, 0, 100], radius=360)
