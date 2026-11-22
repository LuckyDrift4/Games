"""R6 tennis animation clips: the single source of truth (made and previewed in Blender, played in Roblox).

Poses are written like posing with IK controls (see rig.py). Character space (x, y, f): x = right, y = up (0 = middle
of the torso, the floor is y = -3, shoulders ~0.5, head ~1.5), f = forward toward the net.

  root  lean (deg forward), tilt (deg, right shoulder down), turn (deg to the LEFT), x / f shift, y = extra height
        (the hips drop automatically so planted feet reach the floor - rigid R6 legs squat by spreading)
  rf/lf foot target (x, f, lift, toe-out deg)
  rh    right hand (x, y, f) - it holds the racket
  lh    left hand (x, y, f), or ('racket', s) = on the racket s studs up from the right hand
  rk    racket (pointing direction, string-face direction), both (x, y, f)
  look  the point the eyes look at

Keys: (time, pose, options). Between keys every number moves on a smooth curve through the keys;
hold=True eases into and out of that key (a held pose), linear=True goes straight to the next key.
"""

import copy


def pose(base=None, **ch):
    p = copy.deepcopy(base) if base else {}
    for k, v in ch.items():
        if k == 'root' and 'root' in p:
            r = dict(p['root'])
            r.update(v)
            p['root'] = r
        else:
            p[k] = v
    return p


def k(t, p, **opts):
    return (t, p, opts)


FAR = 40   # "far away toward the net"

READY = pose(
    root=dict(lean=16, turn=0),
    rf=(1.45, 0.3, 0, 14), lf=(-1.5, 0.6, 0, 14),
    rh=(0.1, -0.8, 1.15),
    lh=('racket', 0.75),
    rk=((-0.3, 0.75, 1.0), (1, 0, 0.1)),
    look=(0, 1.2, FAR),
)

CLIPS = {}

# ---------------------------------------------------------------- locomotion (loops)
CLIPS['Idle'] = dict(loop=True, priority='Idle', length=1.2, keys=[
    k(0.0, READY),
    k(0.6, pose(READY, root=dict(lean=18, y=-0.08), rh=(0.12, -0.9, 1.12), rk=((-0.24, 0.66, 1.0), (1, 0, 0.12)),
                look=(0.5, 1.0, FAR))),
    k(1.2, READY),
])


def run_key(side, phase):
    """side = +1 right leg forward, -1 left leg forward; phase 0 = contact, 1 = passing (high)"""
    s = side
    if phase == 0:
        return pose(root=dict(lean=20, turn=-9 * s, y=0.05),
                    rf=(0.55, 1.25 * s, 0.25 if s < 0 else 0, 4), lf=(-0.55, -1.25 * s, 0.25 if s > 0 else 0, 4),
                    rh=(1.35, -0.75, 1.05) if s < 0 else (1.45, -0.95, -0.75),
                    lh=(-1.35, -0.75, 1.15) if s > 0 else (-1.45, -0.95, -0.75),
                    rk=((0.1, 0.75, 1.0), (1, 0, 0)) if s < 0 else ((0.15, 0.95, 0.55), (1, 0, 0)),
                    look=(0, 1.0, FAR))
    return pose(root=dict(lean=20, turn=0, y=0.32, auto=False),
                rf=(0.55, 0.15 * s, 0.3), lf=(-0.55, -0.15 * s, 0.3),
                rh=(1.35, -1.15, 0.25), lh=(-1.35, -1.15, 0.25),
                rk=((0.12, 0.85, 0.8), (1, 0, 0)), look=(0, 1.0, FAR))


CLIPS['Run'] = dict(loop=True, priority='Movement', length=0.52, keys=[
    k(0.00, run_key(1, 0)), k(0.13, run_key(1, 1)), k(0.26, run_key(-1, 0)), k(0.39, run_key(-1, 1)),
    k(0.52, run_key(1, 0)),
])

_sh_open = pose(READY, root=dict(lean=18, y=-0.05), rf=(2.35, 0.4, 0, 16), lf=(-2.4, 0.6, 0, 16))
_sh_close = pose(READY, root=dict(lean=16, y=0.18), rf=(1.0, 0.4, 0.2, 8), lf=(-1.1, 0.6, 0.2, 8),
                 rh=(0.6, -0.7, 1.35))
CLIPS['Shuffle'] = dict(loop=True, priority='Movement', length=0.40, keys=[
    k(0.0, _sh_open), k(0.2, _sh_close), k(0.4, _sh_open),
])

