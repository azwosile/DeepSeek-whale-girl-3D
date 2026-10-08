# 大肥鱼第二版 装配 f004：眼前发丝贴图修复 + 袖子缩短 + 后发覆盖鱼尾
import bpy, bmesh, json, math, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_assembly_f003.blend')
sc = bpy.context.scene; R = {}
def labels(me):
    n = len(me.vertices); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    return np.array([f(i) for i in range(n)])
def V(o): return np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
def setV(o, P):
    Mi = o.matrix_world.inverted()
    for i, v in enumerate(o.data.vertices): v.co = Mi @ Vector(P[i])
    o.data.update()
def bvh_world(o, keep=None):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.verts.ensure_lookup_table()
    if keep is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    t = BVHTree.FromBMesh(bm); bm.free(); return t
body = bpy.data.objects['FISH2_body']; BP = V(body); BL = labels(body.data)
skin = min(np.unique(BL), key=lambda i: BP[BL == i][:, 2].min())
cnt = {i: int((BL == i).sum()) for i in np.unique(BL)}
# =============== A. eye-zone hair texture ===============
mat = body.material_slots[0].material
img = [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image][0]
W, H = img.size; print('FX image', img.name, W, H, img.filepath)
PX = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(PX); PX = PX.reshape(H, W, 4)
me = body.data; uvl = me.uv_layers.active.data
luv = np.empty(len(me.loops) * 2, np.float32); uvl.foreach_get('uv', luv); luv = luv.reshape(-1, 2)
lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
def sample(uv):
    x = np.clip((uv[:, 0] % 1.0) * W, 0, W - 1).astype(int); y = np.clip((uv[:, 1] % 1.0) * H, 0, H - 1).astype(int); return PX[y, x, :3]
lcol = sample(luv)
vcol = np.zeros((len(BP), 3)); vn = np.zeros(len(BP)); np.add.at(vcol, lv, lcol); np.add.at(vn, lv, 1); vcol /= np.maximum(vn, 1)[:, None]
rig_hx = float(np.median(BP[(BL == skin) & (np.abs(BP[:, 2] - 1.36) < 0.01)][:, 0]))
TB = bvh_world(body)
Y0, Y1, Z0, Z1, ST = -0.12, 0.12, 1.38, 1.64, 0.002
ny, nz = int((Y1 - Y0) / ST) + 1, int((Z1 - Z0) / ST) + 1
FX = np.full((ny, nz), np.nan)
for iy in range(ny):
    for iz in range(nz):
        y, z = Y0 + iy * ST, Z0 + iz * ST; o = Vector((0.5, y, z)); hits = []
        for _ in range(16):
            h = TB.ray_cast(o, Vector((-1, 0, 0)), 1.0)
            if h[0] is None: break
            hits.append(h[0].x); o = h[0] + Vector((-1e-4, 0, 0))
            if h[0].x < rig_hx - 0.05: break
        if not hits: continue
        k = len(hits)
        for i in range(len(hits) - 1):
            if hits[i] - hits[i + 1] > 0.05: k = i + 1; break
        pre = hits[:k]                      # surfaces before the head interior
        FX[iy, iz] = pre[-2] if (len(pre) % 2 == 0 and len(pre) >= 2) else pre[-1]
FXm = FX.copy()
for dy in (-2, -1, 0, 1, 2):
    for dz in (-2, -1, 0, 1, 2):
        FXm = np.fmax(FXm, np.roll(np.roll(FX, dy, 0), dz, 1))
FX = FXm
def face_x(P):
    iy = np.clip(np.round((P[:, 1] - Y0) / ST).astype(int), 0, ny - 1); iz = np.clip(np.round((P[:, 2] - Z0) / ST).astype(int), 0, nz - 1)
    return FX[iy, iz]
