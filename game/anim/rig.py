"""Pose solver for the R6 tennis animations: poses are written the way an animator thinks (where the feet stand,
where the hands go, where the racket points, what the eyes look at) and solved to the seven Motor6D transforms.

Character space = HumanoidRootPart space in Roblox studs, written here as (x, y, f): x = right, y = up (0 = the
middle of the torso, the floor is at y = -3), f = forward toward the net. Internally Roblox uses Z back, so f = -z.

Every R6 limb is one rigid block, so a limb is "aimed": the solver turns it about its shoulder / hip pivot until the
hand / foot points at the target (it reaches it when the target is about one limb length away), with `roll`
choosing which way the block's front faces. The racket ("RacketGrip" Motor6D on the Right Arm) is the wrist.

Clips are keys of these parameters on a timeline. Between keys every number follows a smooth time-aware cubic
(Hermite) curve, so motion flows through keys instead of stopping at each one; a key marked hold=True eases to a
stop. The result is baked at FPS and the Roblox runtime plays the baked frames, so preview == game.
"""
import math

import r6

FPS = 30
FLOOR = -3.0
LIMB = {   # joint: (end point in Part1 space, default roll hint in character (x, y, f))
    'RS': ((0, -1.15, 0), (0, 0, 1)),     # right hand grip point
    'LS': ((0, -1.0, 0), (0, 0, 1)),      # left hand
    'RH': ((0, -1.0, 0), (0, 0, 1)),      # right foot (bottom centre of the leg)
    'LH': ((0, -1.0, 0), (0, 0, 1)),
}


