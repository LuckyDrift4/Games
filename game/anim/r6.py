"""R6 rig maths (Roblox CFrames as 4x4 matrices) + clip sampling, shared by the Blender preview and the Roblox
exporters. Roblox space: X right, Y up, Z back (a character faces -Z).

Joints are the six R6 Motor6Ds plus W, a "RacketGrip" Motor6D from the Right Arm to the racket that works as the
wrist. Poses are solved in rig.py; lerp_cf matches CFrame:Lerp so the baked frames play the same in Roblox."""
import math


def mat(R=((1, 0, 0), (0, 1, 0), (0, 0, 1)), p=(0, 0, 0)):
    return [[R[0][0], R[0][1], R[0][2], p[0]], [R[1][0], R[1][1], R[1][2], p[1]], [R[2][0], R[2][1], R[2][2], p[2]],
            [0, 0, 0, 1]]


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inv(M):
    R = [[M[j][i] for j in range(3)] for i in range(3)]
    p = [-sum(R[i][k] * M[k][3] for k in range(3)) for i in range(3)]
    return mat(R, p)


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def m3(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def angles(x, y, z):
    """CFrame.Angles(x, y, z) = Rx * Ry * Rz (radians)"""
    return m3(m3(rx(x), ry(y)), rz(z))


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


M_ROOT = ((-1, 0, 0), (0, 0, 1), (0, 1, 0))
M_R = ((0, 0, 1), (0, 1, 0), (-1, 0, 0))
M_L = ((0, 0, -1), (0, 1, 0), (1, 0, 0))
HAND = (0, -1.15, 0)          # racket grip point in Right Arm space (just past the hand)
RACKET_BUTT = 0.30            # the hand holds the racket 0.30 studs above its butt cap
# joint: (part0, part1, C0, C1, Roblox Motor6D name)
JOINTS = {
    'Root': ('HumanoidRootPart', 'Torso', mat(M_ROOT, (0, 0, 0)), mat(M_ROOT, (0, 0, 0)), 'RootJoint'),
    'Neck': ('Torso', 'Head', mat(M_ROOT, (0, 1, 0)), mat(M_ROOT, (0, -0.5, 0)), 'Neck'),
    'RS': ('Torso', 'Right Arm', mat(M_R, (1, 0.5, 0)), mat(M_R, (-0.5, 0.5, 0)), 'Right Shoulder'),
    'LS': ('Torso', 'Left Arm', mat(M_L, (-1, 0.5, 0)), mat(M_L, (0.5, 0.5, 0)), 'Left Shoulder'),
    'RH': ('Torso', 'Right Leg', mat(M_R, (1, -1, 0)), mat(M_R, (0.5, 1, 0)), 'Right Hip'),
    'LH': ('Torso', 'Left Leg', mat(M_L, (-1, -1, 0)), mat(M_L, (-0.5, 1, 0)), 'Left Hip'),
    'W': ('Right Arm', 'Racket', mat(p=HAND), mat(), 'RacketGrip'),
}
ORDER = ['Root', 'Neck', 'RS', 'LS', 'RH', 'LH', 'W']
PART_SIZE = {'HumanoidRootPart': (2, 2, 1), 'Torso': (2, 2, 1), 'Head': (2, 1, 1), 'Right Arm': (1, 2, 1),
             'Left Arm': (1, 2, 1), 'Right Leg': (1, 2, 1), 'Left Leg': (1, 2, 1)}
DEFAULT_W = ((0, -0.2, -1), (1, 0, 0))          # arm space (only used if a clip sets no W)


def frame_from(direction, face):
    """rotation whose +Y = direction (racket head) and +Z = face normal (orthogonalised), in Right Arm space"""
    Y = norm(direction)
    d = sum(a * b for a, b in zip(face, Y))
    Z = norm(tuple(f - d * y for f, y in zip(face, Y)))
    X = cross(Y, Z)
    return tuple(tuple((X, Y, Z)[c][r] for c in range(3)) for r in range(3))


def ease(u, kind):
    u = max(0.0, min(1.0, u))
    if kind == 'linear':
        return u
    if kind == 'in':
        return u * u * u
    if kind == 'out':
        return 1 - (1 - u) ** 3
    return u * u * (3 - 2 * u)               # inout


def joint_matrix(pose, j):
    """Motor6D.Transform for one joint: CFrame.new(px,py,pz) * CFrame.Angles(rx,ry,rz), or for the racket joint W a
    (direction, face) pair in Right Arm space"""
    if j == 'W':
        d, f = pose.get('W', DEFAULT_W)
        return mat(frame_from(d, f))
    v = tuple(pose.get(j, (0, 0, 0)))
    v = v + (0, 0, 0)[:6 - len(v)]
    r = math.radians
    return mat(angles(r(v[0]), r(v[1]), r(v[2])), (v[3], v[4], v[5]))


def to_quat(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1) * 2
        return ((m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, .25 * s)
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1 + m[0][0] - m[1][1] - m[2][2]) * 2
        return (.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s)
    if m[1][1] > m[2][2]:
        s = math.sqrt(1 + m[1][1] - m[0][0] - m[2][2]) * 2
        return ((m[0][1] + m[1][0]) / s, .25 * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s)
    s = math.sqrt(1 + m[2][2] - m[0][0] - m[1][1]) * 2
    return ((m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, .25 * s, (m[1][0] - m[0][1]) / s)


def from_quat(q, p):
    x, y, z, w = q
    R = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return mat(R, p)


def lerp_cf(A, B, u):
    """CFrame:Lerp: slerp the rotation (shortest path), lerp the position"""
    qa, qb = to_quat(A), to_quat(B)
    dot = sum(a * b for a, b in zip(qa, qb))
    if dot < 0:
        qb, dot = tuple(-c for c in qb), -dot
    if dot > .9995:
        q = tuple(a + (b - a) * u for a, b in zip(qa, qb))
    else:
        th = math.acos(dot)
        sa, sb = math.sin((1 - u) * th) / math.sin(th), math.sin(u * th) / math.sin(th)
        q = tuple(a * sa + b * sb for a, b in zip(qa, qb))
    n = math.sqrt(sum(c * c for c in q))
    q = tuple(c / n for c in q)
    p = tuple(A[i][3] + (B[i][3] - A[i][3]) * u for i in range(3))
    return from_quat(q, p)


def solve(pose_mats, root=None):
    """world CFrames of every part (and the racket) for one sampled pose; HumanoidRootPart at `root`"""
    root = root or mat(p=(0, 3, 0))
    W = {'HumanoidRootPart': root}
    for j in ORDER:
        p0, p1, C0, C1, _ = JOINTS[j]
        W[p1] = mul(mul(mul(W[p0], C0), pose_mats[j]), inv(C1))
    return W
