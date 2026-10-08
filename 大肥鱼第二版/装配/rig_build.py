# 大肥鱼第二版 绑定 r001：骨架+权重+头发/鱼尾骨链+裙布料代理+姿势测试/慢跑动作
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_assembly_f004.blend')
sc = bpy.context.scene; OB = {o.name: o for o in sc.objects if o.type == 'MESH'}
body = OB['FISH2_body']; outf = OB['FISH2_outfit']
DL = json.load(open(ASM + 'assemble_acc_f003_report.json'))['pose']['lift_m']
R = {'lift': DL}
print('RB skin-z-range')
def V(o): return np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
def labels(me):
    n = len(me.vertices); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    return np.array([f(i) for i in range(n)])
BP = V(body); BL = labels(body.data)
skin = min(np.unique(BL), key=lambda i: BP[BL == i][:, 2].min())
S = BP[BL == skin]
print('RB skin', len(S), S[:,2].min(), S[:,2].max())
def sl(z, ymin=-1, ymax=1, xr=None, tol=0.008):
    m = (np.abs(S[:, 2] - z) < tol) & (S[:, 1] > ymin) & (S[:, 1] < ymax)
    return S[m]
# ---- landmarks ----
crotch = 0.81 + DL; hipz = crotch + 0.07
J = {}
for sd, nm in ((1, 'L'), (-1, 'R')):
    lo, hi = (0.01, 0.2) if sd > 0 else (-0.2, -0.01)
    q = sl(crotch - 0.05, lo, hi); hipc = q.mean(0)
    ank = sl(0.10 + DL, lo, hi).mean(0); ank[2] = 0.075 + DL + 0.0
    kz = 0.5 * (hipz + ank[2]) + 0.02; knee = sl(kz, lo, hi).mean(0); knee[0] += 0.01
    F = S[(S[:, 2] < 0.13) & (S[:, 1] * sd > 0.02) & (np.abs(S[:, 1]) < 0.2)]
    xq = np.quantile(F[:, 0], 0.8); ball = F[np.abs(F[:, 0] - xq) < 0.01].mean(0); ball[2] = max(ball[2], 0.03)
    toe = F[F[:, 0] > F[:, 0].max() - 0.01].mean(0)
    J['hip' + nm] = np.array([hipc[0], hipc[1] * 0.95, hipz]); J['knee' + nm] = knee; J['ankle' + nm] = ank; J['ball' + nm] = ball; J['toe' + nm] = toe
    A = S[(np.abs(S[:, 1]) > 0.2) & (np.abs(S[:, 1]) < 0.33) & (S[:, 1] * sd > 0) & (S[:, 2] > 0.9 + DL)]
    c = A.mean(0); _, _, vt = np.linalg.svd(A - c); d = vt[0] * np.sign(vt[0][1] * sd)
    def at_y(yv): t = (yv * sd - c[1] * sd) / (d[1] * sd); return c + d * t
    sh = at_y(0.165 * sd); sh[2] = max(sh[2], 1.236 + DL - 0.0259 + 0.0) if False else max(sh[2], 1.24)
    hand = np.array([-0.04, 0.422 * sd, 0.819 + DL])
    wr = hand - 0.06 * (hand - sh) / np.linalg.norm(hand - sh)
    el = sh + 0.52 * (wr - sh)
    near = A[np.linalg.norm(np.cross(A - el, d), axis=1) < 0.06]
    near = near[np.abs((near - el) @ d) < 0.02]
    if len(near) > 5: el = near.mean(0)
    el[0] -= 0.01
    J['shoulder' + nm] = sh; J['elbow' + nm] = el; J['wrist' + nm] = wr; J['hand' + nm] = hand + 0.05 * (hand - wr) / np.linalg.norm(hand - wr)
def spine_pt(z, f=0.42):
    q = sl(z, -0.12, 0.12)
    if len(q) < 8:
        m = (np.abs(BP[:, 2] - z) < 0.008) & (np.abs(BP[:, 1]) < 0.05); q = BP[m]
        print('RB spine fallback', z, len(q))
    return np.array([q[:, 0].min() + f * np.ptp(q[:, 0]), 0, z])
