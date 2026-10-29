"""Triage a BeamNG vehicle mod folder before touching anything.

usage: audit.py <mod_root> [--usage-out mesh_usage.json] [--json report.json]
  mod_root: the folder that holds vehicles/<id>/ (an extracted mod zip)

Reports: JBeam parse errors and duplicate parts, the main part and config list,
flexbody/prop meshes missing from the mod's own DAE/cdae (they may be vanilla:
check against the game's files or beamng.log), DAE objects no part uses, slots no
part fills, config parts that don't exist in the mod, material image paths that
don't exist in the mod (vanilla paths are listed separately), and leftover paths
to another vehicle folder. --usage-out writes {mesh: [parts]} for the Blender scripts.
"""
import sys, os, re, json, glob, argparse, collections, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jbeam

ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--usage-out'); ap.add_argument('--json')
a = ap.parse_args()
vdirs = [d for d in glob.glob(os.path.join(a.root, 'vehicles', '*')) if os.path.isdir(d) and os.path.basename(d) != 'common']
if not vdirs: sys.exit('no vehicles/<id>/ folder under %s' % a.root)
out = {}

def dae_nodes(path):
    names, mats = set(), set()
    for ev, el in ET.iterparse(path, events=('end',)):
        tag = el.tag.split('}')[-1]
        if tag == 'node' and el.get('name'): names.add(el.get('name'))
        elif tag == 'material' and el.get('name'): mats.add(el.get('name'))
        elif tag in ('float_array', 'p', 'vcount', 'source', 'mesh'): el.clear()
    return names, mats

def cdae_strings(path):  # cdae is binary; object names appear as plain strings
    data = open(path, 'rb').read()
    return set(m.decode('ascii', 'replace') for m in re.findall(rb'[A-Za-z_][A-Za-z0-9_.\-]{2,80}', data))