# ---------------------------------------------------------------- strokes (contact = when the racket meets the ball)
# Forehand: open stance, unit turn with the left arm pointing at the ball, racket drop ("pat the dog"), low-to-high
# swing with the racket lagging, contact out in front, windshield-wiper finish over the left shoulder.
FH_LOAD = pose(root=dict(lean=12, turn=-45, x=0.2, y=-0.05),
               rf=(1.7, -0.35, 0, 40), lf=(-1.35, 0.65, 0, 18),
               rh=(2.0, 0.45, -0.45), lh=(0.75, 0.4, 1.35),
               rk=((0.2, 1.0, -0.3), (-0.5, 0, 1)), look=(5, 0.5, 14))
CLIPS['Forehand'] = dict(loop=False, priority='Action', length=1.0, contact=0.30, keys=[
    k(0.00, READY),
    k(0.10, FH_LOAD),
    k(0.20, pose(FH_LOAD, root=dict(turn=-50, y=-0.15), rh=(2.05, -0.6, -0.8), lh=(0.65, 0.05, 1.25),
                 rk=((-0.05, -0.55, -1.0), (0.1, -1, 0.3)), look=(4.5, 0.2, 10))),
    k(0.27, pose(FH_LOAD, root=dict(lean=15, turn=-16, x=0.1, y=-0.12), rh=(2.2, -1.1, 0.35),
                 lh=(-0.4, -0.25, 1.25), rk=((-0.05, -0.45, -1.0), (0.35, -0.35, 1)), look=(3.5, -0.3, 6))),
    k(0.30, pose(FH_LOAD, root=dict(lean=16, turn=8, x=0, y=-0.1), rh=(1.95, -0.8, 1.5),
                 lh=(-1.15, -0.4, 1.0), rk=((1.0, 0.15, 0.35), (-0.1, 0.05, 1)), look=(3.6, -0.5, 3))),
    k(0.37, pose(FH_LOAD, root=dict(lean=16, turn=36, x=-0.1, y=-0.06), rf=(1.5, 0.2, 0, 25), lf=(-1.25, 0.3, 0, 25),
                 rh=(0.65, 0.6, 1.6),
                 lh=(-1.6, -0.5, 0.25), rk=((-0.55, 0.65, -0.45), (-1, 0, -0.2)), look=(1, 0.5, 12))),
    k(0.46, pose(FH_LOAD, root=dict(lean=12, turn=48, x=-0.15, y=0), rf=(1.25, 1.05, 0.35, 0), lf=(-1.15, 0.1, 0, 30),
                 rh=(-1.0, 1.1, 0.7), lh=(-1.4, -0.4, 1.0),
                 rk=((-0.2, -0.3, -1.0), (-0.45, 0.2, -1)), look=(0, 0.8, FAR)), hold=True),
    k(0.62, pose(FH_LOAD, root=dict(lean=12, turn=44, x=-0.12, y=0), rf=(1.3, 0.95, 0, 6), lf=(-1.15, 0.1, 0, 30),
                 rh=(-0.9, 1.0, 0.8), lh=(-1.35, -0.45, 0.95),
                 rk=((-0.2, -0.35, -1.0), (-0.5, 0.2, -1)), look=(0, 1.0, FAR))),
    k(1.00, READY),
])

# Two-handed backhand: both hands stay on the handle (left hand just above the right).
BH_GRIP = ('racket', 0.42)
BH_LOAD = pose(root=dict(lean=14, turn=72, x=-0.15, y=-0.05),
               rf=(1.6, 0.85, 0, 20), lf=(-2.2, -0.3, 0, 45),
               rh=(-0.75, -0.15, 0.2), lh=BH_GRIP,
               rk=((-0.25, 1.0, -0.45), (0.4, 0, 1)), look=(-5, 0.5, 14))
