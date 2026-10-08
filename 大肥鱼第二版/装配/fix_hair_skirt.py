# f001b: 所有发束（非皮肤/手/鞋）推出女仆装外层；沿发束平滑传播，保持形状
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_assembly_f001.blend')
body = bpy.data.objects['FISH2_body']; outf = bpy.data.objects['FISH2_outfit']; me = body.data
def islands(me):
    n = len(me.vertices); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    return np.array([f(i) for i in range(n)])
BL = islands(me); P = np.array([v.co[:] for v in me.vertices])
u = np.unique(BL)
skin = max(u, key=lambda i: (BL == i).sum() if P[BL == i][:, 2].min() < 0.05 else 0)
hair = []
for i in u:
    if i == skin: continue
    q = P[BL == i]
    if len(q) < 60 or q[:, 2].min() > 1.33 or q[:, 2].max() < 1.2: continue   # strands from head down past collar
    if abs(q[:, 1].mean()) > 0.3 and q[:, 2].max() < 1.0: continue          # hands
    hair.append(i)
hm = np.isin(BL, hair)
bb = bmesh.new(); bb.from_mesh(me); bmesh.ops.delete(bb, geom=[v for v in bb.verts if BL[v.index] != skin], context='VERTS'); bb.normal_update(); BT = BVHTree.FromBMesh(bb)
ob = bmesh.new(); ob.from_mesh(outf.data); ob.normal_update(); OT = BVHTree.FromBMesh(ob)
CLR = 0.006; D = np.zeros_like(P); bad = []
for i in np.where(hm & (P[:, 2] < 1.33))[0]:
    p = Vector(P[i]); loc, n, fi, d = BT.find_nearest(p)
    # horizontalise direction below the waist (skirt bell) to avoid pushing up/down
    if p.z < 1.05: n = Vector((n.x, n.y, 0)).normalized() if Vector((n.x, n.y)).length > 1e-3 else n
    t_h = (p - loc).dot(n)
    # outermost cloth layer along the ray within 0.2 m
    t_o = None; o = loc + n * 1e-4; acc = 0
    for k in range(4):
        h = OT.ray_cast(o, n, 0.2 - acc)
        if h[0] is None: break
        acc += h[3]; o = h[0] + n * 1e-4; acc += 1e-4
        if t_o is None or acc - t_o < 0.03: t_o = acc        # consecutive layers close together = same garment
        else: break
    if t_o is None: continue
    if t_h < t_o + CLR and t_h > t_o - 0.10:      # under the cloth but near it (hair inside skirt within 10cm)
        D[i] = n * (t_o + CLR - t_h); bad.append(i)
before = len(bad)
nbr = [[] for _ in range(len(P))]
for e in me.edges: a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
# propagate along strand: neighbours take 0.85*max of neighbours (keeps strand continuous), then light smoothing
for it in range(40):
    D2 = D.copy()
    for i in np.where(hm)[0]:
        nb = nbr[i]
        if not nb: continue
        m = D[nb]; j = np.argmax(np.linalg.norm(m, axis=1)); cand = m[j] * 0.93
        if np.linalg.norm(cand) > np.linalg.norm(D[i]): D2[i] = cand
    D = D2
for it in range(4):
    D2 = D.copy()
    for i in np.where(hm)[0]:
        if nbr[i]: D2[i] = 0.5 * D[i] + 0.5 * D[nbr[i]].mean(0)
    D = np.maximum(np.linalg.norm(D2, axis=1), 0)[:, None] * 0 + D2
# no push near scalp / above collar
fall = np.clip((1.36 - P[:, 2]) / 0.08, 0, 1)[:, None]
D *= fall
P2 = P + D
for i, v in enumerate(me.vertices): v.co = P2[i]
me.update()
CN = np.zeros((len(P), 3))
for l, cn in zip(me.loops, me.corner_normals): CN[l.vertex_index] += cn.vector[:]
CN /= np.linalg.norm(CN, axis=1, keepdims=True) + 1e-12
me.normals_split_custom_set_from_vertices([tuple(n) for n in CN])
# verify
after = 0
for i in np.where(hm & (P2[:, 2] < 1.30))[0]:
    p = Vector(P2[i]); loc, n, fi, d = BT.find_nearest(p)
    if p.z < 1.05 and Vector((n.x, n.y)).length > 1e-3: n = Vector((n.x, n.y, 0)).normalized()
    h = OT.ray_cast(loc + n * 1e-4, n, 0.2)
    if h[0] is not None and (p - loc).dot(n) < h[3] and (p - loc).dot(n) > h[3] - 0.10: after += 1
R = dict(hair_islands=len(hair), hair_verts=int(hm.sum()), under_cloth_before=before, after=after,
         moved=int((np.linalg.norm(D, axis=1) > 1e-4).sum()), max_mm=round(float(np.linalg.norm(D, axis=1).max()) * 1000, 1),
         p95_mm=round(float(np.percentile(np.linalg.norm(D[np.linalg.norm(D, axis=1) > 1e-4], axis=1), 95)) * 1000, 1) if (np.linalg.norm(D, axis=1) > 1e-4).any() else 0)
print('HS', R)
body['fix_notes_f002'] = str(body.get('fix_notes_f002', '')) + '; hair strands pushed outside outfit (6mm), propagated along strand'
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_assembly_f002.blend')
json.dump(R, open(ASM + 'fix_hair_skirt_f002_report.json', 'w'), indent=1)
print('HS_DONE')
