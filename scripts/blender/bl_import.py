"""Import a DAE into a fresh .blend (Blender 4.5 LTS).
usage: blender -b --python bl_import.py -- MODEL.dae OUT.blend
"""
import bpy, sys, time, json
dae, out = sys.argv[sys.argv.index('--')+1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
t = time.time()
bpy.ops.wm.collada_import(filepath=dae, import_units=False, fix_orientation=False, auto_connect=False, find_chains=False, keep_bind_info=False)
print('IMPORT_SECONDS', round(time.time()-t, 1))
objs = bpy.context.scene.objects
print('IMPORT_OBJECTS', len(objs), 'MESHES', sum(o.type == 'MESH' for o in objs))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('SAVED', out)