# ---------------------------------------------------------------- small vector helpers (3-tuples)
def C(v):
    """(x, y, f) -> Roblox character space (x, y, z)"""
    return (v[0], v[1], -v[2])


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scl(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def length(a):
    return math.sqrt(dot(a, a))


def unit(a):
    l = length(a)
    return tuple(x / l for x in a) if l > 1e-9 else (0.0, 1.0, 0.0)


def rot_apply(R, v):
    return tuple(sum(R[i][k] * v[k] for k in range(3)) for i in range(3))


def rot_t(R):
    return tuple(tuple(R[j][i] for j in range(3)) for i in range(3))


def rot_of(M):
    return tuple(tuple(M[i][j] for j in range(3)) for i in range(3))


def pos_of(M):
    return (M[0][3], M[1][3], M[2][3])


def axis_angle(axis, a):
    x, y, z = unit(axis)
    c, s = math.cos(a), math.sin(a)
    t = 1 - c
    return ((t * x * x + c, t * x * y - s * z, t * x * z + s * y),
            (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
            (t * x * z - s * y, t * y * z + s * x, t * z * z + c))


def rot_between(a, b):
    """smallest rotation taking direction a onto direction b"""
    a, b = unit(a), unit(b)
    c = r6.cross(a, b)
    s = length(c)
    d = max(-1.0, min(1.0, dot(a, b)))
    if s < 1e-9:
        if d > 0:
            return ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        perp = r6.cross(a, (1, 0, 0) if abs(a[0]) < .9 else (0, 1, 0))
        return axis_angle(perp, math.pi)
    return axis_angle(c, math.atan2(s, d))


def frame(yaxis, zhint):
    """rotation whose +Y is yaxis and whose +Z is zhint made perpendicular"""
    Y = unit(yaxis)
    Z = sub(zhint, scl(Y, dot(zhint, Y)))
    if length(Z) < 1e-6:
        Z = r6.cross((1, 0, 0), Y) if abs(Y[0]) < .9 else r6.cross((0, 0, 1), Y)
    Z = unit(Z)
    X = r6.cross(Y, Z)
    return tuple(tuple((X, Y, Z)[c][r] for c in range(3)) for r in range(3))


# ---------------------------------------------------------------- solving one pose
def root_transform(root):
    """root = dict(lean=deg forward, tilt=deg (right shoulder down), turn=deg to the left,
    x=shift right, y=up, f=forward) -> RootJoint Transform. Leaning bends at the hips (the hips stay where they
    are and the shoulders go forward), like a person does, not about the middle of the torso."""
    r = math.radians
    R = r6.angles(r(root.get('lean', 0)), r(root.get('tilt', 0)), r(root.get('turn', 0)))
    # RootJoint's joint frame: X = -x (left), Y = -z (forward), Z = y (up); the hips are at (0, 0, -1) in it
    h = (0, 0, -1)
    keep = sub(h, rot_apply(R, h))
    p = (-root.get('x', 0) + keep[0], -root.get('f', 0) + keep[1], root.get('y', 0) + keep[2])
    return r6.mat(R, p)


def limb_transform(joint, parent_world, target, roll):
    """aim a rigid limb (RS / LS / RH / LH) so its end points at `target` (Roblox char space), the block's front (-Z)
    toward `roll`. Returns (Transform, Part1 world)."""
    p0, p1, C0, C1, _ = r6.JOINTS[joint]
    J = r6.mul(parent_world, C0)
    pivot = pos_of(J)
    end_local = LIMB[joint][0]
    c1p = pos_of(C1)
    u = sub(end_local, c1p)                      # pivot -> end, in limb space
    d = sub(target, pivot)
    if length(d) < 1e-6:
        d = (0, -1, 0)
    # start with limb -Y along d, front (-Z) toward roll, then correct for the pivot being off the limb's axis
    R = frame(scl(d, -1), scl(roll, -1))
    for _ in range(4):
        cur = rot_apply(R, u)
        Q = rot_between(cur, d)
        R = r6.m3(Q, R)
        # keep the front facing the roll hint around the limb axis
        ax = unit(rot_apply(R, u))
        front = rot_apply(R, (0, 0, -1))
        want = sub(roll, scl(ax, dot(roll, ax)))
        have = sub(front, scl(ax, dot(front, ax)))
        if length(want) > 1e-6 and length(have) > 1e-6:
            a = math.atan2(dot(r6.cross(unit(have), unit(want)), ax), dot(unit(have), unit(want)))
            R = r6.m3(axis_angle(ax, a), R)
    # Part1 world rotation R; Transform = J^-1 * Part1 * C1  (rotation only, the pivot stays put)
    T = r6.m3(r6.m3(rot_t(rot_of(J)), R), rot_of(C1))
    Tm = r6.mat(T)
    world = r6.mul(r6.mul(J, Tm), r6.inv(C1))
    return Tm, world


def neck_transform(torso_world, look):
    """turn the head so its face (-Z) looks at the point `look` (Roblox char space), staying upright"""
    _, _, C0, C1, _ = r6.JOINTS['Neck']
    J = r6.mul(torso_world, C0)
    head_center = pos_of(r6.mul(J, r6.inv(C1)))
    d = unit(sub(look, head_center))
    up = rot_apply(rot_of(torso_world), (0, 1, 0))
    Zb = scl(d, -1)                               # head +Z points away from where it looks
    X = unit(r6.cross(up, Zb))
    Y = r6.cross(Zb, X)
    R = tuple(tuple((X, Y, Zb)[c][r] for c in range(3)) for r in range(3))
    T = r6.m3(r6.m3(rot_t(rot_of(J)), R), rot_of(C1))
    return r6.mat(T)


def solve_pose(P):
    """P: a full pose dict (see clips.py). Returns {joint: Transform matrix} for r6.ORDER."""
    out = {}
    root_w = r6.mat(p=(0, 0, 0))
    root = dict(P['root'])
    out['Root'] = root_transform(root)
    torso = r6.mul(r6.mul(root_w, r6.JOINTS['Root'][2]), r6.mul(out['Root'], r6.inv(r6.JOINTS['Root'][3])))
    worlds = {}
    # legs: a rigid leg is turned toward the target's direction and lands exactly at the target's height
    for j, key in (('RH', 'rf'), ('LH', 'lf')):
        x, f, lift = P[key][:3]
        toe = P[key][3] if len(P[key]) > 3 else 0
        a = math.radians(toe)
        roll = C((math.sin(a) * (1 if j == 'RH' else -1), 0, math.cos(a)))
        out[j], _ = limb_transform(j, torso, foot_target(j, torso, x, f, lift), roll)
    # right arm, then the racket (wrist) in character space -> Right Arm space
    roll = C(P.get('rh_roll', (0, 0, 1)))
    out['RS'], worlds['RS'] = limb_transform('RS', torso, C(P['rh']), roll)
    d, f = P['rk']
    A = rot_of(worlds['RS'])
    out['W'] = r6.mat(r6.m3(rot_t(A), frame(C(d), C(f))))
    # left arm: a free target, pulled onto the racket handle by `grab` (0..1) at s studs up from the grip
    g, s = P.get('grab', (0, 0.6))
    tgt = C(P['lh'])
    if g > 1e-3:
        racket_w = r6.mul(r6.mul(worlds['RS'], r6.mat(p=r6.HAND)), out['W'])
        on = pos_of(r6.mul(racket_w, r6.mat(p=(0, grip_s(torso, racket_w, s), 0))))
        tgt = add(scl(tgt, 1 - g), scl(on, g))
    roll = C(P.get('lh_roll', (0, 0, 1)))
    out['LS'], worlds['LS'] = limb_transform('LS', torso, tgt, roll)
    out['Neck'] = neck_transform(torso, C(P['look']))
    return out


LEG = length(sub(LIMB['RH'][0], pos_of(r6.JOINTS['RH'][3])))
LARM = length(sub(LIMB['LS'][0], pos_of(r6.JOINTS['LS'][3])))


def foot_target(j, torso, x, f, lift):
    """the point the leg aims at. A planted foot (lift ~0) lands exactly on the floor in the target's direction from
    the hip (never sinking in or floating); a lifted foot aims straight at its target but never goes below the floor"""
    pivot = pos_of(r6.mul(torso, r6.JOINTS[j][2]))
    tgt = C((x, FLOOR + lift, f))

    def at_height(y):
        h = pivot[1] - y
        if 0 < h < LEG:
            dx, dz = tgt[0] - pivot[0], tgt[2] - pivot[2]
            d = math.hypot(dx, dz)
            r = math.sqrt(LEG * LEG - h * h)
            if d > 1e-3:
                return (pivot[0] + dx / d * r, y, pivot[2] + dz / d * r)
        return None
    if lift <= 0.05:
        return at_height(FLOOR) or tgt
    end = add(pivot, scl(unit(sub(tgt, pivot)), LEG))
    if end[1] < FLOOR + 0.03:
        return at_height(FLOOR + 0.03) or tgt
    return tgt


def grip_s(torso, racket_w, s0):
    """where along the handle the left hand can actually reach (rigid arm), near the preferred spot s0"""
    pivot = pos_of(r6.mul(torso, r6.JOINTS['LS'][2]))
    best, best_s = None, s0
    s = max(0.1, s0 - 0.5)
    while s <= s0 + 0.5:
        on = pos_of(r6.mul(racket_w, r6.mat(p=(0, s, 0))))
        cost = abs(length(sub(on, pivot)) - LARM) + 0.12 * abs(s - s0)
        if best is None or cost < best:
            best, best_s = cost, s
        s += 0.025
    return best_s


def auto_height(P, root):
    """lower (or raise) the hips so the planted feet reach the floor: the legs are rigid, so a wide stance squats.
    A foot further out than the leg can reach is pulled in (foot_target), never the hips down to the floor."""
    y = 0.0
    for _ in range(5):
        rr = dict(root, y=y)
        torso = r6.mul(r6.JOINTS['Root'][2], r6.mul(root_transform(rr), r6.inv(r6.JOINTS['Root'][3])))
        errs = []
        for j, key in (('RH', 'rf'), ('LH', 'lf')):
            x, f, lift = P[key][:3]
            if lift > 0.05 and any(P[k][2] <= 0.05 for k in ('rf', 'lf')):
                continue
            pivot = pos_of(r6.mul(torso, r6.JOINTS[j][2]))
            tgt = C((x, FLOOR + lift, f))
            horiz = min(math.hypot(tgt[0] - pivot[0], tgt[2] - pivot[2]), 0.62 * LEG)
            need = math.sqrt(LEG * LEG - horiz * horiz)       # how high the hip must be for the foot to land there
            errs.append((pivot[1] - (FLOOR + lift)) - need)
        if not errs:
            break
        y -= sum(errs) / len(errs)
    return y


# ---------------------------------------------------------------- clip interpolation and baking
def flatten(P):
    """pose dict -> flat list of numbers (for interpolation) and a rebuild function"""
    vals, spec = [], []

    def put(key, v):
        spec.append((key, len(v)))
        vals.extend(v)
    r = P['root']
    put('root', [r.get('lean', 0), r.get('tilt', 0), r.get('turn', 0), r.get('x', 0), r['y'], r.get('f', 0)])
    put('rf', list(P['rf']) + [0] * (4 - len(P['rf'])))
    put('lf', list(P['lf']) + [0] * (4 - len(P['lf'])))
    put('rh', list(P['rh']))
    put('lh', list(P['lh']))
    put('grab', list(P.get('grab', (0, 0.6))))
    put('rh_roll', list(P.get('rh_roll', (0, 0, 1))))
    put('lh_roll', list(P.get('lh_roll', (0, 0, 1))))
    put('rkd', list(P['rk'][0]))
    put('rkf', list(P['rk'][1]))
    put('look', list(P['look']))
    return vals, spec


def rebuild(vals, spec):
    P, i = {}, 0
    for key, n in spec:
        v = vals[i:i + n]
        i += n
        P[key] = v
    r = P['root']
    out = {'root': dict(lean=r[0], tilt=r[1], turn=r[2], x=r[3], y=r[4], f=r[5]),
           'rf': tuple(P['rf']), 'lf': tuple(P['lf']), 'rh': tuple(P['rh']),
           'rh_roll': tuple(P['rh_roll']), 'lh_roll': tuple(P['lh_roll']),
           'rk': (tuple(P['rkd']), tuple(P['rkf'])), 'look': tuple(P['look'])}
    out['lh'] = tuple(P['lh'])
    out['grab'] = tuple(P['grab'])
    return out


def norm_key(P):
    """normalise racket vectors so they interpolate evenly, and turn the root's y (an offset, by default added to
    the height that keeps the planted feet on the floor) into an absolute height for this key"""
    P = dict(P)
    d, f = P['rk']
    P['rk'] = (unit(d), unit(f))
    root = dict(P['root'])
    off = root.get('y', 0) or 0
    root['y'] = off if root.get('auto') is False else auto_height(P, dict(root, y=0)) + off
    P['root'] = root
    if isinstance(P['lh'], tuple) and P['lh'] and P['lh'][0] == 'racket':
        # left hand on the racket: its free target is that racket point, fully grabbed. Rigid arms can only hold a
        # racket together in some spots, so nudge the right hand (as little as possible) until the left one reaches
        s = P['lh'][1]
        P['grab'] = (1.0, s)
        P['lh'] = (0, 0, 0)
        P['rh'] = fit_two_hands(P)
        mats = solve_pose(P)
        q = racket_point(mats, s)
        P['lh'] = (q[0], q[1], -q[2])
    else:
        P['grab'] = (0.0, P.get('lh_s', 0.6))
    return P


def two_hand_error(P):
    mats = solve_pose(P)
    W = world(mats)
    lhp = pos_of(r6.mul(W['Left Arm'], r6.mat(p=(0, -1, 0))))
    on = pos_of(r6.mul(W['Racket'], r6.mat(p=(0, grip_s(W['Torso'], W['Racket'], P['grab'][1]), 0))))
    return length(sub(lhp, on))


def fit_two_hands(P):
    start = tuple(P['rh'])
    best = start
    cost = lambda rh: two_hand_error(dict(P, rh=rh)) + 0.12 * length(sub(rh, start))
    bc = cost(best)
    step = 0.25
    while step > 0.015 and bc > 0.03:
        moved = False
        for axis in range(3):
            for sgn in (1, -1):
                c = list(best)
                c[axis] += sgn * step
                c = tuple(c)
                cc = cost(c)
                if cc < bc:
                    best, bc, moved = c, cc, True
        if not moved:
            step /= 2
    return best


def interpolate(keys, length, loop, t):
    """keys: [(t, pose, opts)] -> pose at time t, smooth cubic through the keys"""
    if loop:
        t = t % length
    else:
        t = max(0.0, min(length, t))
    cache = _FLAT.get(id(keys))
    if cache is None or cache[0] is not keys:
        cache = (keys,) + _flatten_keys(keys)
        _FLAT[id(keys)] = cache
    _, flats, spec0 = cache
    return _interp(keys, flats, spec0, length, loop, t)


_FLAT = {}


def _flatten_keys(keys):
    flats = []
    spec0 = None
    for kt, P, o in keys:
        v, spec = flatten(norm_key(P))
        if spec0 is None:
            spec0 = spec
        flats.append(v)
    return flats, spec0


def _interp(keys, flats, spec0, length, loop, t):
    ts = [k[0] for k in keys]
    n = len(keys)
    # segment
    i = 0
    while i < n - 2 and t > ts[i + 1]:
        i += 1
    t0, t1 = ts[i], ts[i + 1]
    h = max(1e-6, t1 - t0)
    u = (t - t0) / h

    def tangent(k):
        if keys[k][2].get('hold'):
            return [0.0] * len(flats[k])
        if loop and n > 2:
            # the last key equals the first: wrap around
            if k == 0 or k == n - 1:
                a, b = flats[n - 2], flats[1]
                dt = (ts[n - 1] - ts[n - 2]) + (ts[1] - ts[0])
                return [(y - x) / dt for x, y in zip(a, b)]
        if k == 0 or k == n - 1:
            return [0.0] * len(flats[k])
        a, b = flats[k - 1], flats[k + 1]
        dt = ts[k + 1] - ts[k - 1]
        tension = keys[k][2].get('tension', 0.0)
        return [(1 - tension) * (y - x) / dt for x, y in zip(a, b)]
    m0, m1 = tangent(i), tangent(i + 1)
    if keys[i][2].get('linear'):
        out = [a + (b - a) * u for a, b in zip(flats[i], flats[i + 1])]
    else:
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        out = []
        for a, b, ma, mb in zip(flats[i], flats[i + 1], m0, m1):
            out.append(h00 * a + h10 * h * ma + h01 * b + h11 * h * mb)
    return rebuild(out, spec0)


def bake(clip):
    """clip -> list of (t, {joint: Transform}) at FPS (plus the exact end)"""
    length, loop = clip['length'], clip['loop']
    n = int(round(length * FPS))
    frames = []
    for i in range(n + (0 if loop else 1)):
        t = min(length, i / FPS)
        P = interpolate(clip['keys'], length, loop, t)
        if P['grab'][0] > 0.98:
            P['rh'] = fit_two_hands(P)          # keep both hands on the handle between keys too
        frames.append((t, solve_pose(P), P))
    return frames


def world(mats):
    """part world CFrames (Roblox character space, HRP at (0, 0, 0)) for solved transforms"""
    return r6.solve(mats, r6.mat(p=(0, 0, 0)))


def racket_point(mats, s):
    """a point s studs up the racket from the hand, Roblox char space"""
    W = world(mats)
    return pos_of(r6.mul(W['Racket'], r6.mat(p=(0, s, 0))))
