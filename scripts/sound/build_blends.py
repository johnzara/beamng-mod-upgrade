"""Install loops into a mod and write BeamNG 0.40 engine sound blends from a JSON spec.

usage: build_blends.py SPEC.json MOD_ROOT [--dry-run]

SPEC.json:
{
  "vehicle": "saab93",                      # sound folder: art/sound/engine/<vehicle>/<folder>/
  "loops": "/path/to/loops",                # where the WAVs are
  "blends": {
    "saab93_b284_exhaust": {
      "folder": "b284",
      "offload": [["b284ext_idle_1350.wav", 1350], ["b284dyno_onload_2500.wav", 2500]],
      "onload":  [["b284ext_idle_1350.wav", 1350], ["b284dyno_onload_2500.wav", 2500]]
    }
  }
}
Each blend becomes art/sound/blends/<name>.sfxBlend2D.json with
{"header":{"version":1},"eventName":"event:>Engine>default","samples":[[off-load...],[on-load...]]}
(off-load list FIRST). Point the engine's soundConfig / soundConfigExhaust "sampleName"
at <name>. An off-load list may reuse on-load loops if there are no real coast loops.
"""
import os, json, shutil, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('mod'); ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
spec = json.load(open(a.spec)); vid = spec['vehicle']; loops = spec['loops']
copied = set(); bdir = os.path.join(a.mod, 'art/sound/blends')
for name, b in spec['blends'].items():
    folder = b['folder']; rel = 'art/sound/engine/%s/%s' % (vid, folder); d = os.path.join(a.mod, rel)
    for f, _ in b['offload'] + b['onload']:
        src = os.path.join(loops, f); assert os.path.exists(src), 'missing loop ' + src
        if (folder, f) not in copied:
            if not a.dry_run: os.makedirs(d, exist_ok=True); shutil.copy2(src, os.path.join(d, f))
            copied.add((folder, f))
    lst = lambda xs: [['%s/%s' % (rel, f), int(r)] for f, r in sorted(xs, key=lambda x: x[1])]
    blend = {'header': {'version': 1}, 'eventName': 'event:>Engine>default', 'samples': [lst(b['offload']), lst(b['onload'])]}
    if not a.dry_run:
        os.makedirs(bdir, exist_ok=True); json.dump(blend, open(os.path.join(bdir, '%s.sfxBlend2D.json' % name), 'w'), indent=2)
    on = [r for _, r in b['onload']]
    print('%-28s off-load %2d, on-load %2d samples (%d-%d rpm)' % (name, len(b['offload']), len(b['onload']), min(on), max(on)))
print('%swav files: %d' % ('[dry run] ' if a.dry_run else '', len(copied)))