inreg = (np.abs(BP[:, 1]) < 0.115) & (BP[:, 2] > Z0) & (BP[:, 2] < Z1) & (BP[:, 0] > rig_hx - 0.01) & (BL != skin)
fxv = np.where(inreg, face_x(BP), np.nan)
Hm = inreg & ~np.isnan(fxv) & (BP[:, 0] > fxv + 0.0025)      # geometry lying in front of the face surface = hair
onface = inreg & ~np.isnan(fxv) & (np.abs(BP[:, 0] - fxv) < 0.0015)
lum = vcol @ np.array([0.3, 0.59, 0.11])
dark = onface & (lum < 0.22) & (np.abs(BP[:, 1]) < 0.085) & (BP[:, 2] < 1.58)
ez0, ez1 = np.percentile(BP[dark, 2], 2), np.percentile(BP[dark, 2], 98)
band0, band1 = 1.392, ez1 + 0.020
R['eye_band'] = [round(float(band0), 3), round(float(band1), 3)]; print('FX eye dark z', ez0, ez1, 'hair-in-front', int(Hm.sum()))
FE = 0.012
wv = np.clip((BP[:, 2] - (band0 - 0.004)) / 0.004, 0, 1) * np.clip(((band1 + FE) - BP[:, 2]) / FE, 0, 1)
wv = wv * wv * (3 - 2 * wv); wv[~Hm] = 0
lowc = (BP[:, 2] < ez0 - 0.025) & (np.abs(BP[:, 1]) < 0.05); wv[lowc] = 0; Hm = Hm & ~lowc
bad = wv > 0
ref = Hm & (BP[:, 2] >= band1 + FE) & (BP[:, 2] < band1 + FE + 0.04)
gref = np.median(vcol[ref], 0); RI = np.where(ref)[0]
refc = np.zeros((len(BP), 3))
bluish = (vcol[:, 2] - vcol[:, 0] > 0.08)
sideref = ~Hm & bluish & (BL != skin) & (np.abs(BP[:, 1]) > 0.075) & (np.abs(BP[:, 1]) < 0.17) & (BP[:, 2] > 1.30) & (BP[:, 2] < 1.62)
SI = np.where(sideref)[0]
nside = 0
for i in np.where(Hm & (BP[:, 2] > band0 - 0.03) & (BP[:, 2] < band1 + 0.03))[0]:
    k = SI[(np.abs(BP[SI, 2] - BP[i, 2]) < 0.012) & (np.sign(BP[SI, 1]) == np.sign(BP[i, 1] + 1e-6))]
    kt = RI[np.abs(BP[RI, 1] - BP[i, 1]) < 0.012]
    ctop = np.median(vcol[kt], 0) if len(kt) >= 3 else gref
    if len(k) >= 5:
        cs = np.median(vcol[k], 0); nside += 1
        # near the top of the band blend toward the bangs colour above, lower down use the lock's own colour
        a_ = float(np.clip((BP[i, 2] - (band1 - 0.03)) / 0.03, 0, 1)); refc[i] = cs * (1 - a_) + ctop * a_
    else:
        refc[i] = ctop
R['ref_from_side'] = nside
gfac = np.ones(len(BP))
me.calc_loop_triangles()
tri_v = np.array([t.vertices[:] for t in me.loop_triangles]); tri_l = np.array([t.loops[:] for t in me.loop_triangles])
selt = Hm[tri_v].all(1) & bad[tri_v].any(1)
npx = 0
PX0 = PX.copy()
for t in np.where(selt)[0]:
    uv = luv[tri_l[t]] * np.array([W, H]); c = refc[tri_v[t]]
    x0, y0 = np.floor(uv.min(0) - 2).astype(int); x1, y1 = np.ceil(uv.max(0) + 2).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, W - 1) + 1), np.arange(max(y0, 0), min(y1, H - 1) + 1))
    p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1); a, b, cc = uv
    den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
    if abs(den) < 1e-9: continue
    l1 = ((b[1] - cc[1]) * (p[:, 0] - cc[0]) + (cc[0] - b[0]) * (p[:, 1] - cc[1])) / den
    l2 = ((cc[1] - a[1]) * (p[:, 0] - cc[0]) + (a[0] - cc[0]) * (p[:, 1] - cc[1])) / den
    l3 = 1 - l1 - l2; tol = -min(0.6 / max(np.ptp(uv[:, 0]), np.ptp(uv[:, 1]), 1.0), 0.08)
    m = (l1 > tol) & (l2 > tol) & (l3 > tol)
    if not m.any(): continue
    L = np.clip(np.stack([l1[m], l2[m], l3[m]], 1), 0, None); L /= L.sum(1, keepdims=True)
    col = L @ c; ww = (L @ wv[tri_v[t]])[:, None]
    yy, xx = ys.ravel()[m], xs.ravel()[m]
    PX[yy, xx, :3] = PX0[yy, xx, :3] * (1 - ww) + col * ww; npx += int(m.sum())
