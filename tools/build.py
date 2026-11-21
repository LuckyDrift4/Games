"""Build a map: python3 tools/build.py <map module> [--render] [--dpr 2]
Writes out/<map>/<Name>.rbxmx (insert into Studio) and out/<map>/parts.json (preview); --render makes the PNGs."""
import importlib
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studmap.export import write_preview_json, write_rbxmx  # noqa: E402


def main():
    mod_name = sys.argv[1]
    t = time.time()
    mod = importlib.import_module('maps.' + mod_name)
    res = mod.build()
    root, views = res[0], res[1]
    scene = res[2] if len(res) > 2 else {}
    out = os.path.join(ROOT, 'out', mod_name)
    os.makedirs(out, exist_ok=True)
    n = write_rbxmx(os.path.join(out, mod.NAME + '.rbxmx'), root)
    write_preview_json(os.path.join(out, 'parts.json'), root, views, scene)
    by = {}
    bad = []
    for p in root.parts():
        by[p.shape] = by.get(p.shape, 0) + 1
        R = p.cf.R
        cols = [tuple(R[i][j] for i in range(3)) for j in range(3)]
        ortho = all(abs(sum(cols[a][k] * cols[b][k] for k in range(3)) - (1 if a == b else 0)) < 1e-4
                    for a in range(3) for b in range(3))
        det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1]) - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
               + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
        if not ortho or abs(det - 1) > 1e-4:
            bad.append('%s: rotation not orthonormal / mirrored (det %.3f)' % (p.name, det))
        if min(p.size) < 0.05 or max(p.size) > 2048:
            bad.append('%s: size %s outside 0.05..2048' % (p.name, p.size))
    if bad:
        print('VALIDATE_FAILED', len(bad)); print('\n'.join(bad[:20])); sys.exit(1)
    print('BUILD_OK %s: %d parts %s in %.1fs -> %s' % (mod.NAME, n, by, time.time() - t, out))
    if '--render' in sys.argv:
        dpr = sys.argv[sys.argv.index('--dpr') + 1] if '--dpr' in sys.argv else '1'
        subprocess.run(['node', os.path.join(ROOT, 'preview', 'render.cjs'), out, dpr], check=True)


if __name__ == '__main__':
    main()
