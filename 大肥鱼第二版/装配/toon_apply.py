# 大肥鱼第二版 卡通渲染 t001：Toon18 材质 + 反转外壳描边 + 灯光/世界
import bpy, json, numpy as np
from mathutils import Vector
ASM = 'D:/DeepSeek Harness WorkSpace/Blender DSH/大肥鱼第二版/装配/'
SRC = 'D:/DeepSeek Harness WorkSpace/Blender DSH/OC 第五版/骨骼与渲染_20261006/OC5_anime_toon_v018.blend'
bpy.ops.wm.open_mainfile(filepath=ASM + 'FISH2_phys_p002.blend')
sc = bpy.context.scene; R = {}
TM = 'MAT-Toon18-MAT-Anime-tripo_mat_fe3e02d2'
LG = ['LGT-Anime_Key', 'LGT-Anime_Fill', 'LGT-Anime_Rim', 'LGT-Toon18Sun']
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.materials = [TM]; dst.worlds = ['WORLD-Toon18']; dst.objects = LG
toon = bpy.data.materials[TM]; sc.world = bpy.data.worlds['WORLD-Toon18']
from mathutils import Matrix
RZ = Matrix.Rotation(1.5707963, 4, 'Z')
for o in dst.objects:
    sc.collection.objects.link(o); o.location = RZ.to_3x3() @ o.location; o.rotation_mode = 'XYZ'; o.rotation_euler = (RZ.to_3x3() @ o.rotation_euler.to_matrix()).to_euler('XYZ'); print('TA light', o.name, tuple(round(x, 2) for x in o.location))
attrs = {n.name: n.attribute_name for n in toon.node_tree.nodes if n.type == 'ATTRIBUTE'}; print('TA attrs', attrs)
for n in toon.node_tree.nodes:
    if n.type == 'VECT_MATH': print('TA vm', n.name, n.operation, [tuple(round(x, 3) for x in i.default_value) for i in n.inputs if not i.is_linked and hasattr(i.default_value, '__len__')])
for t_ in [toon]:
    for n in t_.node_tree.nodes:
        if n.type == 'VECT_MATH' and n.operation == 'DOT_PRODUCT':
            for i in n.inputs:
                if not i.is_linked and hasattr(i.default_value, '__len__') and Vector(i.default_value).length > 0.1:
                    v = Vector(i.default_value); i.default_value = (-v.y, v.x, v.z)
FACE_A = attrs.get('TOON18-Render-only face region'); HAIR_A = attrs.get('TOON18-Hair-only highlight mask')
# ---- attributes on the body ----
body = bpy.data.objects['FISH2_body']; me = body.data
def labels(me):
    n = len(me.vertices); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    return np.array([f(i) for i in range(n)])
P = np.array([v.co[:] for v in me.vertices]) @ np.array(body.matrix_world.to_3x3()).T + np.array(body.matrix_world.translation)
L = labels(me); skin = min(np.unique(L), key=lambda i: P[L == i][:, 2].min())
rig = bpy.data.objects['FISH2_rig']; hb = rig.data.bones['head']; hx = hb.head_local.x; hz = hb.head_local.z
probe = np.array([hx + 0.11, 0, hz + 0.0]); fi = int(np.argmin(np.linalg.norm(P - probe, axis=1))); face_isl = L[fi]
cnt = {i: int((L == i).sum()) for i in np.unique(L)}
print('TA face island', face_isl, cnt[face_isl], P[L == face_isl].min(0).round(3), P[L == face_isl].max(0).round(3))
face = np.zeros(len(P)); fm = (L == face_isl)
face[fm] = np.clip((P[fm, 0] - hx) / 0.05, 0, 1)
hair = np.array([1.0 if (L[i] != skin and L[i] != face_isl and cnt[L[i]] > 300) else 0.0 for i in range(len(P))])
for nm, val in ((FACE_A, face), (HAIR_A, hair)):
    if not nm: continue
    if nm in me.attributes: me.attributes.remove(me.attributes[nm])
    a = me.attributes.new(nm, 'FLOAT', 'POINT'); a.data.foreach_set('value', val.astype(np.float32))
R['face_verts'] = int((face > 0).sum()); R['hair_verts'] = int(hair.sum())
# ---- materials ----
done = {}
def img_of(m):
    if not m or not m.use_nodes: return None
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image: return n.image
OUTC = {'FISH2_body': (0.06, 0.07, 0.16), 'FISH2_outfit': (0.04, 0.045, 0.11)}
meshes = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith('FISH2_') and not o.hide_render]
for o in meshes:
    for s in o.material_slots:
        m = s.material; im = img_of(m)
        if im is None: print('TA no image', o.name, m.name if m else None); continue
        if m.name not in done:
            t = toon.copy(); t.name = 'FISH2-Toon18-' + m.name
            for n in t.node_tree.nodes:
                if n.type == 'TEX_IMAGE': n.image = im
            done[m.name] = t
        s.material = done[m.name]
    # outline (inverted hull)
    om = bpy.data.materials.new('FISH2-Outline-' + o.name); om.use_nodes = True; nt = om.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0])
    em.inputs['Color'].default_value = (*OUTC.get(o.name, (0.05, 0.05, 0.12)), 1); om.use_backface_culling = True
    try: om.use_backface_culling_shadow = True
    except Exception: pass
    o.data.materials.append(om); idx = len(o.data.materials) - 1
    sd = o.modifiers.new('Outline', 'SOLIDIFY'); sd.use_flip_normals = True; sd.use_rim = False; sd.offset = 1.0
    sd.thickness = {'FISH2_body': 0.0024, 'FISH2_outfit': 0.0030}.get(o.name, 0.0022)
    if o.name == 'FISH2_body':
        vg = o.vertex_groups.new(name='outline_w'); w = 1 - 0.6 * face
        for k in range(len(w)): vg.add([k], float(w[k]), 'REPLACE')
        sd.vertex_group = 'outline_w'; sd.thickness_vertex_group = 0.0; sd.material_offset = idx; sd.material_offset_rim = idx
    sd.use_quality_normals = True
    R.setdefault('outline', {})[o.name] = sd.thickness
print('TA mats', len(done))
# ---- render settings ----
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.film_transparent = False
try: sc.eevee.taa_render_samples = 32
except Exception: pass
bpy.ops.wm.save_as_mainfile(filepath=ASM + 'FISH2_toon_t002.blend')
json.dump(R, open(ASM + 'toon_t002_report.json', 'w'), indent=1)
print('TA_DONE', R)
