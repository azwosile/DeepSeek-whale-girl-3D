"""多视图正交渲染（Blender 后台脚本）：正 / 左 / 背 / 右 + 可选特写，自动取景。

用法:
  blender -b 模型.blend --factory-startup --python-exit-code 1 -P multiview_render.py -- 输出目录 [选项]
  blender -b --factory-startup --python-exit-code 1 -P multiview_render.py -- 输出目录 --import 模型.fbx [选项]
选项:
  --front +X|-X|+Y|-Y   角色正面朝向（默认 -Y，Blender 惯例；Tripo FBX 原样导入时请先确认，见 references/02）
  --engine WORKBENCH|EEVEE   默认 WORKBENCH（贴图平光，适合检查几何与贴图）；卡通材质验收用 EEVEE
  --frame N             渲染第 N 帧（会从第 1 帧逐帧推进，保证布料/物理缓存正确）
  --size 800x1400       单张分辨率
  --views front,left,back,right
  --close x,y,z,scale   额外一张特写：注视点与正交尺度，方向用正面
输出: <输出目录>/<视图>.png，打印 MV_DONE。
要点：同一台机不要并行开两个 EEVEE 渲染这一份工程，贴图可能丢失（品红色）。
"""
import bpy, sys, os
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(A[0]); os.makedirs(OUT, exist_ok=True)   # 必须绝对路径：Blender 的 render.filepath 不按当前目录解析相对路径
opt = {A[i][2:]: A[i + 1] for i in range(1, len(A) - 1) if A[i].startswith('--')}
if 'import' in opt:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = opt['import']; ext = p.lower().rsplit('.', 1)[-1]
    {'fbx': lambda: bpy.ops.import_scene.fbx(filepath=p), 'glb': lambda: bpy.ops.import_scene.gltf(filepath=p),
     'gltf': lambda: bpy.ops.import_scene.gltf(filepath=p), 'obj': lambda: bpy.ops.wm.obj_import(filepath=p)}[ext]()
sc = bpy.context.scene
eng = opt.get('engine', 'WORKBENCH').upper()
if eng == 'WORKBENCH':
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
    if sc.world is None:
        sc.world = bpy.data.worlds.new('mv_world')
    sc.world.color = (0.78, 0.78, 0.78)
    sc.view_settings.view_transform = 'Standard'
else:
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.image_settings.file_format = 'PNG'
if 'frame' in opt:
    for f in range(1, int(opt['frame']) + 1):
        sc.frame_set(f)
W, H = (int(x) for x in opt.get('size', '800x1400').split('x'))
sc.render.resolution_x, sc.render.resolution_y = W, H
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for ob in sc.objects:
    if ob.type == 'MESH' and ob.visible_get() and not ob.hide_render:
        pts += [ob.matrix_world @ Vector(c) for c in ob.evaluated_get(dg).bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
c = (mn + mx) / 2; ext = mx - mn
cd = bpy.data.cameras.new('mv_cam'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('mv_cam', cd); sc.collection.objects.link(cam); sc.camera = cam
F = {'+X': Vector((1, 0, 0)), '-X': Vector((-1, 0, 0)), '+Y': Vector((0, 1, 0)), '-Y': Vector((0, -1, 0))}[opt.get('front', '-Y')]
L = Vector((0, 0, 1)).cross(F)   # 角色左侧方向（右手系，Z 向上）——相机放在角色左侧时看到“左侧视图”
DIRS = {'front': F, 'back': -F, 'left': L, 'right': -L}


def shoot(name, d, target, scale):
    cam.location = target + d.normalized() * (ext.length * 2 + 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = scale; cd.clip_end = ext.length * 6 + 10
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)


for v in opt.get('views', 'front,left,back,right').split(','):
    d = DIRS[v]
    horiz = ext.y if abs(d.x) > 0.5 else ext.x          # 画面横向对应的世界跨度
    scale = (max(ext.z, horiz * H / W) if H >= W else max(horiz, ext.z * W / H)) * 1.08
    shoot(v, d, c, scale)
if 'close' in opt:
    x, y, z, s = (float(t) for t in opt['close'].split(','))
    shoot('close', F, Vector((x, y, z)), s)
print('MV_DONE', OUT, 'bbox', [round(t, 3) for t in mn], [round(t, 3) for t in mx])
