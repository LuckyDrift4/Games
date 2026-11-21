// Preview of a studmap map: builds merged meshes from parts.json (Roblox space = three.js space, Y up, studs),
// procedural Roblox-style stud texture + normal map, sun shadows. Exposes window.setView(i) for render.cjs.
import * as THREE from 'three';

const params = new URLSearchParams(location.search);
const src = params.get('map');
const W = +params.get('w') || 1600, H = +params.get('h') || 900;

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(window.devicePixelRatio || 1);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xcfe9f8, 700, 2600);
const camera = new THREE.PerspectiveCamera(60, W / H, 0.5, 6000);

// lighting close to a bright Roblox day (Future-ish): sky fill + warm sun with shadows
scene.add(new THREE.HemisphereLight(0xdff1ff, 0x8d8a70, 1.55));
const sun = new THREE.DirectionalLight(0xfff4e0, 2.1);
sun.position.set(260, 420, 180);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
const sc = sun.shadow.camera;
sc.left = -420; sc.right = 420; sc.top = 420; sc.bottom = -420; sc.near = 10; sc.far = 1400;
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.6;
scene.add(sun);
scene.add(sun.target);

// ---------- stud texture (one tile = one stud) ----------
function studTextures() {
  const N = 64, c1 = document.createElement('canvas'), c2 = document.createElement('canvas');
  c1.width = c1.height = c2.width = c2.height = N;
  const g1 = c1.getContext('2d'), g2 = c2.getContext('2d');
  const col = g1.createImageData(N, N), nrm = g2.createImageData(N, N);
  const hgt = (x, y) => {                   // rounded square bump, 0..1
    const u = Math.abs(x / N - 0.5), v = Math.abs(y / N - 0.5);
    const r = 0.06, half = 0.3;
    const dx = Math.max(u - (half - r), 0), dy = Math.max(v - (half - r), 0);
    const d = Math.hypot(dx, dy) - r;        // <0 inside
    return 1 - Math.min(1, Math.max(0, (d + 0.035) / 0.07));
  };
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const i = (y * N + x) * 4;
    const hx = hgt(x + 1, y) - hgt(x - 1, y), hy = hgt(x, y + 1) - hgt(x, y - 1);
    const s = 2.2;
    let nx = -hx * s, ny = hy * s, nz = 1; const l = Math.hypot(nx, ny, nz); nx /= l; ny /= l; nz /= l;
    nrm.data[i] = (nx * .5 + .5) * 255; nrm.data[i + 1] = (ny * .5 + .5) * 255; nrm.data[i + 2] = (nz * .5 + .5) * 255; nrm.data[i + 3] = 255;
    const h = hgt(x, y), edge = h > 0.02 && h < 0.98 ? 1 : 0;
    const u = Math.abs(x / N - 0.5), v = Math.abs(y / N - 0.5), seam = Math.max(u, v) > 0.47 ? 1 : 0;
    const k = 255 * (1 - 0.13 * edge - 0.05 * seam);
    col.data[i] = col.data[i + 1] = col.data[i + 2] = k; col.data[i + 3] = 255;
  }
  g1.putImageData(col, 0, 0); g2.putImageData(nrm, 0, 0);
  const t1 = new THREE.CanvasTexture(c1), t2 = new THREE.CanvasTexture(c2);
  for (const t of [t1, t2]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  }
  t1.colorSpace = THREE.SRGBColorSpace;
  return [t1, t2];
}
const [studMap, studNormal] = studTextures();

// ---------- geometry ----------
class Acc {
  constructor() { this.p = []; this.n = []; this.uv = []; this.c = []; }
  quad(a, b, c, d, nrm, uvs, col) { this.tri(a, b, c, nrm, [uvs[0], uvs[1], uvs[2]], col); this.tri(a, c, d, nrm, [uvs[0], uvs[2], uvs[3]], col); }
  tri(a, b, c, nrm, uvs, col) {
    for (const [v, t] of [[a, uvs[0]], [b, uvs[1]], [c, uvs[2]]]) { this.p.push(...v); this.n.push(...nrm); this.uv.push(...t); this.c.push(col.r, col.g, col.b); }
  }
  mesh(mat, shadows = true) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    const m = new THREE.Mesh(g, mat); m.castShadow = shadows; m.receiveShadow = true; return m;
  }
}

