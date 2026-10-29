"""Render single objects (workbench, cavity shading) to compare before/after decimation.
usage: blender -b MODEL.blend --python bl_preview.py -- OUTDIR TAG OBJECT [OBJECT ...]
"""
import bpy, sys, mathutils, os
args = sys.argv[sys.argv.index('--')+1:]
outdir, tag, names = args[0], args[1], args[2:]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.7, 0.7, 0.72)
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_specular_highlight = True
sc.render.resolution_x, sc.render.resolution_y = 640, 480
sc.render.film_transparent = False
cam_data = bpy.data.cameras.new('pc'); cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('pc', cam_data); sc.collection.objects.link(cam); sc.camera = cam
for n in names:
    o = bpy.data.objects.get(n)
    if not o: print('MISSING', n); continue
    for x in sc.objects:
        if x.type == 'MESH': x.hide_render = (x != o)
    pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    ctr = sum(pts, mathutils.Vector()) / 8
    size = max((max(p[i] for p in pts) - min(p[i] for p in pts)) for i in range(3))
    d = mathutils.Vector((0.9, -1.0, 0.55)).normalized()
    cam.location = ctr + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam_data.ortho_scale = size * 1.15; cam_data.clip_end = size * 10
    sc.render.filepath = os.path.join(outdir, '%s_%s.png' % (n, tag))
    bpy.ops.render.render(write_still=True)
    o.data.calc_loop_triangles(); print('RENDERED', n, len(o.data.loop_triangles))
