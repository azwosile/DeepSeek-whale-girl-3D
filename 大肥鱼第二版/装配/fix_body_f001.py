import bpy, bmesh, glob, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SRC = glob.glob('D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/生成模型/大肥鱼素体/*.fbx')[0]
OUTD = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
REN = 'D:/DeepSeek Harness WorkSpace/Arena反代/_arena_tmp/v2fix/'
os.makedirs(OUTD, exist_ok=True); os.makedirs(REN, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
ob.name = 'FISH2_body'; ob.data.name = 'FISH2_body'
me = ob.data
P = np.array([v.co[:] for v in me.vertices]); N0 = len(P)
CN = np.zeros((N0, 3))
for l, cn in zip(me.loops, me.corner_normals): CN[l.vertex_index] += cn.vector[:]
CN /= (np.linalg.norm(CN, axis=1, keepdims=True) + 1e-12)
# islands
E = np.array([e.vertices[:] for e in me.edges])
par = np.arange(N0)
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for a, b in E:
    ra, rb = find(a), find(b)
    if ra != rb: par[ra] = rb
isl = np.array([find(i) for i in range(N0)])
ids, cnt = np.unique(isl, return_counts=True)
info = {}
for i, c in zip(ids, cnt):
    m = isl == i; info[i] = dict(n=int(c), mn=P[m].min(0), mx=P[m].max(0))
body_id = max([i for i in ids if info[i]['mn'][2] < -0.45 and info[i]['mx'][2] > 0.2], key=lambda i: info[i]['n'])
hair_ids = [i for i in ids if i != body_id and info[i]['mn'][2] < 0.15 and info[i]['mn'][2] > -0.4 and abs(info[i]['mn'][1] + info[i]['mx'][1]) / 2 < 0.15 and info[i]['n'] > 500]
print('BODY', body_id, info[body_id]['n'], 'HAIR', [(int(i), info[i]['n'], info[i]['mn'].round(3).tolist(), info[i]['mx'].round(3).tolist()) for i in hair_ids])
body = isl == body_id
nbr = [[] for _ in range(N0)]
for a, b in E: nbr[a].append(b); nbr[b].append(a)

# ---------- renders setup ----------
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.8, 0.8, 0.8); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
sc.display.shading.curvature_ridge_factor = 1.5; sc.display.shading.curvature_valley_factor = 1.5
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.3, 0.32, 0.36)
sc.render.image_settings.file_format = 'JPEG'; sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
def look(d, t, o, name):
    d = Vector(d).normalized(); t = Vector(t); cam.location = t + d * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = o
    sc.render.filepath = REN + name; bpy.ops.render.render(write_still=True)
shots = [('chest', (1, 0, 0), (0.05, 0, 0.2), 0.2), ('chest34', (0.8, 0.6, 0.15), (0.05, 0, 0.2), 0.2),
         ('chestside', (0, 1, 0), (0.05, 0, 0.2), 0.2),
         ('hip_side', (0, 1, 0), (-0.03, 0, 0.07), 0.22), ('hip_back34', (-0.7, 0.7, -0.1), (-0.03, 0, 0.07), 0.22),
         ('hip_under', (-0.5, 0.3, -0.8), (-0.04, 0, 0.06), 0.22), ('back', (-1, 0, 0), (0, 0, 0.12), 0.5), ('side_full', (0, 1, 0), (0.02, 0, 0.15), 0.4)]
def shoot(tag):
    for nm, d, t, o in shots: look(d, t, o, f'{tag}_{nm}.jpg')
shoot('before')
sc.render.resolution_x = sc.render.resolution_y = 600

def bodytree(Pc):
    bm = bmesh.new(); vm = {}
    for i in np.where(body)[0]: vm[i] = bm.verts.new(Pc[i])
    for f in me.polygons:
        vs = f.vertices[:]
        if body[vs[0]]:
            try: bm.faces.new([vm[i] for i in vs])
            except ValueError: pass
    bm.normal_update(); return BVHTree.FromBMesh(bm), bm
def clearance(Pc, idx):
    t, bm = bodytree(Pc); out = []
    for i in idx:
        loc, nrm, fi, dist = t.find_nearest(Vector(Pc[i]))
        s = (Vector(Pc[i]) - loc).dot(nrm); out.append((s, np.array(nrm[:])))
    bm.free(); return out

# ---------- 1. chest crease: low-pass the normal height field (no tangential motion) ----------
Q = P.copy()
bidx = np.where(body)[0]
c0 = np.array([0.095, 0.0, 0.185]); rad = np.array([0.08, 0.105, 0.045])
r = np.sqrt((((P - c0) / rad) ** 2).sum(1))
w = np.where(body & (P[:, 0] > 0.03), np.clip((1 - r) / 0.6, 0, 1), 0.0); w = w * w * (3 - 2 * w)
act = np.where(r < 1.6)[0]; act = act[body[act]]
bnb = {i: [j for j in nbr[i] if body[j]] for i in act}
B = P.copy()
for it in range(40):
    B2 = B.copy()
    for i in act:
        if bnb[i]: B2[i] = B[i] + 0.5 * (B[bnb[i]].mean(0) - B[i])
    B = B2