CLIPS['Backhand'] = dict(loop=False, priority='Action', length=1.0, contact=0.30, keys=[
    k(0.00, pose(READY, lh=BH_GRIP)),
    k(0.10, BH_LOAD),
    k(0.20, pose(BH_LOAD, root=dict(turn=80, y=-0.2), rh=(-0.95, -0.85, -0.2),
                 rk=((0.15, -0.6, -1.0), (-0.1, -1, 0.3)), look=(-4.5, 0.2, 10))),
    k(0.27, pose(BH_LOAD, root=dict(lean=16, turn=42, x=-0.05, y=-0.15), rh=(-0.75, -1.25, 0.85),
                 rk=((-0.3, -0.6, -1.0), (-0.35, -0.35, 1)), look=(-3.5, -0.3, 6))),
    k(0.30, pose(BH_LOAD, root=dict(lean=18, turn=22, x=0, y=-0.12), rh=(-0.35, -1.05, 1.45),
                 rk=((-1.0, 0.12, 0.3), (0.1, 0.05, 1)), look=(-3.6, -0.6, 3))),
    k(0.38, pose(BH_LOAD, root=dict(lean=16, turn=-28, x=0.1, y=-0.08), rh=(0.6, 0.35, 1.55),
                 rk=((0.45, 0.8, -0.4), (1, 0, -0.2)), look=(-1, 0.5, 12))),
    k(0.48, pose(BH_LOAD, root=dict(lean=12, turn=-52, x=0.15, y=0), lf=(-1.4, 0.8, 0.3, 0),
                 rh=(1.05, 1.15, 0.6), rk=((0.3, -0.2, -1.0), (0.4, 0.2, -1)), look=(0, 0.8, FAR)), hold=True),
    k(0.64, pose(BH_LOAD, root=dict(lean=12, turn=-46, x=0.12, y=0), lf=(-1.55, 0.7, 0, 6),
                 rh=(0.95, 1.05, 0.7), rk=((0.25, -0.3, -1.0), (0.45, 0.2, -1)), look=(0, 1.0, FAR))),
    k(1.00, pose(READY, lh=BH_GRIP)),
])

# Serve: sideways stance, toss arm straight up, trophy position, racket drop behind the back, jump up into the ball
# and land inside the court with the racket finishing on the left side.
SV_STANCE = pose(root=dict(lean=4, turn=-76),
                 rf=(0.75, -1.25, 0, 75), lf=(-0.35, 1.15, 0, 35),
                 rh=(-0.1, -0.65, 0.85), lh=('racket', 1.05),
                 rk=((0.05, 0.25, 1.0), (1, 0, 0)), look=(3, 1.5, FAR))
SV_UP = pose(SV_STANCE, lh=(-0.45, 3.7, 1.05))
CLIPS['Serve'] = dict(loop=False, priority='Action', length=1.5, contact=0.86, toss=0.30, keys=[
    k(0.00, SV_STANCE, hold=True),
    k(0.15, pose(SV_STANCE, root=dict(lean=0, y=-0.08), rh=(0.2, -1.05, 0.55), lh=('racket', 1.05),
                 rk=((0.15, -0.35, 1.0), (1, 0, 0)))),
    k(0.30, pose(SV_UP, root=dict(lean=-6, tilt=4, y=-0.15), rh=(1.25, -0.6, -1.25),
                 rk=((0.35, 0.45, -1.0), (1, 0, 0)), look=(0.2, 6, 2))),
    k(0.55, pose(SV_UP, root=dict(lean=-16, tilt=12, turn=-80, y=-0.35), rh=(1.65, 1.25, -0.75),
                 rk=((0.2, 1.0, -0.3), (1, 0, 0)), lh=(-0.5, 3.8, 1.2), look=(0.4, 6, 1.6)), hold=True),
    k(0.74, pose(SV_UP, root=dict(lean=-10, tilt=6, turn=-58, y=-0.1), rh=(1.35, 2.05, -0.55),
                 rk=((0.15, -1.0, -0.45), (-1, 0, 0)), lh=(-0.55, 2.4, 1.3), look=(0.5, 6, 1.6))),
    k(0.86, pose(SV_UP, root=dict(lean=8, tilt=0, turn=-6, y=0.05),
                 rf=(0.8, -0.55, 0.55, 40), lf=(-0.25, 0.95, 0.75, 20),
                 rh=(0.85, 2.45, 0.85), rk=((0.0, 1.0, 0.38), (0, -0.3, 1)), lh=(-0.85, -0.55, 0.9),
                 look=(0.6, 4.5, 2.4))),
    k(0.98, pose(SV_UP, root=dict(lean=24, tilt=-4, turn=26, y=0),
                 rf=(1.05, -1.0, 0.75, 20), lf=(-1.0, 0.35, 0, 10),
                 rh=(0.95, -0.45, 1.65), rk=((-0.45, -0.6, 1.0), (1, 0, 0.2)), lh=(-1.5, -0.55, 0.55),
                 look=(0, 0.5, FAR))),
    k(1.12, pose(SV_UP, root=dict(lean=18, tilt=-2, turn=40, y=0),
                 rf=(0.95, 0.45, 0.2, 10), lf=(-1.0, 0.2, 0, 10),
                 rh=(-1.0, -1.0, 0.8), rk=((-0.6, -0.5, -0.65), (0.3, 0, -1)), lh=(-1.5, -0.65, 0.3),
                 look=(0, 0.8, FAR)), hold=True),
    k(1.50, READY),
])

