# 大肥鱼第二版 物理 p001：头发/鱼尾自写弹簧链烘焙 + 裙代理布料烘焙
import bpy, json, math, numpy as np
from mathutils import Vector, Matrix, Quaternion
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_rig_r002.blend')
sc = bpy.context.scene; rig = bpy.data.objects['FISH2_rig']; arm = rig.data; PB = rig.pose.bones
F0, F1 = 1, 230; SUB = 4; DT = 1.0 / sc.render.fps / SUB
# chains
names = sorted({b.name.rsplit('_', 1)[0] for b in arm.bones if b.name.startswith(('hair_', 'tail_'))})
CH = []
for n in names:
    bs = [arm.bones['%s_%d' % (n, j)] for j in range(10) if ('%s_%d' % (n, j)) in arm.bones]
    CH.append(dict(name=n, bones=[b.name for b in bs], parent=bs[0].parent.name,
                   rest=[Vector(bs[0].head_local)] + [Vector(b.tail_local) for b in bs],
                   L=[b.length for b in bs], tail=n.startswith('tail')))
CH.sort(key=lambda c: 0 if c['tail'] else 1)
TAILC = [c for c in CH if c['tail']][0]
COLB = ['hips', 'spine', 'chest', 'upper_chest', 'neck', 'head', 'thigh.L', 'thigh.R']
def seg_closest(p, a, b):
    d = b - a; t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared)); return a + d * t
for c in CH:
    c['cr'] = []
    for i, p in enumerate(c['rest']):
        row = []
        for bn in COLB:
            b = arm.bones[bn]; q = seg_closest(p, b.head_local, b.tail_local); dd = (p - q).length
            row.append(dd * 0.95 if (dd < 0.2 and i > 0) else 0.0)
        c['cr'].append(row)
for c in CH:
    c['tr'] = []
    for i, p in enumerate(c['rest']):
        row = []
        for j in range(len(TAILC['rest']) - 1):
            q = seg_closest(p, TAILC['rest'][j], TAILC['rest'][j + 1]); dd = (p - q).length
            row.append(min(dd * 0.95, 0.06) if (not c['tail'] and dd < 0.15 and i > 0) else 0.0)
        c['tr'].append(row)
tail_sub = {}
# disable heavy evaluation during the bake
saved = []
for o in sc.objects:
    if o.type == 'MESH':
        for m in o.modifiers:
            saved.append((m, m.show_viewport)); m.show_viewport = False
for c in CH:
    for bn in c['bones']:
        PB[bn].rotation_mode = 'QUATERNION'; PB[bn].rotation_quaternion = Quaternion()
act = rig.animation_data.action
def remove_chain_keys():
    for c in CH:
        for bn in c['bones']:
            try: PB[bn].keyframe_delete('rotation_quaternion')
            except Exception: pass
