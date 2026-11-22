"""R6 tennis animation clips: the single source of truth.

Each pose sets joint rotations in degrees (rx, ry, rz) plus an optional offset (px, py, pz), in the joint's own frame,
exactly as Roblox applies Motor6D.Transform:  Part1 = Part0 * C0 * Transform * C1:Inverse(),
Transform = CFrame.new(px, py, pz) * CFrame.Angles(rx, ry, rz).

Joint axes (worked out from the R6 C0 matrices):
  Root (HumanoidRootPart -> Torso)  rx + = lean forward, ry + = tilt to the right, rz + = turn left
                                     px + = shift left, py + = shift back, pz + = up
  Neck                               rx + = look down, rz + = turn head left
  RS / RH (right shoulder / hip)     rz + = swing forward, rx - = out to the side, rx + = across the body
  LS / LH (left shoulder / hip)      rz - = swing forward, rx - = out to the side, rx + = across the body
  ry on a limb twists it about its own length (used to turn the racket face).

The racket is welded to the right hand and points along the arm (see RACKET_GRIP in r6.py), so the racket face looks
where the arm swings. Ease = how the motion goes from that keyframe to the next one.
"""

LEAN = 14


def W(direction, face):
    """racket pose in CHARACTER space (X right, Y up, -Z toward the net): where the head points, where the face looks"""
    return ('char', direction, face)


def ready(**over):
    """balanced ready stance: low, leaning in, racket in front held with both hands, feet wide"""
    p = {
        'Root': (LEAN, 0, 0, 0, 0, -0.10),
        'Neck': (-LEAN + 2, 0, 0),
        'RS': (20, -10, 52),
        'LS': (24, 10, -50),
        'RH': (-16, 0, LEAN),
        'LH': (-16, 0, -LEAN),
        'W': W((-0.15, 0.55, -1), (1, 0, 0)),
    }
    p.update(over)
    return p


def legs(lean, right_fwd, left_fwd, spread=-16):
    """leg angles that keep the feet under the body for a given torso lean (+fwd = step forward)"""
    return {'RH': (spread, 0, lean + right_fwd), 'LH': (spread, 0, -(lean + left_fwd))}


def k(t, pose, ease='inout'):
    return {'t': t, 'pose': pose, 'ease': ease}


CLIPS = {}

# ---------------------------------------------------------------- locomotion (loops)
CLIPS['Idle'] = dict(loop=True, priority='Idle', length=1.0, keys=[
    k(0.0, ready()),
    k(0.5, ready(Root=(LEAN + 3, 0, 0, 0, 0, -0.22), RS=(20, -10, 56), LS=(24, 10, -54), **legs(LEAN + 3, 0, 0, -18))),
    k(1.0, ready()),
])

_run = []
for i, (rf, lf, bob, rs, ls, twist) in enumerate((
        (42, -38, -0.16, 22, 28, 8),
        (5, -5, 0.10, 34, -10, 0),
        (-38, 42, -0.16, 48, -45, -8),
        (-5, 5, 0.10, 34, -10, 0),
        (42, -38, -0.16, 22, 28, 8))):
    p = {'Root': (16, 0, twist, 0, 0, bob), 'Neck': (-14, 0, -twist), 'RS': (18, -10, rs), 'LS': (12, 0, ls),
         'W': W((-0.2, 0.7, -1), (1, 0, 0))}
    p.update(legs(16, rf, lf, -6))
    _run.append(k(i * 0.14, p, 'inout'))
CLIPS['Run'] = dict(loop=True, priority='Movement', length=0.56, keys=_run)

CLIPS['Shuffle'] = dict(loop=True, priority='Movement', length=0.40, keys=[
    k(0.0, ready(Root=(LEAN, 0, 0, 0, 0, -0.18), **legs(LEAN, 0, 0, -30))),
    k(0.2, ready(Root=(LEAN, 0, 0, 0, 0, 0.02), **legs(LEAN, 0, 0, -6))),
    k(0.4, ready(Root=(LEAN, 0, 0, 0, 0, -0.18), **legs(LEAN, 0, 0, -30))),
])

# ---------------------------------------------------------------- strokes (contact = when the racket meets the ball)
CLIPS['Forehand'] = dict(loop=False, priority='Action', length=0.95, contact=0.30, keys=[
    k(0.00, ready()),
    k(0.16, {'Root': (12, 0, -72, 0, 0.30, -0.16), 'Neck': (-6, 0, 58), 'RS': (-78, 0, -28), 'LS': (38, 0, -88),
             'W': W((0.3, 0.6, 1), (1, 0, 0)), **legs(12, -8, 14, -18)}, 'in'),
    k(0.30, {'Root': (17, 0, 6, 0, -0.06, -0.12), 'Neck': (-12, 0, -4), 'RS': (-72, 0, 62), 'LS': (22, 0, -30),
             'W': W((1, 0.05, -0.25), (0, 0, -1)), **legs(17, -4, 20, -18)}, 'out'),
    k(0.45, {'Root': (19, 0, 68, 0, -0.10, -0.08), 'Neck': (-10, 0, -50), 'RS': (34, 0, 142), 'LS': (-8, 0, 12),
             'W': W((-0.6, 0.3, 1), (-1, 0, 0)), **legs(19, -18, 18, -14)}, 'inout'),
    k(0.95, ready()),
])