J['hips'] = spine_pt(hipz); J['spine'] = spine_pt(hipz + 0.12); J['chest'] = spine_pt(1.10 + DL); J['uchest'] = spine_pt(1.22 + DL)
qn = S[np.abs(S[:, 2] - 1.36) < 0.008]; J['neck'] = np.array([0.5 * (qn[:, 0].min() + qn[:, 0].max()), 0, 1.36 + 0.0])
J['head'] = np.array([J['neck'][0] - 0.005, 0, 1.45 + DL])
top = BP[:, 2].max(); J['headtop'] = np.array([J['head'][0], 0, 1.646 + DL - 0.0])
R['joints'] = {k: [round(float(x), 3) for x in v] for k, v in J.items()}
print('RB joints', R['joints'])
# ---- armature ----
arm = bpy.data.armatures.new('FISH2_rig'); rig = bpy.data.objects.new('FISH2_rig', arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
EB = arm.edit_bones
def bone(name, h, t, parent=None, conn=False, roll=0.0, deform=True):
    b = EB.new(name); b.head = Vector(h); b.tail = Vector(t); b.roll = roll
    if parent: b.parent = EB[parent]; b.use_connect = conn
    b.use_deform = deform; return b
bone('hips', J['hips'], J['spine']); bone('spine', J['spine'], J['chest'], 'hips', True); bone('chest', J['chest'], J['uchest'], 'spine', True)
bone('upper_chest', J['uchest'], J['neck'], 'chest', True); bone('neck', J['neck'], J['head'], 'upper_chest', True); bone('head', J['head'], J['headtop'], 'neck', True)
for nm, sd in (('L', 1), ('R', -1)):
    bone('shoulder.' + nm, J['uchest'] + np.array([0.02, 0.03 * sd, 0.07]), J['shoulder' + nm], 'upper_chest')
    bone('upper_arm.' + nm, J['shoulder' + nm], J['elbow' + nm], 'shoulder.' + nm, True)
    bone('forearm.' + nm, J['elbow' + nm], J['wrist' + nm], 'upper_arm.' + nm, True)
    bone('hand.' + nm, J['wrist' + nm], J['hand' + nm], 'forearm.' + nm, True)
    bone('thigh.' + nm, J['hip' + nm], J['knee' + nm], 'hips')
    bone('shin.' + nm, J['knee' + nm], J['ankle' + nm], 'thigh.' + nm, True)
    bone('foot.' + nm, J['ankle' + nm], J['ball' + nm], 'shin.' + nm, True)
    bone('toe.' + nm, J['ball' + nm], J['toe' + nm], 'foot.' + nm, True)
# consistent rolls: limbs bend axis
bpy.ops.armature.select_all(action='SELECT'); bpy.ops.armature.calculate_roll(type='GLOBAL_POS_X')
bpy.ops.object.mode_set(mode='OBJECT')
BODY_BONES = [b.name for b in arm.bones]
# ---- hair chains ----
hair_isl = []
for i in np.unique(BL):
    q = BP[BL == i]
    if i != skin and len(q) > 300 and q[:, 2].max() > 1.40 + DL and q[:, 2].min() < 1.30 + DL: hair_isl.append(i)
headc = J['head'] + np.array([0, 0, 0.08])
chains = []   # (name, parent, joints list, vertex mask, member weights fn)
for i in hair_isl:
    q = BP[BL == i]; idx = np.where(BL == i)[0]
    rootz = min(1.47 + DL, q[:, 2].max() - 0.03)
    if np.ptp(q[:, 1]) > 0.2:      # big back hair -> split by angle
        low = idx[BP[idx, 2] < rootz]
        ang = np.arctan2(BP[low, 1], BP[low, 0] - headc[0]); ang = np.mod(ang, 2 * np.pi)
        K = 7; cs = np.quantile(ang, np.linspace(0.5 / K, 1 - 0.5 / K, K))
        for it in range(10):
            lab = np.argmin(np.abs(ang[:, None] - cs[None, :]), 1)
            cs = np.array([ang[lab == k].mean() if (lab == k).any() else cs[k] for k in range(K)])
        sig = np.median(np.diff(np.sort(cs))) * 0.6
        for k in range(K):
            mem = low[lab == k]; zmin = BP[mem, 2].min()
            zs = np.linspace(rootz, zmin + 0.01, 5); pts = []
            for z in zs:
                mm = mem[np.abs(BP[mem, 2] - z) < 0.02]
                pts.append(BP[mm].mean(0) if len(mm) else (pts[-1] - [0, 0, 0.05] if pts else BP[mem].mean(0)))
            pts[0][2] = rootz
            chains.append(dict(name='hair_B%d' % k, parent='head', pts=np.array(pts), island=i, ang=cs[k], sig=sig, kind='back'))
    else:
        nm = 'hair_F' + ('L' if q[:, 1].mean() > 0 else 'R')
        zs = np.linspace(rootz, q[:, 2].min() + 0.01, 5); pts = []
        for z in zs:
            mm = idx[np.abs(BP[idx, 2] - z) < 0.02]; pts.append(BP[mm].mean(0) if len(mm) else pts[-1] - [0, 0, 0.05])
        chains.append(dict(name=nm, parent='head', pts=np.array(pts), island=i, kind='lock'))
# tail chain
tl = OB['FISH2_tail']; TP = V(tl)
zs = np.linspace(TP[:, 2].max() - 0.01, TP[:, 2].min() + 0.02, 6); pts = []
for z in zs:
    mm = np.abs(TP[:, 2] - z) < 0.02; pts.append(TP[mm].mean(0))
chains.append(dict(name='tail', parent='hips', pts=np.array(pts), kind='tail'))
bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
    prev = c['parent']
    for j in range(len(c['pts']) - 1):
        nm = '%s_%d' % (c['name'], j)
        bone(nm, c['pts'][j], c['pts'][j + 1], prev, j > 0); prev = nm
    c['bones'] = ['%s_%d' % (c['name'], j) for j in range(len(c['pts']) - 1)]
bpy.ops.object.mode_set(mode='OBJECT')
R['chains'] = {c['name']: len(c['bones']) for c in chains}
print('RB chains', R['chains'])
# ---- body weights: auto heat on body bones ----
for b in arm.bones: b.use_deform = b.name in BODY_BONES
sk_idx = np.where(BL == skin)[0]
sko = body.copy(); sko.data = body.data.copy(); sc.collection.objects.link(sko); sko.vertex_groups.clear(); sko.modifiers.clear()
bm = bmesh.new(); bm.from_mesh(sko.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if BL[v.index] != skin], context='VERTS'); bm.to_mesh(sko.data); bm.free()
assert len(sko.data.vertices) == len(sk_idx)
bpy.ops.object.select_all(action='DESELECT'); sko.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
body.vertex_groups.clear()
for g in sko.vertex_groups: body.vertex_groups.new(name=g.name)
for v in sko.data.vertices:
    for g in v.groups:
        body.vertex_groups[sko.vertex_groups[g.group].name].add([int(sk_idx[v.index])], g.weight, 'REPLACE')
