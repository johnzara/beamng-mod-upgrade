"""Check a re-exported DAE against the original: lost/added objects, moved transforms,
lost UV sets, lost materials.

usage: dae_compare.py ORIGINAL.dae NEW.dae [decimate_report.json]
Objects listed in the report's removed_names are expected to be gone.
"""
import sys, xml.etree.ElementTree as ET, json
NS = '{http://www.collada.org/2005/11/COLLADASchema}'
def scan(path):
    nodes, mats, uvs, geo_uv, up = {}, set(), {}, {}, None
    stack = []; cur_geo = None; inputs = []
    for ev, el in ET.iterparse(path, events=('start', 'end')):
        tag = el.tag.replace(NS, '')
        if ev == 'start':
            if tag == 'node': stack.append([el.get('name'), None, None])
            elif tag == 'geometry': cur_geo = el.get('id'); geo_uv[cur_geo] = 0
            continue
        if tag == 'matrix' and stack: stack[-1][1] = [round(float(v), 4) for v in el.text.split()]
        elif tag == 'instance_geometry' and stack: stack[-1][2] = el.get('url', '')[1:]
        elif tag == 'node':
            n, m, g = stack.pop(); nodes[n] = (m, g)
        elif tag == 'input' and cur_geo and el.get('semantic') == 'TEXCOORD':
            geo_uv[cur_geo] = max(geo_uv[cur_geo], int(el.get('set', '0')) + 1)
        elif tag == 'geometry': cur_geo = None; el.clear()
        elif tag == 'material': mats.add(el.get('name'))
        elif tag == 'up_axis': up = el.text
        elif tag in ('float_array', 'p', 'vcount', 'source'): el.clear()
    return nodes, mats, geo_uv, up
a = scan(sys.argv[1]); b = scan(sys.argv[2]); removed = set(json.load(open(sys.argv[3])).get('removed_names', [])) if len(sys.argv) > 3 else set()
an, am, au, aup = a; bn, bm, bu, bup = b
print('up axis', aup, bup)
print('nodes old/new', len(an), len(bn))
lost = sorted(set(an) - set(bn) - removed); added = sorted(set(bn) - set(an))
print('lost (not intentionally removed):', lost[:20]); print('added:', added[:20])
moved = [n for n in set(an) & set(bn) if an[n][0] and bn[n][0] and max(abs(x - y) for x, y in zip(an[n][0], bn[n][0])) > 1e-3]
print('nodes with changed transform:', len(moved), moved[:10])
uvloss = [n for n in set(an) & set(bn) if an[n][1] and bn[n][1] and au.get(an[n][1], 0) > bu.get(bn[n][1], 0)]
print('nodes that lost a UV set:', len(uvloss), uvloss[:10])
print('materials lost:', sorted(am - bm)[:20], ' added:', sorted(bm - am)[:10])
