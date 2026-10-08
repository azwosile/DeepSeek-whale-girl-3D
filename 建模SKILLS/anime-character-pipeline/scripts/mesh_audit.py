"""网格结构审计 + 保护哈希（Blender 后台脚本）

用法:
  blender -b 模型.blend --factory-startup --python-exit-code 1 -P mesh_audit.py -- 输出.json [对象名前缀]

输出每个网格对象的：顶点/面数、连通片区数、边界边、非流形边、零面积面、世界包围盒，
以及 5 个哈希：topo（面-顶点索引）、uv、co（静止坐标，1e-6 m 取整）、vgroups（权重，1e-6）、mat（面材质索引）。
用 compare_audit.py 对比两次输出，可证明“只改了材质/只改了某个对象”。
注意：哈希一致是必要条件，不是充分条件——修改器、驱动器、动作也要另外核对（见 references/07）。
"""
import bpy, sys, json, hashlib
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else 'mesh_audit.json'
PREFIX = argv[1] if len(argv) > 1 else ''


def h(arr):
    return hashlib.sha1(np.ascontiguousarray(arr).tobytes()).hexdigest()[:16]


def islands(nv, edges):
    parent = np.arange(nv)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(i) for i in range(nv)})


res = {'file': bpy.data.filepath, 'blender': bpy.app.version_string, 'objects': {}}
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != 'MESH' or not ob.name.startswith(PREFIX):
        continue
    me = ob.data
    nv, nf = len(me.vertices), len(me.polygons)
    co = np.empty(nv * 3, np.float64); me.vertices.foreach_get('co', co)
    ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
    ls = np.empty(nf, np.int64); me.polygons.foreach_get('loop_start', ls)
    area = np.empty(nf); me.polygons.foreach_get('area', area)
    mat = np.empty(nf, np.int64); me.polygons.foreach_get('material_index', mat)
    # edge -> face count
    ek = {}
    for p in me.polygons:
        for k in p.edge_keys:
            ek[k] = ek.get(k, 0) + 1
    cnt = np.array(list(ek.values())) if ek else np.zeros(0)
    uvh = {}
    for uv in me.uv_layers:
        a = np.empty(len(me.loops) * 2); uv.data.foreach_get('uv', a); uvh[uv.name] = h(np.round(a, 6))
    W = []
    for v in me.vertices:
        for g in v.groups:
            W.append((v.index, g.group, round(g.weight, 6)))
    mw = np.array(ob.matrix_world)
    wco = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3] if nv else np.zeros((1, 3))
    res['objects'][ob.name] = {
        'verts': nv, 'faces': nf, 'islands': islands(nv, ed) if nv else 0,
        'boundary_edges': int((cnt == 1).sum()), 'nonmanifold_edges': int((cnt > 2).sum()),
        'zero_area_faces': int((area < 1e-12).sum()),
        'bbox_world': [np.round(wco.min(0), 4).tolist(), np.round(wco.max(0), 4).tolist()],
        'modifiers': [f'{m.type}:{m.name}' for m in ob.modifiers],
        'vertex_groups': len(ob.vertex_groups),
        'shape_keys': [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
        'hash': {'topo': h(np.concatenate([ls, lv])), 'uv': uvh, 'co': h(np.round(co, 6)),
                 'vgroups': h(np.array(W, dtype=np.float64)) if W else None, 'mat': h(mat)},
    }
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('AUDIT_DONE', OUT, len(res['objects']), 'objects')