bpy.data.objects.remove(sko)
body.parent = rig; mb = body.modifiers.new('rig', 'ARMATURE'); mb.object = rig
for b in arm.bones: b.use_deform = True
VG = body.vertex_groups
def wsum(o):
    W = np.zeros(len(o.data.vertices))
    for v in o.data.vertices:
        for g in v.groups: W[v.index] += g.weight
    return W
W = wsum(body); zero = np.where(W < 1e-4)[0]
R['auto_zero_verts'] = int(len(zero)); R['auto_zero_skin'] = int(np.isin(zero, np.where(BL == skin)[0]).sum())
# fallback: nearest bone segment for unweighted verts (non-hair)
segs = [(b.name, np.array(b.head_local), np.array(b.tail_local)) for b in arm.bones if b.name in BODY_BONES]
def nearest_bone(p):
    best = None
    for nm, h, t in segs:
        d = t - h; u = np.clip(np.dot(p - h, d) / np.dot(d, d), 0, 1); dist = np.linalg.norm(p - (h + u * d))
        if best is None or dist < best[0]: best = (dist, nm)
    return best[1]
for i in zero:
    g = VG.get(nearest_bone(BP[i])) or VG.new(name=nearest_bone(BP[i])); g.add([int(i)], 1.0, 'REPLACE')
# head-attached islands (non-skin above neck): rigid to head
for i in np.unique(BL):
    if i == skin or i in hair_isl: continue
    q = BP[BL == i]
    if q[:, 2].min() > J['neck'][2] - 0.02:
        idx = [int(x) for x in np.where(BL == i)[0]]
        for g in VG: g.remove(idx)
        (VG.get('head') or VG.new(name='head')).add(idx, 1.0, 'REPLACE')