# Volleys: short punch, racket head above the wrist, step across with the opposite foot.
CLIPS['VolleyForehand'] = dict(loop=False, priority='Action', length=0.62, contact=0.16, keys=[
    k(0.00, READY),
    k(0.07, pose(READY, root=dict(lean=16, turn=-32, x=0.1), rf=(2.0, 0.1, 0, 30), lf=(-1.15, 1.2, 0.35, 15),
                 rh=(1.9, 0.15, 0.55), lh=(0.75, 0.15, 1.55), rk=((0.4, 1.0, -0.2), (-0.35, 0, 1)),
                 look=(3, 0.8, 10))),
    k(0.16, pose(READY, root=dict(lean=22, turn=-18, x=0.05, f=0.1), rf=(2.0, 0.1, 0, 30), lf=(-1.0, 1.75, 0, 15),
                 rh=(2.0, -0.2, 1.75), lh=(-0.45, 0.0, 1.35), rk=((0.7, 0.72, 0.3), (-0.1, 0.25, 1)),
                 look=(3.4, 0.6, 3.5))),
    k(0.28, pose(READY, root=dict(lean=22, turn=-14, x=0.05, f=0.1), rf=(2.0, 0.1, 0, 30), lf=(-1.0, 1.75, 0, 15),
                 rh=(1.75, -0.35, 1.95), lh=(-0.9, -0.2, 1.1), rk=((0.6, 0.65, 0.6), (-0.1, 0.3, 1)),
                 look=(2, 0.6, 10)), hold=True),
    k(0.62, READY),
])

CLIPS['VolleyBackhand'] = dict(loop=False, priority='Action', length=0.62, contact=0.16, keys=[
    k(0.00, READY),
    k(0.07, pose(READY, root=dict(lean=16, turn=48, x=-0.1), rf=(1.15, 1.2, 0.35, 15), lf=(-2.0, 0.1, 0, 30),
                 rh=(-0.45, 0.15, 0.35), lh=('racket', 0.95), rk=((-0.45, 1.0, -0.2), (0.35, 0, 1)),
                 look=(-3, 0.8, 10))),
    k(0.16, pose(READY, root=dict(lean=22, turn=26, x=-0.05, f=0.1), rf=(1.0, 1.75, 0, 15), lf=(-2.0, 0.1, 0, 30),
                 rh=(-0.85, -0.3, 1.55), lh=(-1.85, -0.1, -0.35), rk=((-0.72, 0.7, 0.3), (0.1, 0.25, 1)),
                 look=(-3.4, 0.6, 3.5))),
    k(0.28, pose(READY, root=dict(lean=22, turn=20, x=-0.05, f=0.1), rf=(1.0, 1.75, 0, 15), lf=(-2.0, 0.1, 0, 30),
                 rh=(-0.75, -0.4, 1.75), lh=(-1.9, -0.2, -0.45), rk=((-0.6, 0.65, 0.6), (0.1, 0.3, 1)),
                 look=(-2, 0.6, 10)), hold=True),
    k(0.62, READY),
])

# Smash: turn sideways, point at the ball, racket up behind the head, jump with a scissor kick and hit down.
SM_SIDE = pose(root=dict(lean=-12, turn=-70, y=-0.1),
               rf=(0.95, -1.2, 0, 60), lf=(-0.3, 1.1, 0, 30),
               rh=(1.6, 1.35, -0.55), lh=(-0.45, 3.5, 1.45),
               rk=((0.2, 1.0, -0.4), (1, 0, 0)), look=(0.5, 6, 2.5))
