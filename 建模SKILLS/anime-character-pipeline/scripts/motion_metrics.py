"""骨链运动质量指标（Blender 后台脚本）：判断头发/尾巴/飘带“抖不抖、折不折”。

用法:
  blender -b 模型.blend --factory-startup --python-exit-code 1 -P motion_metrics.py -- 输出.json 骨架名|auto 链前缀1,链前缀2,... 起始帧 结束帧 [fps]
  例: ... -- jit.json FISH2_rig hair_B0,hair_B3,hair_FR,tail 100 228 30
每条链 = 名字以该前缀开头的所有骨骼，按层级从根到梢排序；梢点 = 最后一节的 tail。
从第 1 帧逐帧推进（保证缓存正确），只统计 [起始帧, 结束帧]。

指标（与 references/05 对应）:
  tip_acc_p95      梢点加速度 p95 (m/s^2)。平滑基线约十几到三十；上百说明在颤振
  hf_ratio_5hz     梢点相对根部位移中 >5 Hz 的能量占比。<0.1 正常；>0.4 是高频抖动
  reversal_rate    梢点速度方向反转的帧占比（按主分量）。越低越平顺
  chord_min/p5     根→梢直线距离 / 静止时的距离。<0.9 说明发束被折叠/压缩（“一折一折”）
  bend_p95_deg     各关节相对静止姿态的弯曲变化 p95（逐关节列出，根→梢）
"""
import bpy, sys, json
import numpy as np

A = sys.argv[sys.argv.index('--') + 1:]
OUT, ARM = A[0], A[1]; PREF = A[2].split(','); F0, F1 = int(A[3]), int(A[4]); FPS = float(A[5]) if len(A) > 5 else 30.0
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE') if ARM == 'auto' else bpy.data.objects[ARM]


def chain(prefix):
    bs = [b for b in arm.pose.bones if b.name.startswith(prefix)]
    depth = lambda b: len(b.parent_recursive)
    return sorted(bs, key=depth)


CH = {p: chain(p) for p in PREF}
for p, bs in CH.items():
    if not bs:
        raise SystemExit(f'链 {p} 没有找到骨骼')
REST = {p: [(arm.matrix_world.to_3x3() @ b.bone.matrix_local.to_3x3()).col[1].normalized() for b in bs] for p, bs in CH.items()}
rec = {p: {'root': [], 'tip': [], 'dirs': []} for p in PREF}
for f in range(1, F1 + 1):
    sc.frame_set(f)
    if f < F0:
        continue
    M = arm.matrix_world
    for p, bs in CH.items():
        rec[p]['root'].append(list(M @ bs[0].head)); rec[p]['tip'].append(list(M @ bs[-1].tail))
        rec[p]['dirs'].append([list((M.to_3x3() @ b.matrix.to_3x3()).col[1].normalized()) for b in bs])
res = {'file': bpy.data.filepath, 'frames': [F0, F1], 'fps': FPS, 'chains': {}}
dt = 1.0 / FPS
for p, bs in CH.items():
    root = np.array(rec[p]['root']); tip = np.array(rec[p]['tip']); D = np.array(rec[p]['dirs'])
    rel = tip - root
    acc = np.linalg.norm(np.diff(tip, 2, axis=0), axis=1) / dt ** 2
    x = rel - rel.mean(0); S = np.abs(np.fft.rfft(x, axis=0)) ** 2; fr = np.fft.rfftfreq(len(x), dt)
    hf = float(S[fr > 5].sum() / max(S[1:].sum(), 1e-12))
    v = np.diff(rel, axis=0); u = np.linalg.svd(v - v.mean(0), full_matrices=False)[2][0]; s = np.sign(v @ u)
    rev = float((s[1:] * s[:-1] < 0).mean())
    rest_len = np.linalg.norm((arm.matrix_world @ bs[-1].bone.tail_local) - (arm.matrix_world @ bs[0].bone.head_local))
    chord = np.linalg.norm(rel, axis=1) / max(rest_len, 1e-9)
    # 关节弯曲：相邻两节夹角，与静止夹角之差
    R = np.array([list(d) for d in REST[p]])
    restang = np.degrees(np.arccos(np.clip((R[1:] * R[:-1]).sum(1), -1, 1)))
    ang = np.degrees(np.arccos(np.clip((D[:, 1:] * D[:, :-1]).sum(2), -1, 1)))
    bend = np.abs(ang - restang)
    res['chains'][p] = {
        'bones': [b.name for b in bs], 'tip_acc_p95': round(float(np.percentile(acc, 95)), 2),
        'hf_ratio_5hz': round(hf, 3), 'reversal_rate': round(rev, 3),
        'chord_min': round(float(chord.min()), 3), 'chord_p5': round(float(np.percentile(chord, 5)), 3),
        'bend_p95_deg': [round(float(t), 1) for t in np.percentile(bend, 95, axis=0)],
        'tip_disp_max_m': round(float(np.linalg.norm(rel - rel[0], axis=1).max()), 3),
    }
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('METRICS_DONE', OUT, json.dumps({k: [v['tip_acc_p95'], v['hf_ratio_5hz'], v['chord_min']] for k, v in res['chains'].items()}))