# hair chain weights
def chain_w(P, pts, bones):
    # returns (n, nb) weights by projection param along the polyline (by z)
    zs = pts[:, 2]; nb = len(bones); Wc = np.zeros((len(P), nb))
    for k in range(len(P)):
        z = P[k, 2]
        if z >= zs[0]: Wc[k, 0] = 1; continue
        if z <= zs[-1]: Wc[k, -1] = 1; continue
        j = np.searchsorted(-zs, -z) - 1; j = min(max(j, 0), nb - 1)
        t = (zs[j] - z) / max(zs[j] - zs[j + 1], 1e-6)
        mid = 0.5
        if t < mid and j > 0: Wc[k, j] = 0.5 + t; Wc[k, j - 1] = 0.5 - t
        elif t >= mid and j < nb - 1: Wc[k, j] = 1.5 - t; Wc[k, j + 1] = t - 0.5
        else: Wc[k, j] = 1
    return Wc
for i in hair_isl:
    idx = np.where(BL == i)[0]; P = BP[idx]
    cs = [c for c in chains if c.get('island') == i]
    for g in VG: g.remove([int(x) for x in idx])
    rootz = cs[0]['pts'][0][2]
    hw = np.clip((P[:, 2] - (rootz - 0.03)) / 0.06, 0, 1)        # head share near root
    if cs[0]['kind'] == 'back':
        ang = np.mod(np.arctan2(P[:, 1], P[:, 0] - headc[0]), 2 * np.pi)
        A = np.stack([np.exp(-((ang - c['ang']) / c['sig']) ** 2) for c in cs], 1); A /= A.sum(1, keepdims=True) + 1e-9
    else: A = np.ones((len(P), 1))
    for ci, c in enumerate(cs):
        Wc = chain_w(P, c['pts'], c['bones'])
        for bj, bn in enumerate(c['bones']):
            w = (1 - hw) * A[:, ci] * Wc[:, bj]; g = VG.get(bn) or VG.new(name=bn)
            for k in np.where(w > 1e-3)[0]: g.add([int(idx[k])], float(w[k]), 'REPLACE')
    gh = VG.get('head')
    for k in np.where(hw > 1e-3)[0]: gh.add([int(idx[k])], float(hw[k]), 'REPLACE')
# ---- accessories: rigid / chain ----
def rigid(o, bn):
    o.vertex_groups.clear(); g = o.vertex_groups.new(name=bn); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    m = o.modifiers.new('rig', 'ARMATURE'); m.object = rig; o.parent = rig
for nm in ('FISH2_headband', 'FISH2_bow_side', 'FISH2_bow_back'): rigid(OB[nm], 'head')
rigid(OB['FISH2_shoe_L'], 'foot.L'); rigid(OB['FISH2_shoe_R'], 'foot.R')
for side in ('L', 'R'):   # toe part of shoe to toe bone
    o = OB['FISH2_shoe_' + side]; P = V(o); bx = J['ball' + side][0]
    gt = o.vertex_groups.new(name='toe.' + side); gf = o.vertex_groups['foot.' + side]
    for k in np.where(P[:, 0] > bx - 0.01)[0]:
        t = float(np.clip((P[k, 0] - bx + 0.01) / 0.03, 0, 1)); gt.add([int(k)], t, 'REPLACE'); gf.add([int(k)], 1 - t, 'REPLACE')
tc = [c for c in chains if c['name'] == 'tail'][0]
tl.vertex_groups.clear(); Wc = chain_w(TP, tc['pts'], tc['bones'])
for bj, bn in enumerate(tc['bones']):
    g = tl.vertex_groups.new(name=bn)
    for k in np.where(Wc[:, bj] > 1e-3)[0]: g.add([int(k)], float(Wc[k, bj]), 'REPLACE')
m = tl.modifiers.new('rig', 'ARMATURE'); m.object = rig; tl.parent = rig
# ---- outfit: weights from skin (non-skirt) + skirt zone group ----
OP = V(outf); OLb = labels(outf.data)
waist = 1.04 + DL
sleeve = np.zeros(len(OP), bool)
for i in np.unique(OLb):
    q = OP[OLb == i]
    if q[:, 1].min() * q[:, 1].max() > 0 and np.abs(q[:, 1]).mean() > 0.15 and q[:, 2].max() < 1.34 + DL and q[:, 2].min() > 0.78: sleeve[OLb == i] = True
