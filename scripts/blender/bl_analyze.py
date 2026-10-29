"""Per-mesh stats (tris, dims, materials, UV sets, which parts use it).
usage: blender -b MODEL.blend --python bl_analyze.py -- OUT.json mesh_usage.json
"""
import bpy, json, sys, collections
out, usage = sys.argv[sys.argv.index('--')+1:][:2]
use = json.load(open(usage))
rows = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    me = o.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    d = o.dimensions
    rows.append({'name': o.name, 'data': me.name, 'tris': tris, 'verts': len(me.vertices), 'used': o.name in use,
                 'parts': use.get(o.name, [])[:3], 'dims': [round(d.x,3), round(d.y,3), round(d.z,3)],
                 'loc': [round(v,3) for v in o.matrix_world.translation], 'mats': [m.name for m in me.materials if m],
                 'uvs': len(me.uv_layers), 'colors': len(me.color_attributes), 'users': me.users,
                 'parent': o.parent.name if o.parent else None})
json.dump(rows, open(out, 'w'), indent=0)
print('ANALYZED', len(rows))