for vd in vdirs:
    vid = os.path.basename(vd); R = {}
    print('=' * 70); print('vehicle folder:', vid)
    parts, errs = jbeam.load_dir(vd)
    print('parts: %d   parse errors / duplicates: %d' % (len(parts), len(errs)))
    for e in errs[:40]: print('   ', e)
    R['errors'] = errs
    # main part = the one whose slotType is "main"
    mains = [p for p, v in parts.items() if v.get('slotType') == 'main']
    print('main part(s):', mains)
    info = os.path.join(vd, 'info.json')
    if os.path.exists(info):
        try: d = jbeam.parse(open(info, encoding='utf-8', errors='replace').read()); print('info.json default_pc:', d.get('default_pc'))
        except Exception as e: print('info.json parse error:', e)
    # meshes
    names, dmats = set(), set()
    for f in glob.glob(os.path.join(vd, '**', '*.dae'), recursive=True):
        n, m = dae_nodes(f); names |= n; dmats |= m; print('dae: %s  (%d objects)' % (os.path.relpath(f, vd), len(n)))
    cd = set()
    for f in glob.glob(os.path.join(vd, '**', '*.cdae'), recursive=True):
        s = cdae_strings(f); cd |= s; print('cdae: %s  (%d strings; names only, approximate)' % (os.path.relpath(f, vd), len(s)))
    usage = collections.defaultdict(list); missing = collections.defaultdict(list)
    for pn, p in parts.items():
        for sec in ('flexbodies', 'props'):
            for r in jbeam.rows(p.get(sec, [])):
                m = r.get('mesh')
                if not isinstance(m, str) or m in ('SPOTLIGHT', 'POINTLIGHT', 'mesh'): continue
                usage[m].append(pn)
                if m not in names and m not in cd: missing[m].append(pn)
    print('\nmeshes used by parts but not in this mod (%d) - vanilla or truly missing:' % len(missing))
    for m, ps in sorted(missing.items()): print('   %-40s <- %s' % (m, ', '.join(ps[:3])))
    unused = sorted(n for n in names if n not in usage)
    print('\nDAE objects no part uses (%d):' % len(unused), ', '.join(unused[:60]) + (' ...' if len(unused) > 60 else ''))
    R['missing_meshes'] = missing; R['unused_dae_objects'] = unused
    # slots
    provided = {v.get('slotType') for v in parts.values()}
    wanted = collections.Counter()
    for pn, p in parts.items():
        for key in ('slots', 'slots2'):
            for r in jbeam.rows(p.get(key, [])):
                t = r.get('type') or r.get('name')
                if isinstance(t, str): wanted[t] += 1
    empty = sorted(s for s in wanted if s not in provided)
    print('\nslots no part in this mod fills (%d) - fine if vanilla/common provides them:' % len(empty), ', '.join(empty[:60]))
    R['unfilled_slots'] = empty
    # configs
    print('\nconfigs:')
    bad_cfg = {}
    for pc in sorted(glob.glob(os.path.join(vd, '*.pc'))):
        try: d = json.load(open(pc, encoding='utf-8'))
        except Exception as e: print('   %s: NOT STRICT JSON (%s)' % (os.path.basename(pc), e)); continue
        ps = d.get('parts', {})
        unknown = sorted('%s=%s' % (k, v) for k, v in ps.items() if v and v not in parts)
        bad_cfg[os.path.basename(pc)] = unknown
        print('   %-40s model=%s main=%s  parts=%d  not-in-mod=%d' % (os.path.basename(pc)[:40], d.get('model'), d.get('mainPartName'), len(ps), len(unknown)))
    allun = collections.Counter(x for v in bad_cfg.values() for x in v)
    if allun: print('   parts configs pick that the mod lacks (vanilla/common or broken):', ', '.join('%s (x%d)' % kv for kv in allun.most_common(40)))
    R['config_unknown_parts'] = bad_cfg
    # materials and textures
    img_local, img_vanilla, nonstrict = [], collections.Counter(), []
    defined = set()
    for mf in glob.glob(os.path.join(vd, '**', '*.materials.json'), recursive=True):
        txt = open(mf, encoding='utf-8', errors='replace').read()
        try: json.loads(txt)
        except Exception: nonstrict.append(os.path.relpath(mf, vd))
        try: d = jbeam.parse(txt)
        except Exception as e: print('materials parse error', mf, e); continue
        for name, m in d.items():
            if not isinstance(m, dict): continue
            defined.add(m.get('mapTo', name)); defined.add(name)
            for st in m.get('Stages') or []:
                for k, v in (st or {}).items():
                    if not (isinstance(v, str) and v.lower().endswith(('.png', '.dds', '.jpg', '.jpeg', '.tga'))): continue
                    p = v.lstrip('/')
                    if p.startswith('vehicles/%s/' % vid):
                        if not os.path.exists(os.path.join(a.root, p)): img_local.append('%s: %s %s' % (name, k, v))
                    else: img_vanilla[p.split('/')[1] if p.startswith('vehicles/') and p.count('/') > 1 else p.split('/')[0]] += 1
    print('\nmaterial files that are not strict JSON (newer BeamNG may reject):', nonstrict or 'none')
    print('material images pointing inside this mod but missing (%d):' % len(img_local))
    for x in img_local[:40]: print('   ', x)
    print('material images pointing at other folders (vanilla, check in log):', dict(img_vanilla))
    undefined = sorted(m for m in dmats if m not in defined)
    print('DAE materials with no definition in the mod (%d; often vanilla or only on unused objects - check the log):' % len(undefined), ', '.join(undefined[:40]))
    R['missing_images'] = img_local; R['undefined_dae_materials'] = undefined
    # stray paths to other vehicle folders
    stray = collections.Counter()
    for f in glob.glob(os.path.join(vd, '**', '*'), recursive=True):
        if not f.endswith(('.jbeam', '.json', '.pc', '.lua', '.html', '.js')): continue
        for m in re.findall(r'vehicles/([^/"\']+)/', open(f, encoding='utf-8', errors='replace').read()):
            if m != vid: stray[m] += 1
    print('references to other vehicle folders:', dict(stray.most_common(20)))
    # sound
    sc = collections.Counter()
    for pn, p in parts.items():
        for sec in ('soundConfig', 'soundConfigExhaust'):
            s = p.get(sec)
            if isinstance(s, dict) and s.get('sampleName'): sc['%s -> %s' % (sec, s['sampleName'])] += 1
    print('engine sound samples used:', dict(sc))
    out[vid] = R
    if a.usage_out:
        json.dump(usage, open(a.usage_out, 'w'), indent=0); print('\nwrote mesh usage for %d meshes -> %s' % (len(usage), a.usage_out))
if a.json: json.dump(out, open(a.json, 'w'), indent=1, default=list)