skirt_w = np.clip((waist + 0.02 - OP[:, 2]) / 0.06, 0, 1); skirt_w[sleeve] = 0
skin_obj = body.copy(); skin_obj.data = body.data.copy(); sc.collection.objects.link(skin_obj)
bm = bmesh.new(); bm.from_mesh(skin_obj.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if BL[v.index] != skin], context='VERTS'); bm.to_mesh(skin_obj.data); bm.free()
outf.vertex_groups.clear()
for g in skin_obj.vertex_groups: outf.vertex_groups.new(name=g.name)
dt = outf.modifiers.new('dt', 'DATA_TRANSFER'); dt.object = skin_obj; dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = outf; bpy.ops.object.modifier_apply(modifier='dt')
bpy.data.objects.remove(skin_obj)
for g in outf.vertex_groups:
    for v in outf.data.vertices:
        if skirt_w[v.index] > 0:
            try:
                w = g.weight(v.index); g.add([v.index], w * (1 - skirt_w[v.index]), 'REPLACE')
            except RuntimeError: pass
# strip arm weights from non-sleeve torso garment parts (arms hang near back waist -> wrong nearest-skin transfer)
ARMB = [n for n in BODY_BONES if n.startswith(('forearm', 'hand'))]; UPB = [n for n in BODY_BONES if n.startswith('upper_arm')]
fixed = 0
for v in outf.data.vertices:
    if sleeve[v.index]: continue
    strip = set(ARMB) | (set(UPB) if OP[v.index, 2] < 1.17 + DL else set())
    gs_ = [(outf.vertex_groups[g.group].name, g.weight) for g in v.groups]
    bad = [n for n, w in gs_ if n in strip and w > 0]
    if not bad: continue
    fixed += 1
    for n in bad: outf.vertex_groups[n].remove([v.index])
    rest = [(n, w) for n, w in gs_ if n not in strip and n in BODY_BONES and w > 0]
    tot = sum(w for _, w in rest)
    if tot < 1e-4:
        outf.vertex_groups['spine' if OP[v.index, 2] > hipz + 0.06 else 'hips'].add([v.index], 1.0, 'REPLACE')
    else:
        for n, w in rest: outf.vertex_groups[n].add([v.index], w / tot, 'REPLACE')
R['outfit_arm_stripped'] = fixed; print('RB stripped', fixed)
# skirt zone: keep it following hips at least (weight 1-skirt_w handled), and the zone itself to hips for rest following
gs = outf.vertex_groups.new(name='skirt_zone')
for k in np.where(skirt_w > 0)[0]: gs.add([int(k)], float(skirt_w[k]), 'REPLACE')
gh = outf.vertex_groups.get('hips') or outf.vertex_groups.new(name='hips')
for k in np.where(skirt_w > 0)[0]:
    try: w0 = gh.weight(int(k))
    except RuntimeError: w0 = 0
    gh.add([int(k)], w0 + float(skirt_w[k]) * 0.0, 'REPLACE')
outf.parent = rig
m = outf.modifiers.new('rig', 'ARMATURE'); m.object = rig
# ---- skirt cloth proxy ----
sk_isl = max([i for i in np.unique(OLb) if OP[OLb == i][:, 1].min() < -0.1 and OP[OLb == i][:, 1].max() > 0.1 and OP[OLb == i][:, 2].max() < waist + 0.05],
             key=lambda i: (OLb == i).sum())
SKV = np.where(OLb == sk_isl)[0]
bm = bmesh.new(); bm.from_mesh(outf.data); bm.transform(outf.matrix_world); bm.verts.ensure_lookup_table()
keep = set(int(i) for i in SKV)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
OT = BVHTree.FromBMesh(bm); bm.free()
SK = OP[SKV]; hem = SK[:, 2].min(); print('RB skirt island', sk_isl, len(SKV), 'hem', hem); axis_x = float(SK[:, 0].mean())
NSEG, NR = 48, 16
zs = np.linspace(waist - 0.01, hem - 0.015, NR)
axs = []
for z in zs:
    q = SK[np.abs(SK[:, 2] - z) < 0.015]
    axs.append(0.5 * (q[:, 0].min() + q[:, 0].max()) if len(q) > 10 else np.nan)