function xf(cf) {     // cf = [x, y, z, R00..R22]
  const [x, y, z, a, b, c, d, e, f, g, h, i] = cf;
  return {
    p: v => [x + a * v[0] + b * v[1] + c * v[2], y + d * v[0] + e * v[1] + f * v[2], z + g * v[0] + h * v[1] + i * v[2]],
    n: v => { const r = [a * v[0] + b * v[1] + c * v[2], d * v[0] + e * v[1] + f * v[2], g * v[0] + h * v[1] + i * v[2]]; const l = Math.hypot(...r); return r.map(q => q / l); },
  };
}

function addBox(acc, s, T, col) {
  const [hx, hy, hz] = s.map(q => q / 2), [sx, sy, sz] = s;
  const F = [   // [normal, 4 corners, u size, v size]
    [[1, 0, 0], [[hx, -hy, hz], [hx, -hy, -hz], [hx, hy, -hz], [hx, hy, hz]], sz, sy],
    [[-1, 0, 0], [[-hx, -hy, -hz], [-hx, -hy, hz], [-hx, hy, hz], [-hx, hy, -hz]], sz, sy],
    [[0, 1, 0], [[-hx, hy, hz], [hx, hy, hz], [hx, hy, -hz], [-hx, hy, -hz]], sx, sz],
    [[0, -1, 0], [[-hx, -hy, -hz], [hx, -hy, -hz], [hx, -hy, hz], [-hx, -hy, hz]], sx, sz],
    [[0, 0, 1], [[-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]], sx, sy],
    [[0, 0, -1], [[hx, -hy, -hz], [-hx, -hy, -hz], [-hx, hy, -hz], [hx, hy, -hz]], sx, sy],
  ];
  for (const [n, q, u, v] of F) acc.quad(...q.map(T.p), T.n(n), [[0, 0], [u, 0], [u, v], [0, v]], col);
}

function addWedge(acc, s, T, col) {
  const [hx, hy, hz] = s.map(q => q / 2), [sx, sy, sz] = s, sl = Math.hypot(sy, sz);
  acc.quad(...[[-hx, -hy, -hz], [hx, -hy, -hz], [hx, -hy, hz], [-hx, -hy, hz]].map(T.p), T.n([0, -1, 0]), [[0, 0], [sx, 0], [sx, sz], [0, sz]], col);
  acc.quad(...[[-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]].map(T.p), T.n([0, 0, 1]), [[0, 0], [sx, 0], [sx, sy], [0, sy]], col);
  acc.quad(...[[hx, -hy, -hz], [-hx, -hy, -hz], [-hx, hy, hz], [hx, hy, hz]].map(T.p), T.n([0, sz, -sy]), [[0, 0], [sx, 0], [sx, sl], [0, sl]], col);
  acc.tri(...[[hx, -hy, -hz], [hx, hy, hz], [hx, -hy, hz]].map(T.p), T.n([1, 0, 0]), [[0, 0], [sz, sy], [sz, 0]], col);
  acc.tri(...[[-hx, -hy, hz], [-hx, hy, hz], [-hx, -hy, -hz]].map(T.p), T.n([-1, 0, 0]), [[0, 0], [0, sy], [sz, 0]], col);
}

