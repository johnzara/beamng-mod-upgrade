"""Remove meshes no part uses and decimate over-dense ones, keeping their shading.

usage (Blender 4.5 LTS; 5.x has no COLLADA):
  blender -b model.blend --python bl_decimate.py -- mesh_usage.json out.blend report.json [caps.json]

mesh_usage.json: from audit.py --usage-out. Objects not in it (and with no children) are deleted.
caps.json: optional {"caps": [["keyword", max_tris], ...], "default": 25000, "keep": ["keyword", ...]}
  first keyword found in the lowercase object name wins; "keep" objects are never decimated.
  Objects within 15% of their cap are left alone.
Each decimated mesh gets its custom normals copied back from the dense original
(DATA_TRANSFER, POLYINTERP_NEAREST), which is what keeps panels from looking dented.
ALWAYS render before/after (bl_preview.py) and exempt anything that shows artifacts:
on the Saab the dashboard, engine, upper trim and body shell had to be kept at full detail.
"""
import bpy, json, sys
args = sys.argv[sys.argv.index('--') + 1:]
usage, out_blend, report = args[:3]
use = json.load(open(usage))
cfg = json.load(open(args[3])) if len(args) > 3 else {}
CAPS = cfg.get('caps', [['headliner', 12000], ['navi', 8000], ['steer', 20000], ['doorpanel', 30000], ['seat', 24000],
                        ['motor', 20000], ['battery', 10000], ['transmission', 15000], ['gauge', 15000], ['radio', 8000],
                        ['bumper', 55000], ['light', 30000], ['door', 45000], ['hood', 45000], ['fender', 45000],
                        ['tailgate', 45000], ['trunk', 45000], ['roof', 45000]])
DEFAULT_CAP = cfg.get('default', 25000)
KEEP = [k.lower() for k in cfg.get('keep', ['dash', 'engine', 'body', 'quarterpanel', 'trim'])]
def cap_for(name):
    n = name.lower()
    if any(k in n for k in KEEP): return None
    for k, c in CAPS:
        if k in n: return c
    return DEFAULT_CAP
def tris(me):
    me.calc_loop_triangles(); return len(me.loop_triangles)

log = {'removed': [], 'decimated': [], 'kept': []}
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in use and not o.children:
        log['removed'].append([o.name, tris(o.data)]); bpy.data.objects.remove(o, do_unlink=True)
done = set()
for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    me = o.data
    if me.name in done: continue
    done.add(me.name)
    before = tris(me); cap = cap_for(o.name)
    if cap is None: log['kept'].append([o.name, before]); continue
    if before <= cap * 1.15: continue
    sharers = [x for x in bpy.data.objects if x.data == me and x != o]
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    if me.users > 1: o.data = me.copy()
    ref = o.copy(); ref.data = o.data.copy(); bpy.context.scene.collection.objects.link(ref)
    mod = o.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
    mod.ratio = cap / before; mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    dt = o.modifiers.new('nrm', 'DATA_TRANSFER'); dt.object = ref
    dt.use_loop_data = True; dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(ref, do_unlink=True)
    for x in sharers: x.data = o.data
    log['decimated'].append([o.name, before, tris(o.data)])
bpy.ops.outliner.orphans_purge(do_recursive=True)
log['total_after'] = sum(tris(o.data) for o in bpy.context.scene.objects if o.type == 'MESH')
log['removed_names'] = [n for n, _ in log['removed']]
json.dump(log, open(report, 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
print('DONE removed=%d decimated=%d kept=%d total=%d' % (len(log['removed']), len(log['decimated']), len(log['kept']), log['total_after']))
