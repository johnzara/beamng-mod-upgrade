"""Export the open .blend back to DAE with the settings BeamNG needs
(triangulated, matrix transforms, all UV sets, no global re-orientation).
usage: blender -b MODEL.blend --python bl_export.py -- OUT.dae
"""
import bpy, sys, time
out = sys.argv[sys.argv.index('--')+1]
t = time.time()
bpy.ops.wm.collada_export(filepath=out, apply_modifiers=True, selected=False, include_children=False,
    include_armatures=False, include_shapekeys=False, include_animations=False, active_uv_only=False,
    use_texture_copies=False, triangulate=True, use_object_instantiation=True, sort_by_name=False,
    keep_bind_info=False, limit_precision=False, apply_global_orientation=False,
    export_object_transformation_type_selection='matrix', export_mesh_type_selection='view')
print('EXPORTED', round(time.time()-t, 1))
