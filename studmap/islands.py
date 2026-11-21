"""Floating stud islands built from square grid cells: dirt column + grass slab, grass 'drips' hanging over every
exposed edge (where the neighbour cell is missing or lower), optional rocky underside. Cell (i, j) is centred at
x = i * cell, z = -j * cell (j grows toward -Z, the front)."""
import random

from .core import shade

DIRT = '#b47b50'


class Cells:
    def __init__(self, cell=24.0, seed=0):
        self.cell = cell
        self.c = {}
        self.rng = random.Random(seed)

    def add(self, i, j, top=0.0, grass='#6fd94f', dirt=DIRT, depth=None):
        self.c[(i, j)] = dict(top=top, grass=grass, dirt=dirt, depth=depth or self.rng.choice((16, 18, 20, 22)))

    def rect(self, i0, i1, j0, j1, **kw):
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                self.add(i, j, **kw)

    def top(self, i, j):
        return self.c[(i, j)]['top'] if (i, j) in self.c else None

    def build(self, P, drips=True, under=True):
        C, rng = self.cell, self.rng
        for (i, j), d in sorted(self.c.items()):
            x0, x1 = i * C - C / 2, i * C + C / 2
            z0, z1 = -j * C - C / 2, -j * C + C / 2
            t, dep, g, dirt = d['top'], d['depth'], d['grass'], d['dirt']
            P.span(x0, x1, t - dep, t - 2.4, z0, z1, dirt if (i + j) % 2 else shade(dirt, .95), name='Dirt')
            P.span(x0, x1, t - 2.4, t, z0, z1, g, name='Grass')
            if under and rng.random() < .55:                     # rocky underside step
                w = C * rng.uniform(.4, .75)
                cx, cz = (x0 + x1) / 2 + rng.uniform(-3, 3), (z0 + z1) / 2 + rng.uniform(-3, 3)
                h = rng.uniform(4, 9)
                P.span(cx - w / 2, cx + w / 2, t - dep - h, t - dep, cz - w / 2, cz + w / 2, shade(dirt, .82), name='Dirt')
            if not drips:
                continue
            for (di, dj, axis, edge, out) in ((1, 0, 'z', x1, 1), (-1, 0, 'z', x0, -1), (0, -1, 'x', z1, 1), (0, 1, 'x', z0, -1)):
                nt = self.top(i + di, j + dj)
                drop = dep if nt is None else t - nt
                if drop <= 0.5:
                    continue
                s0, s1 = (z0, z1) if axis == 'z' else (x0, x1)
                s = s0
                k = 0
                while s < s1 - .2:
                    w = min(rng.choice((2.0, 3.0, 4.0)), s1 - s)
                    L = min(drop - .3, rng.choice((1.4, 2.6, 3.8)) if k % 2 == 0 else rng.choice((.8, 1.6)))
                    if L > .3:
                        y0, y1 = t - 2.4 - L, t - .2
                        if axis == 'z':
                            P.span(edge, edge + .5 * out, y0, y1, s, s + w, g, name='GrassDrip')
                        else:
                            P.span(s, s + w, y0, y1, edge, edge + .5 * out, g, name='GrassDrip')
                    s += w
                    k += 1
        return P
