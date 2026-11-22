"""studmap core: Parts, CFrames, props and groups in ROBLOX space.

Roblox space everywhere: X east, Y up, Z south, 1 unit = 1 stud, a part's front (LookVector) is -Z.
Rotation matrices follow Roblox: columns are the part's right (X), up (Y) and back (Z) vectors.
"""
import math

I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _mm(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _mv(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))


def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def length(a): return math.sqrt(dot(a, a))
def norm(a): l = length(a); return (a[0] / l, a[1] / l, a[2] / l)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rot_y(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def from_axes(X, Y, Z):
    """rotation whose columns are the given right / up / back vectors"""
    return tuple((X[i], Y[i], Z[i]) for i in range(3))


class CF:
    """position + rotation (like a Roblox CFrame)"""
    __slots__ = ('p', 'R')

    def __init__(self, p=(0, 0, 0), R=I3):
        self.p = (float(p[0]), float(p[1]), float(p[2]))
        self.R = R

    def __mul__(self, o):
        return CF(add(self.p, _mv(self.R, o.p)), _mm(self.R, o.R))

    def point(self, v): return add(self.p, _mv(self.R, v))
    def vec(self, v): return _mv(self.R, v)


def cf(x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0, roll=0.0):
    """yaw about Y, then pitch about X, then roll about Z (degrees). yaw > 0 turns the front (-Z) toward -X."""
    R = _mm(rot_y(yaw), _mm(rot_x(pitch), rot_z(roll)))
    return CF((x, y, z), R)


def yaw_to(x, z, tx, tz):
    """yaw that turns a part's front (-Z) from (x, z) toward (tx, tz)"""
    return math.degrees(math.atan2(-(tx - x), -(tz - z)))


def hexcol(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(h, k):
    """multiply a hex colour's value by k (k < 1 darker, > 1 lighter)"""
    r, g, b = hexcol(h)
    f = lambda c: max(0, min(255, int(round(c * k))))
    return '#%02x%02x%02x' % (f(r), f(g), f(b))


class Part:
    """one Roblox part. shape: block | wedge | cyl | ball | spawn. mat: plastic (studs) | smooth | neon | glass | wood
    | concrete | metal | grass | slate | fabric | sand. extra: optional children, e.g. {'mesh': 'sphere'} (an ellipsoid
    SpecialMesh filling the part) or {'light': (range, brightness, '#rrggbb')} (a PointLight)"""
    __slots__ = ('name', 'size', 'cf', 'color', 'shape', 'mat', 'studs', 'tr', 'collide', 'shadow', 'extra')

    def __init__(self, name, size, cframe, color, shape='block', mat='plastic', studs=None, tr=0.0, collide=True,
                 shadow=True, extra=None):
        self.name, self.size, self.cf, self.color, self.shape = name, tuple(float(s) for s in size), cframe, color, shape
        self.mat = mat
        self.studs = (mat == 'plastic' and shape in ('block', 'wedge', 'spawn')) if studs is None else studs
        self.tr, self.collide, self.shadow = tr, collide, shadow
        self.extra = extra

    def moved(self, c):
        return Part(self.name, self.size, c * self.cf, self.color, self.shape, self.mat, self.studs, self.tr,
                    self.collide, self.shadow, self.extra)


class Prop:
    """a reusable piece built in its own local space (origin = bottom centre, front = -Z)"""

    def __init__(self, name):
        self.name = name
        self.parts = []

    # -- primitives ---------------------------------------------------------------------------------
    def box(self, size, pos=(0, 0, 0), color='#ffffff', yaw=0.0, pitch=0.0, roll=0.0, name=None, **kw):
        if min(size) <= 0.01:
            return self
        self.parts.append(Part(name or self.name, size, cf(*pos, yaw=yaw, pitch=pitch, roll=roll), color, **kw))
        return self

    def span(self, x0, x1, y0, y1, z0, z1, color, name=None, **kw):
        """axis-aligned box between two corners"""
        return self.box((abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                        color, name=name, **kw)

    def wedge(self, size, pos=(0, 0, 0), color='#ffffff', yaw=0.0, pitch=0.0, roll=0.0, name=None, **kw):
        """Roblox WedgePart: tall end at +Z (back), slope faces -Z (front) and up"""
        self.parts.append(Part(name or self.name, size, cf(*pos, yaw=yaw, pitch=pitch, roll=roll), color,
                               shape='wedge', **kw))
        return self

    def cyl(self, length, radius, pos=(0, 0, 0), color='#ffffff', axis='y', yaw=0.0, name=None, **kw):
        """cylinder part; Roblox cylinders run along their X axis, so axis 'y' rolls it upright"""
        roll = 90.0 if axis == 'y' else 0.0
        y2 = yaw + (90.0 if axis == 'z' else 0.0)
        kw.setdefault('mat', 'smooth')
        self.parts.append(Part(name or self.name, (length, radius * 2, radius * 2), cf(*pos, yaw=y2, roll=roll),
                               color, shape='cyl', **kw))
        return self

    def ball(self, d, pos=(0, 0, 0), color='#ffffff', name=None, **kw):
        kw.setdefault('mat', 'smooth')
        self.parts.append(Part(name or self.name, (d, d, d), cf(*pos), color, shape='ball', **kw))
        return self

    def tri(self, p0, p1, p2, y_top, t, color, name=None, **kw):
        """flat horizontal right triangle (one WedgePart): right angle at p0, points are (x, z); top face at y_top"""
        P0, P1, P2 = (p0[0], 0.0, p0[1]), (p1[0], 0.0, p1[1]), (p2[0], 0.0, p2[1])
        v1, v2 = sub(P1, P0), sub(P2, P0)
        L1, L2 = length(v1), length(v2)
        if L1 < 0.05 or L2 < 0.05:
            return self
        Z = mul(v1, -1.0 / L1)
        Y = mul(v2, 1.0 / L2)
        X = cross(Y, Z)
        c = add(P0, mul(add(v1, v2), 0.5))
        self.parts.append(Part(name or self.name, (t, L2, L1), CF((c[0], y_top - t / 2, c[2]), from_axes(X, Y, Z)),
                               color, shape='wedge', **kw))
        return self

    def poly(self, pts, y_top, t, color, name=None, **kw):
        """flat convex polygon (x, z points) as right-triangle wedges fanned from the centroid: no overlaps"""
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ex, ez = b[0] - a[0], b[1] - a[1]
            L2 = ex * ex + ez * ez
            u = ((cx - a[0]) * ex + (cz - a[1]) * ez) / L2
            u = max(0.0, min(1.0, u))
            m = (a[0] + ex * u, a[1] + ez * u)
            self.tri(m, (cx, cz), a, y_top, t, color, name, **kw)
            self.tri(m, (cx, cz), b, y_top, t, color, name, **kw)
        return self

    def put(self, other, c):
        """nest another prop at local CFrame c"""
        for p in other.parts:
            self.parts.append(p.moved(c))
        return self

    @property
    def count(self):
        return len(self.parts)


def ngon(r, n, rot=0.0, cx=0.0, cz=0.0):
    return [(cx + r * math.cos(math.radians(rot + i * 360.0 / n)), cz + r * math.sin(math.radians(rot + i * 360.0 / n)))
            for i in range(n)]


class Group:
    """a Folder or Model in the output tree"""

    def __init__(self, name, cls='Folder'):
        self.name, self.cls = name, cls
        self.children = []

    def add(self, x):
        self.children.append(x)
        return x

    def folder(self, name, cls='Folder'):
        for c in self.children:
            if isinstance(c, Group) and c.name == name:
                return c
        return self.add(Group(name, cls))

    def place(self, prop, c, name=None, cls='Model'):
        """add a prop instance as a Model (or straight into this group when cls is None)"""
        target = self.add(Group(name or prop.name, cls)) if cls else self
        for p in prop.parts:
            target.add(p.moved(c))
        return target

    def parts(self):
        for c in self.children:
            if isinstance(c, Group):
                yield from c.parts()
            else:
                yield c
