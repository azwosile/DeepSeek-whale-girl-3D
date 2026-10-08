# 大肥鱼第二版 装配修复 f001：女仆装去实心 + 袖子对齐手臂 + 素体内收消穿模 + 胸前发束外推
import bpy, bmesh, glob, json, math, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
TMP = 'D:/DeepSeek Harness WorkSpace/Arena反代/_arena_tmp/v2fit/'
FIT = json.load(open(TMP + 'fit.json'))
SRC = glob.glob('D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/生成模型/大肥鱼女仆装/*.fbx')[0]
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_body_f001.blend')
sc = bpy.context.scene; body = bpy.data.objects['FISH2_body']
bpy.ops.import_scene.fbx(filepath=SRC)
outf = [o for o in sc.objects if o.type == 'MESH' and o != body][0]; outf.name = 'FISH2_outfit'; outf.data.name = 'FISH2_outfit'
s, tx, tz = FIT['s'], FIT['tx'], FIT['tz']
outf.data.transform(Matrix.Translation((tx, 0, tz)) @ Matrix.Scale(s, 4)); outf.data.update()
R = {}
def islands_bm(bm):
    bm.verts.ensure_lookup_table(); lab = [-1] * len(bm.verts); k = 0
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = k
        while st:
            a = st.pop()
            for e in a.link_edges:
                b = e.other_vert(a)
                if lab[b.index] < 0: lab[b.index] = k; st.append(b)
        k += 1
    return np.array(lab)
def body_skin_tree(Pc=None):
    bb = bmesh.new(); bb.from_mesh(body.data); bl = islands_bm(bb)
    if Pc is not None:
        for v in bb.verts: v.co = Pc[v.index]
    BP = np.array([v.co[:] for v in bb.verts])
    bid = max(set(bl.tolist()), key=lambda i: ((bl == i).sum() if BP[bl == i][:, 2].min() < 0.05 else 0))
    keep = bl == bid
    bmesh.ops.delete(bb, geom=[v for v in bb.verts if not keep[v.index]], context='VERTS')
    bb.normal_update(); return BVHTree.FromBMesh(bb), bl, bid
BT, BL, BID = body_skin_tree()
def sd_body(p):
    loc, n, i, d = BT.find_nearest(p); return (p - loc).dot(n), loc, n

