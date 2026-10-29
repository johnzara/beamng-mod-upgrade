"""Rename a vehicle folder id everywhere (folder with spaces/capitals -> clean lowercase id).

usage: rename_vehicle.py <mod_root> <old_folder_name> <new_id> [--dry-run]

Moves vehicles/<old>/ to vehicles/<new_id>/, rewrites every "/vehicles/<old>/" path
(also the local://local form) in .jbeam/.json/.pc/.lua/.html/.js/.css files, and sets
"model" in each .pc to <new_id>. Paths into art/ need no change.
Renaming the main part (and each .pc's mainPartName/mainPartPath) is a separate,
deliberate step: do it only when the main part clashes with a vanilla one (e.g. etk800).
"""
import os, re, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
src, dst = os.path.join(a.root, 'vehicles', a.old), os.path.join(a.root, 'vehicles', a.new)
assert os.path.isdir(src), src
assert not os.path.exists(dst) or a.old == a.new, dst + ' exists'
pat = re.compile(r'(local://local)?/?vehicles/%s/' % re.escape(a.old))
changed, refs = 0, 0
for dp, _, fs in os.walk(src):
    for f in fs:
        if not f.endswith(('.jbeam', '.json', '.pc', '.lua', '.html', '.js', '.css')): continue
        p = os.path.join(dp, f); t = open(p, encoding='utf-8', errors='surrogateescape').read()
        n, k = pat.subn(lambda m: (m.group(1) or '') + '/vehicles/%s/' % a.new, t)
        if f.endswith('.pc'):
            n, k2 = re.subn(r'("model"\s*:\s*)"%s"' % re.escape(a.old), r'\1"%s"' % a.new, n); k += k2
        if n != t:
            changed += 1; refs += k
            if not a.dry_run: open(p, 'w', encoding='utf-8', errors='surrogateescape').write(n)
if not a.dry_run and a.old != a.new: os.rename(src, dst)
print('%s%d files, %d references%s' % ('[dry run] ' if a.dry_run else '', changed, refs, '' if a.dry_run else ', folder renamed'))