R['hairtex'] = dict(bad_verts=int(bad.sum()), faces=int(selt.sum()), pixels=npx)
os.makedirs(ASM + 'tex', exist_ok=True)
nimg = bpy.data.images.new('FISH2_body_tex_f004', W, H, alpha=True); nimg.pixels.foreach_set(PX.ravel())
nimg.filepath_raw = ASM + 'tex/FISH2_body_tex_f004.png'; nimg.file_format = 'PNG'; nimg.save()
for s in body.material_slots:
    for n in s.material.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image == img: n.image = nimg
print('FX hairtex', R['hairtex'])
# =============== B. sleeves ===============
outf = bpy.data.objects['FISH2_outfit']; OP = V(outf); OL = labels(outf.data); OP0 = OP.copy()
S = BP[BL == skin]
hand_isl = {}
for sd in (1, -1):
    hc = np.array([-0.04, 0.422 * sd, 0.819 + 0.0259]); hand_isl[sd] = BL[int(np.argmin(np.linalg.norm(BP - hc, axis=1)))]
R['sleeve'] = {}
D_SHIFT = 0.065
for sd, nm in ((1, 'L'), (-1, 'R')):
    A = S[(S[:, 1] * sd > 0.27) & (S[:, 1] * sd < 0.39) & (S[:, 2] > 0.85)]
    c = A.mean(0); _, _, vt = np.linalg.svd(A - c); d = vt[0] * np.sign(vt[0][1] * sd)
    isl = [i for i in np.unique(OL) if (OP[OL == i][:, 1] * sd).min() > 0.05 and np.abs(OP[OL == i][:, 1]).mean() > 0.15
           and OP[OL == i][:, 2].min() > 0.78 and OP[OL == i][:, 2].max() < 1.36]
    sv = np.isin(OL, isl); t = (OP - c) @ d
    elb = np.array([-0.025, 0.273 * sd, 1.048]); te = float((elb - c) @ d)
    cuff_isl = [i for i in isl if OP[OL == i][:, 2].max() < 0.95]
    cv = np.isin(OL, cuff_isl); tube = sv & ~cv
    Sm = (BP[:, 1] * sd > 0.27) & (BL == skin); t_wr = float(((BP[Sm] - c) @ d).max()); t_cend = float(t[cv].max())
    D_SHIFT = round(t_cend - (t_wr + 0.03), 4); print('FX', nm, 't_wrist', t_wr, 'cuff end', t_cend, 'shift', D_SHIFT)
    t_end_tube = float(t[tube].max()); Lt = t_end_tube - te
    # tube compression beyond elbow
    m = tube & (t > te); tn = te + (t[m] - te) * (Lt - D_SHIFT) / Lt
    OP[m] += (tn - t[m])[:, None] * d[None, :]
    OP[cv] -= D_SHIFT * d[None, :]
    # radial clearance vs forearm skin + hand
    prof = BP[(BL == skin) | (BL == hand_isl[sd])]; prof = prof[(((prof - c) @ d) > te - 0.02) & (np.abs(prof[:, 1]) > 0.2)]
    u = np.cross(d, [0, 0, 1.0]); u /= np.linalg.norm(u); w_ = np.cross(d, u)
    def cyl(Pp):
        q = Pp - c; tt = q @ d; rr = q - tt[:, None] * d[None, :]
        return tt, np.linalg.norm(rr, axis=1), np.arctan2(rr @ w_, rr @ u)
    pt, pr, pa = cyl(prof); NB, NA = 60, 16; tb0 = te - 0.02
    RS = np.zeros((NB, NA))
    bi = np.clip(((pt - tb0) / 0.005).astype(int), 0, NB - 1); ai = ((pa + np.pi) / (2 * np.pi) * NA).astype(int) % NA
    np.maximum.at(RS, (bi, ai), pr)
    for k in range(1, NB):          # fill empty
        RS[k] = np.where(RS[k] == 0, RS[k - 1], RS[k])
    def need(Pp):
        tt, rr, aa = cyl(Pp); b_ = np.clip(((tt - tb0) / 0.005).astype(int), 0, NB - 1); a_ = ((aa + np.pi) / (2 * np.pi) * NA).astype(int) % NA
        rq = np.maximum(RS[b_, a_], np.maximum(RS[np.clip(b_ + 1, 0, NB - 1), a_], RS[np.clip(b_ - 1, 0, NB - 1), a_]))
        return tt, rr, rq
    scl = {}
    for i in cuff_isl:
        mm = OL == i; tt, rr, rq = need(OP[mm]); okm = rr > 1e-3
        f = float(np.percentile((rq[okm] + 0.004) / rr[okm], 95)) if okm.any() else 1.0
        f = min(max(f, 1.0), 1.5); scl[int(i)] = round(f, 3)
        if f > 1.0:
            q = OP[mm] - c; tt = q @ d; rad = q - tt[:, None] * d[None, :]; OP[mm] = c + tt[:, None] * d[None, :] + rad * f
    mt = sv & (t > te - 0.02); tt, rr, rq = need(OP[mt])
    push = np.maximum(0, rq + 0.003 - rr); idx = np.where(mt)[0]
    q = OP[idx] - c; ttt = q @ d; rad = q - ttt[:, None] * d[None, :]; rn = np.linalg.norm(rad, axis=1, keepdims=True)
    OP[idx] += rad / np.maximum(rn, 1e-6) * push[:, None]
    R['sleeve'][nm] = dict(islands=len(isl), cuffs=len(cuff_isl), tube_verts=int(tube.sum()), cuff_verts=int(cv.sum()), shift=D_SHIFT,
                           cuff_scale=scl, tube_pushed=int((push > 0).sum()), max_push=round(float(push.max()), 4))