function addCyl(acc, s, T, col, seg = 20) {       // axis along local X
  const hx = s[0] / 2, r = Math.min(s[1], s[2]) / 2;
  for (let i = 0; i < seg; i++) {
    const a0 = i / seg * Math.PI * 2, a1 = (i + 1) / seg * Math.PI * 2;
    const p = (x, a) => [x, Math.cos(a) * r, Math.sin(a) * r];
    const am = (a0 + a1) / 2;
    acc.quad(...[p(-hx, a0), p(-hx, a1), p(hx, a1), p(hx, a0)].map(T.p), T.n([0, Math.cos(am), Math.sin(am)]), [[0, 0], [1, 0], [1, 1], [0, 1]], col);
    acc.tri(...[[hx, 0, 0], p(hx, a0), p(hx, a1)].map(T.p), T.n([1, 0, 0]), [[0, 0], [1, 0], [0, 1]], col);
    acc.tri(...[[-hx, 0, 0], p(-hx, a1), p(-hx, a0)].map(T.p), T.n([-1, 0, 0]), [[0, 0], [1, 0], [0, 1]], col);
  }
}

function addBall(acc, s, T, col) {
  const r = s[0] / 2, nu = 16, nv = 10;
  const P = (i, j) => { const u = i / nu * Math.PI * 2, v = j / nv * Math.PI; return [Math.sin(v) * Math.cos(u) * r, Math.cos(v) * r, Math.sin(v) * Math.sin(u) * r]; };
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    const a = P(i, j), b = P(i + 1, j), c = P(i + 1, j + 1), d = P(i, j + 1);
    const m = [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2, (a[2] + c[2]) / 2];
    acc.quad(...[a, b, c, d].map(T.p), T.n(m), [[0, 0], [1, 0], [1, 1], [0, 1]], col);
  }
}

async function load() {
  const data = await (await fetch(src)).json();
  const buckets = new Map();     // key -> {acc, kind, tr}
  const get = (kind, tr) => { const k = kind + ':' + tr; if (!buckets.has(k)) buckets.set(k, { acc: new Acc(), kind, tr }); return buckets.get(k).acc; };
  for (const [shape, size, cf, hex, studs, mat, tr] of data.parts) {
    const T = xf(cf), col = new THREE.Color(hex);
    const kind = mat === 'neon' ? 'neon' : (studs ? 'stud' : 'smooth');
    const acc = get(kind, tr);
    if (shape === 'wedge') addWedge(acc, size, T, col);
    else if (shape === 'cyl') addCyl(acc, size, T, col);
    else if (shape === 'ball') addBall(acc, size, T, col);
    else addBox(acc, size, T, col);
  }
  for (const { acc, kind, tr } of buckets.values()) {
    let mat;
    if (kind === 'neon') mat = new THREE.MeshBasicMaterial({ vertexColors: true });
    else if (kind === 'stud') mat = new THREE.MeshStandardMaterial({ vertexColors: true, map: studMap, normalMap: studNormal, normalScale: new THREE.Vector2(.9, .9), roughness: .78, metalness: 0 });
    else mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .55, metalness: 0 });
    if (tr > 0) { mat.transparent = true; mat.opacity = 1 - tr; mat.depthWrite = false; }
    scene.add(acc.mesh(mat, kind !== 'neon' && tr === 0));
  }
  const sc0 = data.scene || {};
  if (sc0.center) {
    const [cx, cy, cz] = sc0.center, r = sc0.radius || 420;
    sun.target.position.set(cx, cy, cz); sun.position.set(cx + 260, cy + 420, cz + 180);
    sc.left = -r; sc.right = r; sc.top = r; sc.bottom = -r; sc.far = 1400 + r; sc.updateProjectionMatrix();
  }
  if (sc0.sea) { scene.fog.color.set(sc0.fog || 0xcfe9f8); }
  window.VIEWS = data.views;
  window.PARTS = data.parts.length;
  setView(0);
  window.READY = true;
}

window.setView = (i) => {
  const v = window.VIEWS[i];
  camera.fov = v.fov || 60; camera.aspect = W / H; camera.updateProjectionMatrix();
  camera.position.set(...v.pos); camera.lookAt(...v.target);
  renderer.render(scene, camera);
  return v.name;
};

load();
