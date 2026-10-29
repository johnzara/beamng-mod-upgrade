"""Triangles a spawned config draws from the mod's own model, and its heaviest meshes.

usage: config_tris.py <vehicle_dir> <mesh_stats.json> [config.pc ...]
  mesh_stats.json: output of blender/bl_analyze.py ([{name, tris}, ...])
  no configs given -> all *.pc in vehicle_dir
Vanilla meshes (not in the stats) count as 0.
"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jbeam
root, stats, pcs = sys.argv[1], sys.argv[2], sys.argv[3:] or sorted(os.path.basename(p) for p in glob.glob(os.path.join(sys.argv[1], '*.pc')))
parts, _ = jbeam.load_dir(root)
tris = {x['name']: x['tris'] for x in json.load(open(stats))}
def resolve(pc):
    d = json.load(open(os.path.join(root, pc)))
    chosen = d['parts']
    main = d.get('mainPartName') or next(p for p, v in parts.items() if v.get('slotType') == 'main')
    used, stack = [], [main]
    while stack:
        pn = stack.pop()
        if pn not in parts or pn in used: continue
        used.append(pn)
        for key in ('slots', 'slots2'):
            for r in jbeam.rows(parts[pn].get(key, [])):
                slot = r.get('type') or r.get('name')
                pick = chosen.get(slot, r.get('default'))
                if pick: stack.append(pick)
    meshes = set()
    for pn in used:
        for sec in ('flexbodies', 'props'):
            for r in jbeam.rows(parts[pn].get(sec, [])):
                if isinstance(r.get('mesh'), str): meshes.add(r['mesh'])
    return used, meshes
for pc in pcs:
    used, meshes = resolve(pc)
    t = sum(tris.get(m, 0) for m in meshes)
    top = sorted(((tris.get(m, 0), m) for m in meshes), reverse=True)[:8]
    print('%-40s parts=%d meshes=%d mod-model tris=%d' % (pc[:40], len(used), len(meshes), t))
    print('    heaviest:', ', '.join('%s %dk' % (m, v // 1000) for v, m in top))