setV(outf, OP); print('FX sleeve', R['sleeve'])
# =============== C. back hair drapes over the tail ===============
tail = bpy.data.objects['FISH2_tail']; TT = bvh_world(tail); TP = V(tail)
hair_isl = [i for i in np.unique(BL) if i != skin and cnt[i] > 300 and BP[BL == i][:, 2].max() > 1.40 and BP[BL == i][:, 2].min() < 1.30]
hv = np.isin(BL, hair_isl)
gy = np.arange(-0.30, 0.20, 0.005); gz = np.arange(0.80, 1.12, 0.005)
XB = np.full((len(gy), len(gz)), np.nan); XF = XB.copy()
for a, y in enumerate(gy):
    for b, z in enumerate(gz):
        h1 = TT.ray_cast(Vector((-0.6, y, z)), Vector((1, 0, 0)), 1.0); h2 = TT.ray_cast(Vector((0.4, y, z)), Vector((-1, 0, 0)), 1.0)
        if h1[0] is not None and h2[0] is not None: XB[a, b] = h1[0].x; XF[a, b] = h2[0].x
def cell(P):
    a = np.clip(np.round((P[:, 1] - gy[0]) / 0.005).astype(int), 0, len(gy) - 1); b = np.clip(np.round((P[:, 2] - gz[0]) / 0.005).astype(int), 0, len(gz) - 1); return a, b