# ---------- 1. hollow: remove skirt dome/floor + caps inside body ----------
bm = bmesh.new(); bm.from_mesh(outf.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
ol = islands_bm(bm); OP = np.array([v.co[:] for v in bm.verts])
ids, cnt = np.unique(ol, return_counts=True); skirt = ids[np.argmax(cnt)]
hem = OP[ol == skirt][:, 2].min()
fisl = np.array([ol[f.verts[0].index] for f in bm.faces])
OT = BVHTree.FromBMesh(bm)
dirs = [Vector((math.cos(a), math.sin(a), 0)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
band = set()
for f in bm.faces:
    if fisl[f.index] != skirt: continue
    c = f.calc_center_median()
    if not (hem + 0.06 < c.z < 1.03): continue
    hit = sum(1 for d in dirs if (lambda r: r[0] is not None and r[2] != f.index)(OT.ray_cast(c + d * 0.002, d, 1.0)))
    if hit >= 10: band.add(f.index)
seeds = set()
for x in np.arange(-0.08, 0.20, 0.02):
    for y in np.arange(-0.16, 0.17, 0.02):
        loc, n, fi, d = OT.ray_cast(Vector((x, y, 0.3)), Vector((0, 0, 1)), 1.0)
        if fi is not None and fi in band and n.z < -0.3: seeds.add(fi)
        if loc is not None:
            loc2, n2, fi2, d2 = OT.ray_cast(loc + Vector((0, 0, 1e-4)), Vector((0, 0, 1)), 0.3)
            if fi2 is not None and fi2 in band and n2.z > 0.3: seeds.add(fi2)
comp = set(seeds); fr = list(seeds)
while fr:
    f = bm.faces[fr.pop()]
    for e in f.edges:
        for g in e.link_faces:
            if g.index in comp or g.index not in band or g.calc_center_median().z < hem + 0.15: continue
            comp.add(g.index); fr.append(g.index)
# hole-fill small unselected patches enclosed by selection (skirt, above ruffles)
for it in range(2):
    seen = set()
    for f in bm.faces:
        if f.index in comp or f.index in seen or fisl[f.index] != skirt or f.calc_center_median().z < hem + 0.15: continue
        patch = {f.index}; st = [f]; open_ = False
        while st and len(patch) < 41:
            a = st.pop()
            for e in a.edges:
                if e.is_boundary: open_ = True
                for g in e.link_faces:
                    if g.index in comp or g.index in patch: continue
                    patch.add(g.index); st.append(g)
        seen |= patch
        if len(patch) <= 40 and not open_: comp |= patch
# visibility guard: keep faces that can see outside along any non-downward direction (exterior wall seen through gaps)
gold = math.pi * (3 - math.sqrt(5)); sph = []
for k in range(64):
    zz = 1 - 2 * (k + 0.5) / 64; rr = math.sqrt(1 - zz * zz); sph.append(Vector((math.cos(gold * k) * rr, math.sin(gold * k) * rr, zz)))
updirs = [d for d in sph if d.z > -0.3]
vis = set()
for fi in comp:
    f = bm.faces[fi]; c = f.calc_center_median()
    for d in updirs:
        if OT.ray_cast(c + d * 0.0015, d, 3.0)[0] is None: vis.add(fi); break
R['vis_kept'] = len(vis); comp -= vis
print('FX visible-from-outside kept', len(vis), 'remaining dome/floor', len(comp))
# caps inside body (non-skirt): near-horizontal faces whose centre is inside the skin
caps = set()
for f in bm.faces:
    if fisl[f.index] == skirt: continue
    c = f.calc_center_median()
    if abs(f.normal.z) > 0.6 and sd_body(c)[0] < -0.003: caps.add(f.index)
fr = list(caps)
while fr:
    f = bm.faces[fr.pop()]
    for e in f.edges:
        for g in e.link_faces:
            if g.index in caps or fisl[g.index] == skirt: continue
            c = g.calc_center_median()
            if abs(g.normal.z) > 0.4 and sd_body(c)[0] < -0.002:
                caps.add(g.index); fr.append(g.index)
# waist floor disc (non-skirt, z<1.045, horizontal, enclosed)
for f in bm.faces:
    if fisl[f.index] == skirt or f.index in caps: continue
    c = f.calc_center_median()
    if 0.95 < c.z < 1.045 and abs(f.normal.z) > 0.8:
        hit = sum(1 for d in dirs if (lambda r: r[0] is not None and r[2] != f.index)(OT.ray_cast(c + d * 0.002, d, 0.5)))
        if hit >= 10: caps.add(f.index)
dele = comp | caps
from collections import Counter
R['caps_by_island'] = {int(k): v for k, v in Counter(int(fisl[i]) for i in caps).most_common(12)}
print('FX capsisl', R['caps_by_island'])
R['hollow'] = dict(skirt_dome_floor=len(comp), caps_other=len(caps), deleted=len(dele), faces_before=len(bm.faces))
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in dele], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(outf.data); outf.data.update(); bm.free()
R['hollow']['faces_after'] = len(outf.data.polygons)
print('FX hollow', R['hollow'])

# ---------- 2. sleeves: align to arms ----------
me = outf.data; OP = np.array([v.co[:] for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); ol = islands_bm(bm); bm.free()
BP = np.array([v.co[:] for v in body.data.vertices]); skin = BL == BID
def centre(P, yv, side, zlim=(0.7, 1.45), xlim=(-0.3, 0.4)):
    m = (np.abs(P[:, 1] * side - yv) < 0.006) & (P[:, 2] > zlim[0]) & (P[:, 2] < zlim[1]) & (P[:, 0] > xlim[0]) & (P[:, 0] < xlim[1])
    return P[m].mean(0) if m.sum() >= 4 else None
R['sleeve'] = {}
for side in (1, -1):
    isl_ids = []
    for i in np.unique(ol):
        m = ol == i; q = OP[m]
        if (q[:, 1] * side).mean() > 0.165 and q[:, 2].max() < 1.34 and q[:, 2].min() > 0.75: isl_ids.append(i)
    sm = np.isin(ol, isl_ids)
    A0 = centre(BP[skin], 0.20, side); A1 = centre(BP[skin], 0.35, side)
    S0 = centre(OP[sm], 0.20, side); S1 = centre(OP[sm], 0.35, side)
    a = Vector(A1 - A0).normalized(); b = Vector(S1 - S0).normalized()
    rot = b.rotation_difference(a).to_matrix().to_4x4()
    M = Matrix.Translation(Vector(A0)) @ rot @ Matrix.Translation(-Vector(S0))
    # blend: verts near shoulder (|y|<0.17) move less (avoid tearing at bodice seam)
    for idx in np.where(sm)[0]:
        v = me.vertices[idx]; p = v.co.copy(); q = M @ p
        w = min(max((abs(p.y) - 0.15) / 0.06, 0.0), 1.0)
        v.co = p.lerp(q, w)
    ang = math.degrees(b.angle(a))
    R['sleeve']['L' if side > 0 else 'R'] = dict(parts=len(isl_ids), verts=int(sm.sum()), angle_deg=round(ang, 2), arm0=A0.round(3).tolist(), arm1=A1.round(3).tolist(), slv0=S0.round(3).tolist(), slv1=S1.round(3).tolist())
me.update()
print('FX sleeve', R['sleeve'])
OP = np.array([v.co[:] for v in me.vertices])
# outfit tree after edits
obm = bmesh.new(); obm.from_mesh(me); obm.normal_update(); OT = BVHTree.FromBMesh(obm)

# ---------- 3. body skin pull-in where it pokes through the outfit ----------
bme = body.data
CN = np.zeros((len(bme.vertices), 3))
for l, cn in zip(bme.loops, bme.corner_normals): CN[l.vertex_index] += cn.vector[:]
CN /= (np.linalg.norm(CN, axis=1, keepdims=True) + 1e-12)
VN = np.array([v.normal[:] for v in bme.vertices])
P = BP.copy(); D = np.zeros_like(P); poke = 0
covered = skin & (P[:, 2] > 0.95) & (P[:, 2] < 1.40)
for i in np.where(covered)[0]:
    p = Vector(P[i]); n = Vector(VN[i])
    loc, nn, fi, dist = OT.ray_cast(p + n * 1e-4, -n, 0.02)       # outfit just inside the skin => skin pokes out
    if loc is not None:
        D[i] = -n * (dist + 0.003); poke += 1
# also: skin within 2mm under the cloth -> ensure 3mm
for i in np.where(covered & (np.linalg.norm(D, axis=1) == 0))[0]:
    p = Vector(P[i]); n = Vector(VN[i])
    loc, nn, fi, dist = OT.ray_cast(p, n, 0.003)
    if loc is not None: D[i] = -n * (0.003 - dist)
nbr = [[] for _ in range(len(P))]
for e in bme.edges: a, b2 = e.vertices; nbr[a].append(b2); nbr[b2].append(a)
for it in range(6):
    D2 = D.copy()
    for i in np.where(covered)[0]:
        nb = [j for j in nbr[i] if skin[j]]
        if nb:
            avg = D[nb].mean(0)
            D2[i] = D[i] if np.linalg.norm(D[i]) >= np.linalg.norm(avg) else 0.5 * (D[i] + avg)
    D = D2
P2 = P + D
R['skin'] = dict(poke_verts=int(poke), moved=int((np.linalg.norm(D, axis=1) > 1e-5).sum()), max_mm=round(float(np.linalg.norm(D, axis=1).max()) * 1000, 1))
print('FX skin', R['skin'])

# ---------- 4. front hair locks: push out of the outfit ----------
locks = []
for i in np.unique(BL):
    if i == BID: continue
    q = P2[BL == i]
    if 300 < len(q) < 600 and q[:, 0].mean() > 0.08 and 0.04 < abs(q[:, 1].mean()) < 0.15 and q[:, 2].min() < 1.25: locks.append(i)
lm = np.isin(BL, locks); Dh = np.zeros_like(P2); need = 0
BT2 = None
bb = bmesh.new(); bb.from_mesh(bme)
for v in bb.verts: v.co = P2[v.index]
bmesh.ops.delete(bb, geom=[v for v in bb.verts if BL[v.index] != BID], context='VERTS'); bb.normal_update(); BT2 = BVHTree.FromBMesh(bb)
CLR = 0.006
for i in np.where(lm)[0]:
    p = Vector(P2[i])
    if p.z > 1.36: continue
    loc, n, fi, d = BT2.find_nearest(p)
    t_h = (p - loc).dot(n)
    hit = OT.ray_cast(loc + n * 1e-4, n, 0.08)
    if hit[0] is None: continue
    t_o = hit[3]
    # outer surface of cloth: continue through possible double layer
    h2 = OT.ray_cast(hit[0] + n * 1e-4, n, 0.01)
    if h2[0] is not None: t_o += 1e-4 + h2[3]
    req = t_o + CLR
    if t_h < req: Dh[i] = n * (req - t_h); need += 1
for it in range(10):
    D2 = Dh.copy()
    for i in np.where(lm)[0]:
        nb = nbr[i]
        if nb:
            avg = Dh[nb].mean(0)
            D2[i] = avg if np.linalg.norm(avg) > np.linalg.norm(Dh[i]) else 0.5 * (Dh[i] + avg)
    Dh = D2
# root falloff: no push above collar top
ztop = OP[:, 2].max()
fall = np.clip((ztop + 0.02 - P2[:, 2]) / 0.06, 0, 1)[:, None]
P3 = P2 + Dh * fall
R['locks'] = dict(islands=[int(i) for i in locks], verts=int(lm.sum()), needed=int(need), max_mm=round(float(np.linalg.norm(Dh * fall, axis=1).max()) * 1000, 1))
print('FX locks', R['locks'])
for i, v in enumerate(bme.vertices): v.co = P3[i]
bme.update()
# normals: keep original custom normals except where moved
GN = np.array([v.normal[:] for v in bme.vertices])
mv = np.linalg.norm(P3 - P, axis=1); wn = np.clip(mv / 0.002, 0, 1)
NN = CN * (1 - wn)[:, None] + GN * wn[:, None]; NN /= (np.linalg.norm(NN, axis=1, keepdims=True) + 1e-12)
bme.normals_split_custom_set_from_vertices([tuple(n) for n in NN])

# ---------- verify ----------
bb = bmesh.new(); bb.from_mesh(bme); bmesh.ops.delete(bb, geom=[v for v in bb.verts if BL[v.index] != BID], context='VERTS'); bb.normal_update(); BT3 = BVHTree.FromBMesh(bb)
OP = np.array([v.co[:] for v in me.vertices]); sds = []
for p in OP[::2]:
    loc, n, fi, d = BT3.find_nearest(Vector(p)); sds.append((Vector(p) - loc).dot(n))
sds = np.array(sds)
pk = 0
for i in np.where(covered)[0]:
    p = Vector(P3[i]); n = Vector(GN[i])
    if OT.ray_cast(p + n * 1e-4, -n, 0.02)[0] is not None: pk += 1
lk = 0
for i in np.where(lm & (P3[:, 2] < 1.30))[0]:
    p = Vector(P3[i]); loc, n, fi, d = BT3.find_nearest(p)
    h = OT.ray_cast(loc + n * 1e-4, n, 0.08)
    if h[0] is not None and (p - loc).dot(n) < h[3]: lk += 1
hands = [i for i in np.unique(BL) if i != BID and abs(P3[BL == i][:, 1].mean()) > 0.3 and (BL == i).sum() > 1000]
cuffs = {}
for side in (1, -1):
    m = (OP[:, 1] * side > 0.3); cuffs['L' if side > 0 else 'R'] = OP[m].mean(0).round(3).tolist()
R['verify'] = dict(outfit_inside_skin_pct=round(100 * float((sds < 0).mean()), 2), outfit_inside_gt5mm_pct=round(100 * float((sds < -0.005).mean()), 2),
                   skin_poke_verts_after=int(pk), lock_verts_still_under_cloth=int(lk),
                   hand_centres=[P3[BL == i].mean(0).round(3).tolist() for i in hands], cuff_centres=cuffs)
print('FX verify', R['verify'])
for o in (body, outf): o.select_set(False)
body['fix_notes_f002'] = 'f002: skin pulled 3mm under outfit where poking; front locks pushed >=6mm outside cloth'
outf['fix_notes'] = 'f001: fitted s=%.4f tx=%.4f tz=%.4f; skirt solid dome/floor + inner caps deleted; sleeves rotated to arms' % (s, tx, tz)
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_assembly_f001.blend')
bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
json.dump(R, open(ASM + 'fix_assembly_f001_report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('FX_DONE')
