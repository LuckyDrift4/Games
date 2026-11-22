"""Write a studmap Group tree as a Roblox model file (.rbxmx) and as JSON for the three.js preview."""
import json
from xml.sax.saxutils import escape

from .core import Group, hexcol

# Enum.Material values
MATERIAL = {'plastic': 256, 'smooth': 272, 'neon': 288, 'wood': 512, 'glass': 1568, 'concrete': 816,
            'metal': 1088, 'grass': 1280, 'slate': 800, 'fabric': 1312, 'sand': 1296}
SURF_STUDS, SURF_SMOOTH = 3, 0          # Enum.SurfaceType.Studs / Smooth
SHAPE = {'ball': 0, 'block': 1, 'cyl': 2}  # Enum.PartType


def _n(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


def _children_xml(p, nref):
    out = []
    ex = p.extra or {}
    if ex.get('mesh') == 'sphere':
        out.append('<Item class="SpecialMesh" referent="RBX%X"><Properties><string name="Name">Mesh</string>'
                   '<token name="MeshType">3</token></Properties></Item>' % nref())
    if ex.get('light'):
        rng, bri, col = ex['light']
        r, g, b = hexcol(col)
        out.append('<Item class="PointLight" referent="RBX%X"><Properties><string name="Name">Light</string>'
                   '<float name="Range">%s</float><float name="Brightness">%s</float><bool name="Shadows">false</bool>'
                   '<Color3 name="Color"><R>%s</R><G>%s</G><B>%s</B></Color3></Properties></Item>'
                   % (nref(), _n(rng), _n(bri), _n(r / 255), _n(g / 255), _n(b / 255)))
    return ''.join(out)


def _part_xml(p, ref, nref=None):
    cls = {'wedge': 'WedgePart', 'spawn': 'SpawnLocation'}.get(p.shape, 'Part')
    (x, y, z), R = p.cf.p, p.cf.R
    r, g, b = hexcol(p.color)
    surf = SURF_STUDS if p.studs else SURF_SMOOTH
    props = [
        '<string name="Name">%s</string>' % escape(p.name),
        '<bool name="Anchored">true</bool>',
        '<CoordinateFrame name="CFrame"><X>%s</X><Y>%s</Y><Z>%s</Z>%s</CoordinateFrame>' % (
            _n(x), _n(y), _n(z), ''.join('<R%d%d>%s</R%d%d>' % (i, j, _n(R[i][j]), i, j) for i in range(3) for j in range(3))),
        '<Vector3 name="size"><X>%s</X><Y>%s</Y><Z>%s</Z></Vector3>' % tuple(_n(s) for s in p.size),
        '<Color3uint8 name="Color3uint8">%d</Color3uint8>' % (0xFF000000 | (r << 16) | (g << 8) | b),
        '<token name="Material">%d</token>' % MATERIAL[p.mat],
    ]
    props += ['<token name="%sSurface">%d</token>' % (f, surf) for f in ('Top', 'Bottom', 'Front', 'Back', 'Left', 'Right')]
    if p.shape in SHAPE:
        props.append('<token name="shape">%d</token>' % SHAPE[p.shape])
    if p.tr > 0:
        props.append('<float name="Transparency">%s</float>' % _n(p.tr))
    if not p.collide:
        props.append('<bool name="CanCollide">false</bool>')
    if not p.shadow:
        props.append('<bool name="CastShadow">false</bool>')
    if p.shape == 'spawn':
        props.append('<bool name="Neutral">true</bool>')
        props.append('<int name="Duration">0</int>')
    kids = _children_xml(p, nref) if (nref and p.extra) else ''
    return '<Item class="%s" referent="RBX%X"><Properties>%s</Properties>%s</Item>' % (cls, ref, ''.join(props), kids)


def write_rbxmx(path, root: Group):
    out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">']
    ref = [0]

    def nref():
        ref[0] += 1
        return ref[0]

    count = [0]

    def walk(g):
        out.append('<Item class="%s" referent="RBX%X"><Properties><string name="Name">%s</string></Properties>' % (
            g.cls, nref(), escape(g.name)))
        for c in g.children:
            if isinstance(c, Group):
                walk(c)
            else:
                out.append(_part_xml(c, nref(), nref))
                count[0] += 1
        out.append('</Item>')

    walk(root)
    out.append('</roblox>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    return count[0]


def write_preview_json(path, root: Group, views, scene=None):
    parts = []
    for p in root.parts():
        (x, y, z), R = p.cf.p, p.cf.R
        shape = 'ball' if (p.extra or {}).get('mesh') == 'sphere' else p.shape
        parts.append([shape, [round(s, 4) for s in p.size],
                      [round(v, 4) for v in (x, y, z, R[0][0], R[0][1], R[0][2], R[1][0], R[1][1], R[1][2],
                                             R[2][0], R[2][1], R[2][2])],
                      p.color, 1 if p.studs else 0, p.mat, round(p.tr, 3)])
    with open(path, 'w') as f:
        json.dump({'parts': parts, 'views': views, 'scene': scene or {}}, f, separators=(',', ':'))
    return len(parts)