CLIPS['Smash'] = dict(loop=False, priority='Action', length=1.0, contact=0.45, keys=[
    k(0.00, READY),
    k(0.18, SM_SIDE),
    k(0.33, pose(SM_SIDE, root=dict(lean=-8, turn=-56, y=-0.35), rh=(1.25, 2.1, -0.5),
                 rk=((0.12, -1.0, -0.45), (-1, 0, 0)), lh=(-0.5, 3.0, 1.5), look=(0.5, 5.5, 2.2))),
    k(0.45, pose(SM_SIDE, root=dict(lean=12, turn=4, y=0.1), rf=(1.1, 0.85, 1.0, 10), lf=(-0.5, -0.95, 0.8, 10),
                 rh=(0.8, 2.4, 1.05), rk=((0.0, 1.0, 0.5), (0, -0.4, 1)), lh=(-0.95, -0.4, 1.0),
                 look=(0.6, 3.5, 3))),
    k(0.58, pose(SM_SIDE, root=dict(lean=30, turn=36, y=0), rf=(1.0, 1.25, 0, 10), lf=(-0.75, -0.85, 0.45, 10),
                 rh=(-0.5, -0.85, 1.35), rk=((-0.5, -0.65, 0.6), (0.3, 0, -1)), lh=(-1.55, -0.4, 0.4),
                 look=(0, 0, FAR))),
    k(0.72, pose(SM_SIDE, root=dict(lean=24, turn=34, y=0), rf=(1.15, 1.1, 0, 10), lf=(-1.0, -0.55, 0, 10),
                 rh=(-0.7, -0.95, 1.1), rk=((-0.55, -0.6, 0.5), (0.3, 0, -1)), lh=(-1.5, -0.5, 0.35),
                 look=(0, 0.8, FAR)), hold=True),
    k(1.00, READY),
])

# ---------------------------------------------------------------- reactions
STAND = pose(root=dict(lean=2), rf=(0.7, 0.1, 0, 8), lf=(-0.7, 0.15, 0, 8),
             rh=(1.55, -1.2, 0.3), lh=(-1.5, -1.2, 0.1), rk=((0.15, -0.35, 1.0), (1, 0, 0)), look=(0, 1.5, FAR))
CROUCH = pose(READY, root=dict(lean=22, y=-0.1), rf=(2.1, 0.3, 0, 16), lf=(-2.1, 0.5, 0, 16),
              rh=(1.15, -1.25, 0.75), lh=(-1.15, -1.25, 0.75), rk=((0.3, -0.25, 1.0), (1, 0, 0)), look=(0, 0, 12))
UP = pose(root=dict(lean=-10, y=0), rf=(0.75, 0.15, 1.5, 8), lf=(-0.75, 0.05, 1.3, 8),
          rh=(1.5, 3.5, 0.2), lh=(-1.6, 3.2, 0.35), rk=((0.12, 1.0, 0.08), (0, 0, 1)), look=(0, 4, 10))
PUMP_DOWN = pose(READY, root=dict(lean=26, y=-0.1), rf=(2.15, 0.3, 0, 16), lf=(-2.15, 0.6, 0, 16),
                 rh=(1.6, 0.4, 0.5), rk=((0.25, 1.0, 0.1), (0, 0, 1)), lh=(-1.0, -0.55, 0.75), look=(0, -1, 7))
PUMP_UP = pose(PUMP_DOWN, root=dict(lean=18), lh=(-1.35, 1.1, 1.05), look=(0, 0.5, 8))
CLIPS['Celebrate'] = dict(loop=False, priority='Action', length=1.6, keys=[
    k(0.00, READY),
    k(0.12, CROUCH),
    k(0.32, UP, hold=True),
    k(0.52, pose(CROUCH, rh=(1.5, 1.6, 0.4), lh=(-1.5, 1.4, 0.4), rk=((0.2, 1.0, 0.1), (0, 0, 1)), look=(0, 1, 10))),
    k(0.72, PUMP_DOWN),
    k(0.86, PUMP_UP),
    k(1.00, PUMP_DOWN, hold=True),
    k(1.22, pose(PUMP_DOWN, root=dict(lean=20), look=(0, 0.5, 10))),
    k(1.60, STAND),
])

SLUMP = pose(STAND, root=dict(lean=28, y=-0.05), rf=(0.8, 0.2, 0, 10), lf=(-0.8, 0.25, 0, 10),
             rh=(1.35, -1.6, 0.35), rk=((0.1, -1.0, 0.3), (1, 0, 0)), lh=(-0.25, 1.45, 1.35), look=(0, -3, 3))
CLIPS['Upset'] = dict(loop=False, priority='Action', length=1.8, keys=[
    k(0.00, READY),
    k(0.35, SLUMP),
    k(0.70, pose(SLUMP, look=(-2.2, -3, 3))),
    k(0.95, pose(SLUMP, look=(2.2, -3, 3))),
    k(1.20, pose(SLUMP, root=dict(lean=20), lh=(-1.3, -1.4, 0.35), look=(0, -2, 4)), hold=True),
    k(1.80, STAND),
])

ORDER = ['Idle', 'Run', 'Shuffle', 'Forehand', 'Backhand', 'Serve', 'VolleyForehand', 'VolleyBackhand', 'Smash',
         'Celebrate', 'Upset']