# vertex normals of the base surface
FN = np.zeros_like(P)
for f in me.polygons:
    vs = list(f.vertices)
    if not body[vs[0]]: continue
    pts = B[vs]; n = np.zeros(3)
    for k in range(len(vs)): n += np.cross(pts[k], pts[(k + 1) % len(vs)])
    FN[vs] += n
nrm = FN / (np.linalg.norm(FN, axis=1, keepdims=True) + 1e-12)
h = ((P - B) * nrm).sum(1)
hs = h.copy()
for it in range(100):
    h2 = hs.copy()
    for i in act:
        if bnb[i]: h2[i] = hs[i] + 0.5 * w[i] * (hs[bnb[i]].mean() - hs[i])
    hs = h2
Q = P + ((hs - h) * w)[:, None] * nrm
chest_disp = np.linalg.norm(Q - P, axis=1)
sel = np.where(w > 0)[0]
print('CHEST sel', len(sel), 'max disp', chest_disp.max().round(4), 'mean disp', chest_disp[sel].mean().round(4),
      'h std before/after', h[sel].std().round(5), hs[sel].std().round(5),
      'bust apex x before/after', P[body & (np.abs(P[:, 1]) < 0.09)][:, 0].max().round(4), Q[body & (np.abs(Q[:, 1]) < 0.09)][:, 0].max().round(4))
# ---------- 2. back hair tips: clearance push ----------
hair = np.isin(isl, hair_ids); hidx = np.where(hair)[0]
CL = 0.012  # ~2 cm at 1.62 m
cl0 = clearance(Q, hidx)
s0 = np.array([c[0] for c in cl0])
print('HAIR before: n', len(hidx), 'penetrating', int((s0 < 0).sum()), '<1cm', int((s0 < 0.006).sum()), '<2cm', int((s0 < CL).sum()), 'min', s0.min().round(4))
D = np.zeros_like(Q)
z = Q[:, 2]
ramp = np.clip((0.20 - z) / (0.20 - 0.12), 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
for k, i in enumerate(hidx):
    s, n = cl0[k]
    if s < CL and ramp[i] > 0: D[i] = n * (CL - s) * ramp[i]
# diffuse displacement on hair graph (max-preserving smooth)
for it in range(12):
    D2 = D.copy()
    for i in hidx:
        nb = nbr[i]
        if nb:
            avg = D[nb].mean(0)
            D2[i] = avg if np.linalg.norm(avg) > np.linalg.norm(D[i]) else 0.5 * (D[i] + avg)
    D = D2
D *= ramp[:, None] if False else 1.0
Q2 = Q + D
# iterate once more for anything still close
cl1 = clearance(Q2, hidx); s1 = np.array([c[0] for c in cl1])
for k, i in enumerate(hidx):
    s, n = cl1[k]
    if s < CL * 0.9 and z[i] < 0.2: Q2[i] += n * (CL - s)
cl2 = clearance(Q2, hidx); s2 = np.array([c[0] for c in cl2])
low = hidx[z[hidx] < 0.2]
print('HAIR after: penetrating', int((s2 < 0).sum()), '<1cm', int((s2 < 0.006).sum()), '<2cm(z<0.2)', int((s2[z[hidx] < 0.2] < CL * 0.95).sum()),
      'min', s2.min().round(4), 'max push', np.linalg.norm(Q2 - Q, axis=1).max().round(4))
for i in range(N0): me.vertices[i].co = Q2[i]
me.update()
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
GN = np.array([v.normal[:] for v in me.vertices])   # geometric normals after edit
wn = np.clip(w * 1.5, 0, 1)                           # blend zone a bit wider than the edit
NN = CN * (1 - wn)[:, None] + GN * wn[:, None]; NN /= (np.linalg.norm(NN, axis=1, keepdims=True) + 1e-12)
me.normals_split_custom_set_from_vertices([tuple(n) for n in NN])
me.update(); print('NORMALS custom cleared ->', me.has_custom_normals)
shoot('after')

# ---------- 3. scale to 1.62 m (hair top excl. ahoge), feet on ground ----------
ahoge = [i for i in ids if info[i]['mn'][2] > 0.455]
top = Q2[~np.isin(isl, ahoge)][:, 2].max(); bot = Q2[:, 2].min()
s = 1.62 / (top - bot)
for i in range(N0): me.vertices[i].co = Vector(((Q2[i, 0]) * s, Q2[i, 1] * s, (Q2[i, 2] - bot) * s))
me.update()
bb = np.array([v.co[:] for v in me.vertices])
ob['fix_notes'] = 'f001: chest crease Taubin(30it, masked); back-hair clearance >=2cm below z~0.20n; scaled %.4f, feet z=0, front +X' % s
bpy.data.objects.remove(cam)
bpy.ops.wm.save_as_mainfile(filepath=OUTD + 'FISH2_body_f001.blend')
bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
print('FIX', json.dumps(dict(scale=round(s, 4), hairtop_norm=round(float(top), 4), dims=np.ptp(bb, 0).round(4).tolist(), zmin=round(float(bb[:, 2].min()), 4))))
print('FIX_DONE')