axs = np.array(axs); good = ~np.isnan(axs); axs = np.interp(np.arange(NR), np.where(good)[0], axs[good])
axs = np.convolve(np.pad(axs, 1, mode='edge'), [0.25, 0.5, 0.25], 'valid')
th = 2 * np.pi * np.arange(NSEG) / NSEG
RAD = np.full((NR, NSEG), np.nan)
for r, z in enumerate(zs):
    for k in range(NSEG):
        d = Vector((math.cos(th[k]), math.sin(th[k]), 0)); o = Vector((axs[r], 0, z))
        h = OT.ray_cast(o + d * 0.8, -d, 0.8)
        if h[0] is not None: RAD[r, k] = 0.8 - h[3]
# fill + low-pass each ring (Fourier <= 4), then monotone flare + smooth along z
for r in range(NR):
    row = RAD[r]; g = ~np.isnan(row)
    if g.sum() < 6: RAD[r] = RAD[r - 1] if r else 0.15; continue
    row = np.interp(th, th[g], row[g], period=2 * np.pi)
    F = np.fft.rfft(row); F[5:] = 0; RAD[r] = np.fft.irfft(F, NSEG)
for r in range(1, NR): RAD[r] = np.maximum(RAD[r], RAD[r - 1])
for it in range(2):
    RAD[1:-1] = 0.25 * RAD[:-2] + 0.5 * RAD[1:-1] + 0.25 * RAD[2:]
R['proxy_radius_range'] = [float(RAD.min()), float(RAD.max())]
pverts = []; pfaces = []
for r in range(NR):
    for k in range(NSEG):
        rr = max(RAD[r, k] - 0.006, 0.05)
        pverts.append(Vector((axs[r] + rr * math.cos(th[k]), rr * math.sin(th[k]), zs[r])))
for r in range(NR - 1):
    for s_ in range(NSEG):
        a = r * NSEG + s_; b = r * NSEG + (s_ + 1) % NSEG; pfaces.append((a, b, b + NSEG, a + NSEG))
pm = bpy.data.meshes.new('FISH2_skirt_proxy'); pm.from_pydata([tuple(v) for v in pverts], [], pfaces); pm.update()
px = bpy.data.objects.new('FISH2_skirt_proxy', pm); sc.collection.objects.link(px); px.parent = rig
gpin = px.vertex_groups.new(name='pin'); ghp = px.vertex_groups.new(name='hips')
for k in range(len(pverts)):
    r = k // NSEG; w = [1.0, 0.75, 0.35][r] if r < 3 else 0.0
    if w > 0: gpin.add([k], w, 'REPLACE')
    ghp.add([k], 1.0, 'REPLACE')
pa = px.modifiers.new('rig', 'ARMATURE'); pa.object = rig
cl = px.modifiers.new('cloth', 'CLOTH'); cs_ = cl.settings
cs_.quality = 10; cs_.mass = 0.3; cs_.tension_stiffness = 25; cs_.compression_stiffness = 25; cs_.shear_stiffness = 15; cs_.bending_stiffness = 4.0
cs_.air_damping = 1.5; cs_.vertex_group_mass = 'pin'; cs_.pin_stiffness = 1.0
cs_.tension_damping = 8; cs_.compression_damping = 8; cs_.bending_damping = 2.0
cl.collision_settings.use_self_collision = False; cl.collision_settings.distance_min = 0.012; cl.collision_settings.collision_quality = 5
cl.point_cache.frame_start = 1; cl.point_cache.frame_end = 230
px.hide_render = True; px.display_type = 'WIRE'
# leg collision capsules
for side in ('L', 'R'):
    for bn, rad in (('thigh.' + side, 0.08), ('shin.' + side, 0.06)):
        b = arm.bones[bn]; L = (b.tail_local - b.head_local).length
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=rad, depth=L * 1.05)
        cy = bpy.context.active_object; cy.name = 'COL_' + bn
        cy.matrix_world = Matrix.Translation((b.head_local + b.tail_local) / 2) @ (b.tail_local - b.head_local).to_track_quat('Z', 'Y').to_matrix().to_4x4()
        cy.parent = rig; cy.parent_type = 'BONE'; cy.parent_bone = bn
        cy.matrix_parent_inverse = (rig.matrix_world @ Matrix.Translation(b.tail_local) @ b.matrix_local.to_3x3().to_4x4()).inverted()
        cy.modifiers.new('col', 'COLLISION'); cy.collision.thickness_outer = 0.02; cy.hide_render = True; cy.display_type = 'WIRE'