CLIPS['Backhand'] = dict(loop=False, priority='Action', length=0.95, contact=0.30, keys=[
    k(0.00, ready()),
    k(0.16, {'Root': (12, 0, 78, 0, 0.28, -0.16), 'Neck': (-6, 0, -60), 'RS': (58, 0, -14), 'LS': (-52, 0, 18),
             'W': W((-0.3, 0.6, 1), (-1, 0, 0)), **legs(12, 16, -6, -18)}, 'in'),
    k(0.30, {'Root': (17, 0, -6, 0, -0.06, -0.12), 'Neck': (-12, 0, 4), 'RS': (60, 0, 58), 'LS': (-36, 0, -60),
             'W': W((-1, 0.05, -0.25), (0, 0, -1)), **legs(17, 20, -4, -18)}, 'out'),
    k(0.45, {'Root': (18, 0, -70, 0, -0.10, -0.08), 'Neck': (-10, 0, 46), 'RS': (-14, 0, 150), 'LS': (6, 0, -150),
             'W': W((0.6, 0.3, 1), (1, 0, 0)), **legs(18, 18, -16, -14)}, 'inout'),
    k(0.95, ready()),
])

CLIPS['Serve'] = dict(loop=False, priority='Action', length=1.45, contact=0.86, toss=0.30, keys=[
    k(0.00, {'Root': (5, 0, -70, 0, 0, 0), 'Neck': (-4, 0, 62), 'RS': (16, 0, 32), 'LS': (22, 0, -34),
             'W': W((-0.3, 0.3, -1), (0, 1, 0)), **legs(5, -6, 10, -12)}),
    k(0.30, {'Root': (-6, 0, -74, 0, 0.10, -0.20), 'Neck': (-28, 0, 60), 'RS': (-62, 0, -36), 'LS': (-8, 0, -172),
             'W': W((0.3, -0.6, 1), (1, 0, 0)), **legs(-6, -6, 10, -14)}),
    k(0.62, {'Root': (-18, 0, -64, 0, 0.12, -0.34), 'Neck': (-38, 0, 52), 'RS': (-48, 70, 150), 'LS': (-4, 0, -166),
             'W': W((0.2, 1, 0.6), (1, 0, 0)), **legs(-18, -4, 8, -16)}, 'in'),
    k(0.86, {'Root': (12, 0, 4, 0, -0.20, 0.45), 'Neck': (-22, 0, 0), 'RS': (6, 180, 178), 'LS': (10, 0, -22),
             'W': W((0.1, 1, -0.25), (0, 0.2, -1)), **legs(12, -30, 4, -6)}, 'out'),
    k(1.06, {'Root': (28, 0, 36, 0, -0.30, 0.10), 'Neck': (-6, 0, -22), 'RS': (56, 90, 40), 'LS': (14, 0, 12),
             'W': W((-0.5, -0.8, -0.2), (0, 0, -1)), **legs(28, -46, 14, -10)}, 'inout'),
    k(1.45, ready()),
])

CLIPS['VolleyForehand'] = dict(loop=False, priority='Action', length=0.60, contact=0.16, keys=[
    k(0.00, ready()),
    k(0.08, {'Root': (15, 0, -32, 0, 0.05, -0.20), 'Neck': (-12, 0, 30), 'RS': (-62, -90, 48), 'LS': (26, 0, -60),
             'W': W((0.5, 0.9, -0.3), (0.3, 0, -1)), **legs(15, 0, 10, -20)}, 'in'),
    k(0.16, {'Root': (17, 0, -10, 0, -0.15, -0.20), 'Neck': (-14, 0, 8), 'RS': (-56, -90, 76), 'LS': (20, 0, -44),
             'W': W((0.35, 0.9, -0.5), (0, 0, -1)), **legs(17, -4, 26, -20)}, 'out'),
    k(0.32, {'Root': (16, 0, -6, 0, -0.12, -0.18), 'Neck': (-14, 0, 6), 'RS': (-52, -90, 80), 'LS': (20, 0, -40),
             **legs(16, -4, 24, -20)}),
    k(0.60, ready()),
])

