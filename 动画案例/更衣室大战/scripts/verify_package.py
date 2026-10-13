"""Validate release dependency hashes, relative paths and selected Blender frames.
Run with Blender -b --factory-startup --disable-autoexec --python this_file -- --root CASE.
"""
import bpy,sys,argparse,json,hashlib,math,struct,array
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--render-qa',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=Path(a.root).resolve()
    manifest=json.loads((root/'manifests'/'dependencies.json').read_text(encoding='utf-8'))
    for row in manifest['dependencies']+[manifest['release_checkpoint']]:
        f=root/row['path'];assert f.is_file() and f.stat().st_size==row['bytes'],row['path'];assert digest(f)==row['sha256'],row['path']
    bpy.ops.wm.open_mainfile(filepath=str(root/'project'/'GYS_release_r033.blend'),load_ui=False,use_scripts=False)
    s=bpy.context.scene;refs=[]
    def check(path,label):
        assert path.startswith('//'),(label,'absolute path',path)
        f=Path(bpy.path.abspath(path)).resolve();assert root in f.parents and f.exists(),(label,f)
        refs.append({'label':label,'path':f.relative_to(root).as_posix()})
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            if m.type=='MESH_CACHE':check(m.filepath,ob.name+'/'+m.name)
    for x in bpy.data.sounds:
        if not x.packed_file:check(x.filepath,x.name)
    for x in bpy.data.movieclips:check(x.filepath,x.name)
    for x in bpy.data.images:
        if x.source in {'FILE','TILED'}:assert x.packed_file,('unpacked image',x.name)
    assert not bpy.data.libraries
    tested=[(1,0.),(700,0.),(700,.5),(1121,0.),(1121,.5),(1500,0.),(1500,.5),(2483,0.)]
    evaluated_meshes=set()
    for f,sub in tested:
        s.frame_set(f,subframe=sub);bpy.context.view_layer.update()
        for n in ['ARM-Claude_rig','FISH2_rig']:
            rig=bpy.data.objects[n]
            assert all(math.isfinite(v) for row in rig.matrix_world for v in row),(f,n)
        deps=bpy.context.evaluated_depsgraph_get()
        for ob in bpy.data.objects:
            if ob.type=='MESH' and any(m.type=='MESH_CACHE' for m in ob.modifiers):
                mesh=ob.evaluated_get(deps).data
                coords=array.array('f',[0.0])*(len(mesh.vertices)*3)
                mesh.vertices.foreach_get('co',coords)
                assert coords and all(math.isfinite(v) for v in coords),(f,sub,ob.name,'invalid evaluated vertices')
                evaluated_meshes.add(ob.name)
    av_path=root/'reports'/'av-delivery.json'
    av=json.loads(av_path.read_text(encoding='utf-8')) if av_path.exists() else None
    if av:
        master=next(x for x in manifest['dependencies'] if x['kind']=='delivered_video' and 'with-audio' in x['references'])
        assert av['sha256']==master['sha256'] and av['bytes']==master['bytes']
        assert av['decode_exit_code']==0 and av['decoded_frames']==2483
    errors=[]
    for d in list(bpy.data.objects)+list(bpy.data.shape_keys)+list(bpy.data.node_groups)+[m.node_tree for m in bpy.data.materials if m.node_tree]:
        ad=d.animation_data
        if ad:
            for fc in ad.drivers:
                if not fc.driver.is_valid:errors.append({'id':d.name,'path':fc.data_path})
    assert not errors,errors
    report={'status':'package_dependency_validation_passed','all_manifest_hashes_passed':True,'outside_package_dependencies':[],'relative_dependencies':refs,'tested_frame_subframes':tested,'driver_errors':errors,'scene_frames':[s.frame_start,s.frame_end],'fps':s.render.fps/s.render.fps_base,'resolution':[s.render.resolution_x,s.render.resolution_y],'evaluated_cache_meshes':sorted(evaluated_meshes),'original_video_validation':{'voiced_and_silent_master_exist':True,'voiced_full_av_decode_passed':bool(av),'decoded_frames':av['decoded_frames'] if av else None,'evidence':'reports/av-delivery.json' if av else None,'note':'Previous full decode evidence matched against the current master hash; this script does not decode MP4s'},'acceptance':'Mild intersections allowed; sampled visual review, not zero-penetration certification','qa_renders':[]}
    if a.render_qa:
        s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=92
        if hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=16
        for f in [1,375,1121,1543,1960,2483]:
            s.frame_set(f);name='preview/qa_%04d.jpg'%f;s.render.filepath=str(root/name);bpy.ops.render.render(write_still=True);report['qa_renders'].append(name)
    (root/'reports'/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PACKAGE_VALIDATED',len(refs),len(report['qa_renders']),flush=True)
if __name__=='__main__':main()
