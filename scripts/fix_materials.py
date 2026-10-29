"""Clean *.materials.json: drop material entries nobody uses whose images are missing,
drop missing image keys from used ones, and rewrite every file as strict JSON.

usage: fix_materials.py <mod_root> <vehicle_id> [--dry-run]
"Used" = the name/mapTo appears in a DAE material, in a cdae's strings, or quoted in
any .jbeam/.pc (skins, damage materials). Only images under /vehicles/<id>/ are
checked; vanilla paths are left alone (verify those with beamng.log).
Keep the originals: copy the files to _removed/ first.
"""
import sys, os, re, glob, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jbeam
ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('vid'); ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
vd = os.path.join(a.root, 'vehicles', a.vid)
used = set()
for f in glob.glob(os.path.join(vd, '**', '*.dae'), recursive=True):
    used |= set(re.findall(r'<material[^>]*\bname="([^"]+)"', open(f, encoding='utf-8', errors='replace').read()))
    used |= set(re.findall(r'<material[^>]*\bid="([^"]+?)(?:-material)?"', open(f, encoding='utf-8', errors='replace').read()))
for f in glob.glob(os.path.join(vd, '**', '*.cdae'), recursive=True):
    used |= set(m.decode('ascii', 'replace') for m in re.findall(rb'[A-Za-z_][A-Za-z0-9_.\-]{2,80}', open(f, 'rb').read()))
jtext = ''.join(open(p, encoding='utf-8', errors='replace').read() for p in glob.glob(os.path.join(vd, '**', '*.jbeam'), recursive=True) + glob.glob(os.path.join(vd, '*.pc')))
prefix = '/vehicles/%s/' % a.vid
log = []
for mf in glob.glob(os.path.join(vd, '**', '*.materials.json'), recursive=True):
    txt = open(mf, encoding='utf-8', errors='replace').read()
    d = jbeam.parse(txt); changed = False
    try: json.loads(txt)
    except Exception: changed = True; log.append('not strict JSON, rewriting: ' + os.path.relpath(mf, vd))
    for name in list(d):
        m = d[name]
        if not isinstance(m, dict): continue
        missing = [(i, k) for i, st in enumerate(m.get('Stages') or []) for k, v in (st or {}).items()
                   if isinstance(v, str) and v.startswith(prefix) and not os.path.exists(os.path.join(a.root, v.lstrip('/')))]
        if not missing: continue
        mt = m.get('mapTo', name)
        if mt not in used and name not in used and ('"%s"' % mt) not in jtext and ('"%s"' % name) not in jtext:
            del d[name]; log.append('removed unused material %s' % name)
        else:
            for i, k in missing: del m['Stages'][i][k]
            log.append('dropped missing %s from %s' % ('/'.join(k for _, k in missing), name))
        changed = True
    if changed and not a.dry_run:
        json.dump(d, open(mf, 'w', encoding='utf-8'), indent=2); log.append('rewrote ' + os.path.relpath(mf, vd))
print(('[dry run]\n' if a.dry_run else '') + '\n'.join(log or ['nothing to do']))