P = dict(hair=dict(k0=70.0, k1=22.0, zeta=0.75, maxang=32.0), tail=dict(k0=90.0, k1=35.0, zeta=0.8, maxang=28.0))
state = {}; out = {c['name']: [] for c in CH}; stats = {c['name']: dict(maxdev=0.0, maxjerk=0.0) for c in CH}
prevM = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    M = {bn: Matrix(PB[bn].matrix) for bn in set(COLB) | {c['parent'] for c in CH}}
    for c in CH:
        par = arm.bones[c['parent']]; Mp = M[c['parent']]; Mp0 = prevM.get(c['parent'], Mp)
        rel = Mp @ par.matrix_local.inverted(); rel0 = Mp0 @ par.matrix_local.inverted()
        n = len(c['rest']); pr = P['tail' if c['tail'] else 'hair']
        T1 = [rel @ p for p in c['rest']]; T0 = [rel0 @ p for p in c['rest']]
        if c['name'] not in state:
            state[c['name']] = dict(x=[t.copy() for t in T1], v=[Vector() for _ in T1])
        S = state[c['name']]; x, v = S['x'], S['v']
        for s in range(1, SUB + 1):
            a_ = s / SUB
            T = [T0[i].lerp(T1[i], a_) for i in range(n)]
            x[0] = T[0].copy()
            for i in range(1, n):
                k = pr['k0'] + (pr['k1'] - pr['k0']) * (i - 1) / max(n - 2, 1); cdmp = 2 * pr['zeta'] * math.sqrt(k)
                acc = (T[i] - x[i]) * k - v[i] * cdmp
                v[i] = v[i] + acc * DT; x[i] = x[i] + v[i] * DT
            # deviation smoothing along chain (anti zig-zag)
            off = [x[i] - T[i] for i in range(n)]
            for i in range(1, n):
                nb = off[i - 1] * 0.25 + off[i] * 0.5 + (off[i + 1] * 0.25 if i + 1 < n else off[i] * 0.25)
                x[i] = T[i] + nb
            # length + angle constraints from root
            for i in range(1, n):
                old = x[i].copy()
                d = (x[i] - x[i - 1]); td = (T[i] - T[i - 1]).normalized()
                if d.length < 1e-6: d = td.copy()
                dn = d.normalized(); ang = math.degrees(dn.angle(td, 0.0))
                if ang > pr['maxang']:
                    q = td.rotation_difference(dn); axis, an = q.to_axis_angle()
                    dn = Quaternion(axis, math.radians(pr['maxang'])) @ td
                x[i] = x[i - 1] + dn * c['L'][i - 1]
                # collisions (rest-distance capsules)
                for ci, bn in enumerate(COLB):
                    r = c['cr'][i][ci]
                    if r <= 0: continue
                    b = arm.bones[bn]; Mb = M[bn]; ha = Mb.translation; ta = Mb @ Vector((0, b.length, 0))
                    q = seg_closest(x[i], ha, ta); dd = x[i] - q
                    if dd.length < r: x[i] = q + dd.normalized() * r
                if not c['tail'] and s in tail_sub:
                    tx = tail_sub[s]
                    for j in range(len(tx) - 1):
                        r = c['tr'][i][j]
                        if r <= 0: continue
                        q = seg_closest(x[i], tx[j], tx[j + 1]); dd = x[i] - q
                        if dd.length < r: x[i] = q + dd.normalized() * r
                v[i] = v[i] + (x[i] - old) / DT * 0.5
            if c['tail']: tail_sub[s] = [p.copy() for p in x]
        out[c['name']].append([p.copy() for p in x])
        dev = max(math.degrees((x[i] - x[i - 1]).angle(T1[i] - T1[i - 1], 0)) for i in range(1, n))
        stats[c['name']]['maxdev'] = max(stats[c['name']]['maxdev'], dev)
    prevM = M
# convert to local rotations and keyframe
for fi, f in enumerate(range(F0, F1 + 1)):
    sc.frame_set(f)
    for c in CH:
        par = arm.bones[c['parent']]; Mpar = Matrix(PB[c['parent']].matrix)
        x = out[c['name']][fi]; Mp = Mpar; pb_rest_parent = par.matrix_local
        for j, bn in enumerate(c['bones']):
            b = arm.bones[bn]
            Mc0 = Mp @ pb_rest_parent.inverted() @ b.matrix_local
            d0 = (Mc0.to_3x3() @ Vector((0, 1, 0))).normalized(); d1 = (x[j + 1] - x[j]).normalized()
            q = d0.rotation_difference(d1); R0 = Mc0.to_quaternion()
            ql = R0.inverted() @ q @ R0
            pbn = PB[bn]
            if fi > 0 and pbn.rotation_quaternion.dot(ql) < 0: ql.negate()
            pbn.rotation_quaternion = ql; pbn.keyframe_insert('rotation_quaternion', frame=f)
            Mp = Matrix.Translation(Mc0.translation) @ (q.to_matrix() @ Mc0.to_3x3()).to_4x4(); pb_rest_parent = b.matrix_local
# jerk metric on tips (second difference, m/frame^2)
for c in CH:
    tip = np.array([fr[-1][:] for fr in out[c['name']]]); acc = np.linalg.norm(tip[2:] - 2 * tip[1:-1] + tip[:-2], axis=1)
    stats[c['name']]['maxjerk'] = float(acc[99:].max()); stats[c['name']]['meanjerk'] = float(acc[99:].mean())
    stats[c['name']]['maxdev'] = round(stats[c['name']]['maxdev'], 1)
for m, s in saved: m.show_viewport = s
# cloth bake
px = bpy.data.objects['FISH2_skirt_proxy']; cl = px.modifiers['cloth']
cl.point_cache.frame_start = F0; cl.point_cache.frame_end = F1
for f in range(F0, F1 + 1): sc.frame_set(f)
with bpy.context.temp_override(scene=sc, active_object=px, object=px, point_cache=cl.point_cache):
    bpy.ops.ptcache.bake_from_cache()
R = dict(chains=stats, cloth_baked=cl.point_cache.is_baked)
print('PB', json.dumps(R)[:1500])
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_phys_p002.blend')
json.dump(R, open(ASM + 'dynamics_verification_p002.json', 'w'), indent=1)
print('PB_DONE')