CLIPS['VolleyBackhand'] = dict(loop=False, priority='Action', length=0.60, contact=0.16, keys=[
    k(0.00, ready()),
    k(0.08, {'Root': (15, 0, 36, 0, 0.05, -0.20), 'Neck': (-12, 0, -32), 'RS': (62, 90, 44), 'LS': (-20, 0, -30),
             'W': W((-0.5, 0.9, -0.3), (-0.3, 0, -1)), **legs(15, 10, 0, -20)}, 'in'),
    k(0.16, {'Root': (17, 0, 12, 0, -0.15, -0.20), 'Neck': (-14, 0, -10), 'RS': (56, 90, 74), 'LS': (-34, 0, -10),
             'W': W((-0.4, 0.9, -0.5), (0, 0, -1)), **legs(17, 26, -4, -20)}, 'out'),
    k(0.32, {'Root': (16, 0, 8, 0, -0.12, -0.18), 'Neck': (-14, 0, -8), 'RS': (52, 90, 78), 'LS': (-34, 0, -8),
             **legs(16, 24, -4, -20)}),
    k(0.60, ready()),
])

CLIPS['Smash'] = dict(loop=False, priority='Action', length=1.0, contact=0.45, keys=[
    k(0.00, ready()),
    k(0.20, {'Root': (-12, 0, -66, 0, 0.15, -0.26), 'Neck': (-40, 0, 56), 'RS': (-46, 70, 150), 'LS': (-6, 0, -160),
             'W': W((0.2, 1, 0.6), (1, 0, 0)), **legs(-12, -6, 10, -16)}, 'in'),
    k(0.45, {'Root': (15, 0, 0, 0, -0.10, 0.36), 'Neck': (-26, 0, 0), 'RS': (5, 180, 176), 'LS': (10, 0, -26),
             'W': W((0.05, 1, -0.3), (0, 0.2, -1)), **legs(15, -20, 6, -8)}, 'out'),
    k(0.62, {'Root': (30, 0, 36, 0, -0.20, 0.0), 'Neck': (-4, 0, -16), 'RS': (60, 90, 36), 'LS': (14, 0, 14),
             'W': W((-0.5, -0.8, -0.2), (0, 0, -1)), **legs(30, -30, 10, -12)}, 'inout'),
    k(1.00, ready()),
])

# ---------------------------------------------------------------- reactions
_stand = {'Root': (0, 0, 0, 0, 0, 0), 'Neck': (0, 0, 0), 'RS': (8, 0, 18), 'LS': (6, 0, -8),
          'W': W((0.1, -0.4, -1), (1, 0, 0)), **legs(0, 0, 0, -6)}
CLIPS['Celebrate'] = dict(loop=False, priority='Action', length=1.6, keys=[
    k(0.00, ready()),
    k(0.22, {'Root': (-6, 0, 0, 0, 0, 0.65), 'Neck': (-20, 0, 0), 'RS': (-12, 0, 172), 'LS': (-40, 0, -120),
             'W': W((0, 1, 0.1), (0, 0, -1)), **legs(-6, 10, -10, -10)}, 'in'),
    k(0.48, {'Root': (10, 0, 0, 0, 0, -0.22), 'Neck': (-6, 0, 0), 'RS': (6, 0, 110), 'LS': (10, 0, -40),
             'W': W((0.2, 0.8, -0.5), (1, 0, 0)), **legs(10, 0, 0, -18)}, 'out'),
    k(0.72, {'Root': (-6, 0, 0, 0, 0, 0.65), 'Neck': (-20, 0, 0), 'RS': (-12, 0, 172), 'LS': (-40, 0, -120),
             'W': W((0, 1, 0.1), (0, 0, -1)), **legs(-6, -10, 10, -10)}, 'in'),
    k(1.00, {'Root': (8, 0, 0, 0, 0, -0.18), 'Neck': (-6, 0, 0), 'RS': (6, 0, 110), 'LS': (10, 0, -40),
             'W': W((0.2, 0.8, -0.5), (1, 0, 0)), **legs(8, 0, 0, -16)}, 'out'),
    k(1.60, dict(_stand)),
])

CLIPS['Upset'] = dict(loop=False, priority='Action', length=1.8, keys=[
    k(0.00, ready()),
    k(0.45, {'Root': (28, 0, 0, 0, 0, -0.10), 'Neck': (34, 0, 0), 'RS': (2, 0, 10), 'LS': (38, -20, -150),
             'W': W((0.2, -1, -0.2), (1, 0, 0)), **legs(28, 0, 0, -10)}, 'inout'),
    k(1.30, {'Root': (30, 0, 6, 0, 0, -0.12), 'Neck': (38, 0, -6), 'RS': (2, 0, 8), 'LS': (40, -20, -150),
             **legs(30, 0, 0, -10)}, 'inout'),
    k(1.80, dict(_stand)),
])

ORDER = ['Idle', 'Run', 'Shuffle', 'Forehand', 'Backhand', 'Serve', 'VolleyForehand', 'VolleyBackhand', 'Smash',
         'Celebrate', 'Upset']