# hips collision too
sd_ = outf.modifiers.new('skirt', 'SURFACE_DEFORM'); sd_.target = px; sd_.vertex_group = 'skirt_zone'; sd_.falloff = 4
bpy.context.view_layer.objects.active = outf; sc.frame_set(1)
bpy.ops.object.surfacedeform_bind(modifier='skirt'); bpy.context.view_layer.update(); outf.evaluated_get(bpy.context.evaluated_depsgraph_get())
R['skirt_proxy'] = dict(verts=len(pverts), rings=NR, segs=NSEG, axis_x=round(axis_x, 3), hem=round(float(hem), 3), bound=sd_.is_bound)
print('RB proxy', R['skirt_proxy'])
# ---- animation: pose tests + jog ----
sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = 230
rig.animation_data_create(); act = bpy.data.actions.new('FISH2_posetest_jog'); rig.animation_data.action = act
PB = rig.pose.bones
for pb in PB: pb.rotation_mode = 'QUATERNION'
def wq(bn, axis, deg):
    b = arm.bones[bn]; Mr = b.matrix_local.to_quaternion()
    return Mr.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ Mr
def key(f, poses, loc=None):
    for pb in PB:
        if pb.name.startswith(('hair_', 'tail_')): continue
        pb.rotation_quaternion = Quaternion()
        for bn, ax, dg in poses.get(pb.name, []): pb.rotation_quaternion = pb.rotation_quaternion @ wq(bn, ax, dg)
        pb.keyframe_insert('rotation_quaternion', frame=f)
    PB['hips'].location = Vector(loc) if loc else Vector()
    PB['hips'].keyframe_insert('location', frame=f)
def P(**kw): return {k.replace('_L', '.L').replace('_R', '.R'): v for k, v in kw.items()}
key(1, {}); key(10, {})
key(20, {'head': [('head', (0, 0, 1), 28)], 'neck': [('neck', (0, 0, 1), 12)]})
key(28, {})
key(40, {'upper_arm.L': [('upper_arm.L', (1, 0, 0), 65)], 'upper_arm.R': [('upper_arm.R', (1, 0, 0), -65)]})
key(48, {})
key(60, {'forearm.L': [('forearm.L', (0, 1, 0), -90)], 'forearm.R': [('forearm.R', (0, 1, 0), -90)]})
key(68, {})
key(80, {'thigh.L': [('thigh.L', (0, 1, 0), -55)], 'shin.L': [('shin.L', (0, 1, 0), 95)]})
key(92, {})
# jog f100-228 (period 16)
for k, f in enumerate(range(100, 229, 4)):
    ph = (k % 4) / 4.0 * 2 * math.pi
    sw = math.sin(ph); up = abs(math.cos(ph))
    pose = {'thigh.L': [('thigh.L', (0, 1, 0), -28 * sw)], 'thigh.R': [('thigh.R', (0, 1, 0), 28 * sw)],
            'shin.L': [('shin.L', (0, 1, 0), 25 + 35 * max(0, sw))], 'shin.R': [('shin.R', (0, 1, 0), 25 + 35 * max(0, -sw))],
            'upper_arm.L': [('upper_arm.L', (0, 1, 0), 30 * sw)], 'upper_arm.R': [('upper_arm.R', (0, 1, 0), -30 * sw)],
            'forearm.L': [('forearm.L', (0, 1, 0), -50)], 'forearm.R': [('forearm.R', (0, 1, 0), -50)],
            'spine': [('spine', (0, 0, 1), 8 * sw)], 'hips': [('hips', (0, 0, 1), -6 * sw)]}
    key(f, pose, (0, 0, 0.03 * up - 0.02))
for fc in act.fcurves if hasattr(act, 'fcurves') else []:
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
R['frames'] = dict(head_turn=20, arm_raise=40, elbow_bend=60, knee_bend=80, jog='100-228')
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_rig_r002.blend')
bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
json.dump(R, open(ASM + 'rig_r002_report.json', 'w'), indent=1, default=float)
print('RB_DONE')
