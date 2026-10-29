"""Fast stats of a (large) COLLADA file without loading it into Blender.

usage: dae_stats.py MODEL.dae OUT.json
Prints up axis, unit, geometry count, total triangles, node count, material count;
OUT.json has per-geometry triangles and the node list.
"""
import sys, xml.etree.ElementTree as ET, json
path = sys.argv[1]
ns = '{http://www.collada.org/2005/11/COLLADASchema}'
geoms = {}; cur = None; tris = 0; nodes = []; up = None; unit = None; images = 0; mats=set()
depth_node = 0
for ev, el in ET.iterparse(path, events=('start','end')):
    tag = el.tag.replace(ns,'')
    if ev == 'start':
        if tag == 'geometry': cur = el.get('name') or el.get('id'); tris = 0
        elif tag == 'node': nodes.append(el.get('name') or el.get('id'))
        continue
    if tag in ('triangles','polylist','polygons') and cur:
        tris += int(el.get('count','0')); mats.add(el.get('material'))
    elif tag == 'geometry':
        geoms[cur] = tris; cur = None; el.clear()
    elif tag == 'up_axis': up = el.text
    elif tag == 'unit': unit = el.get('meter')
    elif tag == 'image': images += 1
    elif tag in ('float_array','p','vcount','source','mesh'):
        el.clear()
json.dump({'up':up,'unit':unit,'geometries':len(geoms),'total_tris':sum(geoms.values()),'images':images,'materials':len(mats),
 'top':sorted(geoms.items(), key=lambda x:-x[1])[:25],'nodes':nodes,'geoms':geoms}, open(sys.argv[2],'w'), indent=1)
print(up, unit, len(geoms), sum(geoms.values()), len(nodes), len(mats))