HI = np.where(hv & (BP[:, 2] < 1.12) & (BP[:, 2] > 0.80))[0]
a, b = cell(BP[HI]); xb = XB[a, b]; xf = XF[a, b]
DL = np.zeros_like(XB)
ok = ~np.isnan(xb) & (BP[HI, 0] < xf + 0.005)
need_ = np.where(ok, BP[HI, 0] - (xb - 0.007), 0.0)
np.maximum.at(DL, (a[ok], b[ok]), np.maximum(need_[ok], 0))
R['tailhair_raw_max'] = round(float(DL.max()), 4)
# dilate (y 1.5cm, z 2cm) then anisotropic blur (y 2cm, z up 6cm) and keep >= raw
from itertools import product
def maxf(A, ry, rz):
    Bm = A.copy()
    for dy, dz in product(range(-ry, ry + 1), range(-rz, rz + 1)):
        Bm = np.maximum(Bm, np.roll(np.roll(A, dy, 0), dz, 1))
    return Bm
def gblur(A, sy, sz):
    ky = np.exp(-0.5 * (np.arange(-3 * sy, 3 * sy + 1) / sy) ** 2); ky /= ky.sum()
    kz = np.exp(-0.5 * (np.arange(-3 * sz, 3 * sz + 1) / sz) ** 2); kz /= kz.sum()
    A = np.apply_along_axis(lambda r: np.convolve(np.pad(r, 3 * sy, mode='edge'), ky, 'valid'), 0, A)
    return np.apply_along_axis(lambda r: np.convolve(np.pad(r, 3 * sz, mode='edge'), kz, 'valid'), 1, A)
D2 = gblur(maxf(DL, 3, 4), 4, 10); D2 = np.maximum(D2, DL)
D2 = gblur(D2, 2, 4); D2 = np.maximum(D2, DL)
HI2 = np.where(hv & (BP[:, 2] < 1.12 + 0.0) & (BP[:, 2] > 0.80))[0]
a, b = cell(BP[HI2]); dd = D2[a, b]
xf2 = XF[a, b]; xfill = np.where(np.isnan(xf2), -0.03, xf2)
wx = np.clip((xfill + 0.012 - BP[HI2, 0]) / 0.024, 0, 1); wx = wx * wx * (3 - 2 * wx)
BP2 = BP.copy(); BP2[HI2, 0] -= dd * wx
# top fade: no shift above 1.10
fade = np.clip((1.11 - BP2[HI2, 2]) / 0.04, 0, 1); BP2[HI2, 0] = BP[HI2, 0] - dd * wx * fade
setV(body, BP2)
# check
TTb = bvh_world(tail)
inside = 0; poke = 0
for i in HI2:
    p = Vector(BP2[i]); h = TTb.ray_cast(p, Vector((-1, 0, 0)), 1.0); h2 = TTb.ray_cast(p, Vector((1, 0, 0)), 1.0)
    if h[0] is not None and h2[0] is not None and h[3] < 0.06 and h2[3] < 0.06: inside += 1
a, b = cell(BP2[HI2]); xb = XB[a, b]
outer = {}
for k, i in enumerate(HI2):
    if np.isnan(xb[k]): continue
    key = (a[k], b[k]); outer[key] = min(outer.get(key, 9), BP2[i, 0])
poke = sum(1 for (aa, bb), xo in outer.items() if xo > XB[aa, bb] - 0.002)
R['tailhair'] = dict(max_shift=round(float((dd * wx).max()), 4), verts_shifted=int(((dd * wx) > 1e-4).sum()), hair_inside_tail=inside, columns_tail_outside_hair=poke, columns=len(outer))
print('FX tailhair', R['tailhair'])
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_assembly_f004.blend', relative_remap=True)
json.dump(R, open(ASM + 'fix_f004_report.json', 'w'), indent=1, default=float)
print('FX_DONE')
