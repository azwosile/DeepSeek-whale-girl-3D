"""Collect a self-contained release from a final Blender checkpoint. Run in Blender.
Never changes the source checkpoint. Keeps essential PC2 files and delivered movies.
"""
import bpy, argparse, sys, json, hashlib, shutil, struct, re, math
from pathlib import Path

def arguments():
    p=argparse.ArgumentParser()
    p.add_argument('--source-blend',required=True)
    p.add_argument('--destination',required=True)
    p.add_argument('--voiced-video',required=True)
    p.add_argument('--silent-video',required=True)
    return p.parse_args(sys.argv[sys.argv.index('--')+1:])
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    a=arguments();src=Path(a.source_blend).resolve();out=Path(a.destination).resolve();project=out/'project'
    for folder in ['project','cache','audio','video','preview','reports','manifests']: (out/folder).mkdir(parents=True,exist_ok=True)
    release=project/'GYS_release_r033.blend';assert not release.exists(),release
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
    s=bpy.context.scene;entries={};manifest={'schema_version':1,'source_checkpoint':src.name,'source_checkpoint_sha256':digest(src),'blender_version':bpy.app.version_string,'dependencies':[],'frames':[s.frame_start,s.frame_end],'fps':s.render.fps/s.render.fps_base,'resolution':[s.render.resolution_x,s.render.resolution_y]}
    def collect(path,kind,folder,ref):
        path=Path(path).resolve();assert path.is_file(),(kind,path)
        sha=digest(path);key=(kind,sha)
        if key not in entries:
            name=re.sub(r'[^\w.\-]+','_',path.name)
            target=out/folder/(sha[:16]+'-'+name)
            if target.exists():assert digest(target)==sha,target
            else:shutil.copy2(path,target)
            assert digest(target)==sha,target
            row={'kind':kind,'path':target.relative_to(out).as_posix(),'bytes':target.stat().st_size,'sha256':sha,'source_basename':path.name,'references':[]}
            if kind=='mesh_cache':
                with target.open('rb') as f:signature,version,points,start,step,samples=struct.unpack('<12siiffi',f.read(32))
                assert signature==b'POINTCACHE2\0' and version==1
                assert target.stat().st_size==32+points*12*samples
                row['pc2']={'points':points,'samples':samples,'start':start,'step':step,'complete_bytes':True}
            entries[key]=(target,row);manifest['dependencies'].append(row)
            print('COLLECTED',kind,row['path'],row['bytes'],flush=True)
        target,row=entries[key];row['references'].append(ref)
        return '//'+__import__('os').path.relpath(target,project).replace('\\','/')
    assert not bpy.data.libraries,'Linked libraries must be resolved separately'
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            if m.type=='MESH_CACHE':m.filepath=collect(bpy.path.abspath(m.filepath),'mesh_cache','cache',ob.name+'/'+m.name)
            pc=getattr(m,'point_cache',None)
            if pc and getattr(pc,'use_disk_cache',False):raise RuntimeError('External physics disk cache requires explicit collection: '+ob.name+'/'+m.name)
    for sound in bpy.data.sounds:
        if not sound.packed_file:sound.filepath=collect(bpy.path.abspath(sound.filepath),'sound','audio',sound.name)
    for im in bpy.data.images:
        if im.source in {'FILE','TILED'} and not im.packed_file:im.pack()
    for font in bpy.data.fonts:
        if font.filepath and font.filepath!='<builtin>' and not font.packed_file:font.pack()
    for clip in bpy.data.movieclips:clip.filepath=collect(bpy.path.abspath(clip.filepath),'movie_clip','video',clip.name)
    movies={}
    for label,path in [('with-audio',a.voiced_video),('silent',a.silent_video)]:
        p=Path(path).resolve();assert p.is_file()
        target=out/'video'/('locker-room-r033-1080p-'+label+'.mp4');assert not target.exists();shutil.copy2(p,target);sha=digest(p);assert digest(target)==sha
        row={'kind':'delivered_video','path':target.relative_to(out).as_posix(),'bytes':target.stat().st_size,'sha256':sha,'references':[label]};manifest['dependencies'].append(row);movies[label]=row
    # Remove machine-specific provenance paths from custom metadata, not driver expressions.
    for owner in [s]+list(bpy.data.objects):
        for k in list(owner.keys()):
            v=owner[k]
            if isinstance(v,str) and re.match(r'^[A-Za-z]:[\\/]',v):owner[k]='[source path omitted from publication]'
    s['最终视频']='//../video/locker-room-r033-1080p-with-audio.mp4';s['最终视频SHA256']=movies['with-audio']['sha256'];s['验收记录']='//../reports/validation.json'
    s['发布说明']='Self-contained r033 release; mild intersections allowed, not zero-intersection certification.'
    s.render.filepath='//../renders/locker-room-r033';s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(release),check_existing=False,relative_remap=False,compress=True)
    manifest['release_checkpoint']={'path':release.relative_to(out).as_posix(),'bytes':release.stat().st_size,'sha256':digest(release)}
    manifest['unique_mesh_cache_count']=len([x for x in manifest['dependencies'] if x['kind']=='mesh_cache'])
    manifest['mesh_cache_bytes']=sum(x['bytes'] for x in manifest['dependencies'] if x['kind']=='mesh_cache')
    (out/'manifests'/'dependencies.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PACKAGE_COMPLETE',manifest['unique_mesh_cache_count'],manifest['mesh_cache_bytes'],flush=True)
if __name__=='__main__':main()
