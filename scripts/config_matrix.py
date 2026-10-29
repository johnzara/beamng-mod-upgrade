"""Table of what every config actually picks for the slots that matter.

usage: config_matrix.py <vehicle_dir> [--slots REGEX]
  default REGEX: engine|intake|turbo|super|ecu|exhaust|transmission|internals|paint_design

This is how config mistakes show up: a "Turbo X" on a non-turbo intake, a "2.0" on
the 1.8 engine, a "1.8" on a diesel. A part that the slot's default would pick is
shown as (default ...). A slot nobody sets is resolved from its default.
For each engine part the soundConfig/soundConfigExhaust sampleName and maxRPM are listed too.
"""
import sys, os, re, json, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jbeam
ap = argparse.ArgumentParser(); ap.add_argument('vdir')
ap.add_argument('--slots', default=r'engine|intake|turbo|super|ecu|exhaust|transmission|internals|paint_design')
a = ap.parse_args()
parts, _ = jbeam.load_dir(a.vdir)
pat = re.compile(a.slots, re.I)

def resolve(chosen, main):
    picks, stack, seen = {}, [main], set()
    while stack:
        pn = stack.pop()
        if pn in seen or pn not in parts: continue
        seen.add(pn)
        for key in ('slots', 'slots2'):
            for r in jbeam.rows(parts[pn].get(key, [])):
                slot = r.get('type') or r.get('name')
                if not isinstance(slot, str): continue
                if slot in chosen: pick = chosen[slot]
                else: pick = r.get('default'); pick = ('(default) ' + pick) if pick else ''
                picks[slot] = pick
                real = pick.replace('(default) ', '') if isinstance(pick, str) else ''
                if real: stack.append(real)
    return picks

rows = []
for pc in sorted(glob.glob(os.path.join(a.vdir, '*.pc'))):
    d = json.load(open(pc, encoding='utf-8'))
    picks = resolve(d.get('parts', {}), d.get('mainPartName') or next((p for p, v in parts.items() if v.get('slotType') == 'main'), None))
    rows.append((os.path.basename(pc)[:-3], {k: v for k, v in picks.items() if pat.search(k) and v}))
slots = sorted({k for _, p in rows for k in p})
for name, p in rows:
    print('\n' + name)
    for s in slots:
        if s in p:
            real = p[s].replace('(default) ', '')
            tag = ''
            if 'intake' in s.lower() and real in parts:
                tag = '   [turbo]' if 'turbocharger' in parts[real] else '   [supercharger]' if 'supercharger' in parts[real] else '   [NO turbo/supercharger]'
            print('    %-38s %s%s' % (s, p[s], tag))
print('\nengine parts:')
for pn, p in sorted(parts.items()):
    sc, se = p.get('soundConfig'), p.get('soundConfigExhaust')
    if isinstance(sc, dict) and sc.get('sampleName') or isinstance(se, dict) and se.get('sampleName'):
        rpm = (p.get('mainEngine') or {}).get('maxRPM') if isinstance(p.get('mainEngine'), dict) else None
        print('    %-36s slot=%-28s maxRPM=%s  engine=%s  exhaust=%s' % (pn, p.get('slotType'), rpm,
              (sc or {}).get('sampleName'), (se or {}).get('sampleName')))
print('\nintake parts:')
for pn, p in sorted(parts.items()):
    if 'intake' in str(p.get('slotType', '')).lower():
        print('    %-44s %s  name=%s' % (pn, 'turbo' if 'turbocharger' in p else 'supercharger' if 'supercharger' in p else 'NA', (p.get('information') or {}).get('name')))
