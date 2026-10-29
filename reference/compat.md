# Pass 1–2: triage, compatibility, log loop

## Setup
```bash
SRC=~/Downloads/<source>; W=~/Downloads/<id>_work
mkdir -p "$W" && cp -R "$SRC"/. "$W"/        # or unzip into a NEW empty folder first
python3 -I SKILL/scripts/audit.py "$W" --usage-out "$SCRATCH/mesh_usage.json" | tee "$SCRATCH/audit1.txt"
python3 -I SKILL/scripts/config_matrix.py "$W/vehicles/<id>"
```

## Checklist (from the audit)
- **Vehicle folder id:** lowercase, no spaces -> `rename_vehicle.py` (dry run first).
- **Main part** (`slotType: "main"`): must not share a name with a vanilla vehicle's
  main part. Rename it and set `mainPartName`/`mainPartPath` (`/vehicles/<id>/`) and
  `model` in every `.pc`; `.pc` files are format 2 strict JSON.
- **info.json** `default_pc` must name one of this mod's configs (without `.pc`).
- **Missing meshes:** a flexbody mesh that's neither in the mod's DAE/cdae nor vanilla
  is simply invisible. Options: repoint to an equivalent vanilla mesh of the donor car
  (the mod is often built on a vanilla car: etk800, midsize, sunburst... - its meshes
  load from the game's own files), or leave and list it. Never invent mesh names:
  check the game files the user dumps (PowerShell below) or the log.
- **Duplicate parts:** inside the mod = fix; with other installed mods in
  `/vehicles/common` = not ours, tell the user.
- **Configs picking parts that don't exist:** set them to an existing variant.
- **Materials:** `fix_materials.py` (missing images, unused entries, strict JSON).
  Materials a mesh uses but nobody defines -> map to a defined one (often the donor's
  `<donor>_glass_dmg` etc.). Version 1.5 materials: `Stages` list, `mapTo`.
- **UI/HTML/Lua extras** (nav screens, radios): broken image/font refs, bundled
  commercial music -> remove.
- **Bundled donor data** (e.g. `drivingDynamics/` copied from vanilla) -> remove;
  stale copies break on game updates.
- Rebuild: `cd "$W" && zip -r -X -q ../<id>.zip vehicles art`.

## Log loop (pass 2)
Ask the user to:
1. Delete the old zip from the mods folder, copy the new one in.
2. Start the game, spawn each config family once (and the default), drive a bit.
3. Send `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\beamng.log` (copy it to the Mac).
They don't need to clear the log; it's rewritten each launch.

Then: `grep -n -i -E "<id>|error|warn|missing|failed" beamng.log | grep -v -i other_mod_names`.
Typical lines and fixes:
| Log says | Fix |
|---|---|
| `material ... not found` / `Failed to load texture` | path wrong or file missing -> repoint or drop key |
| `flexbody ... mesh not found` | mesh name (see above) |
| `duplicate part` | rename ours, or ignore if from another mod |
| `slot ... no part` | harmless if optional; else add/point default |
| `please resave` on an old `.cdae` | still loads; re-export later from the DAE |
| JSON/JBeam parse error with line | fix syntax (trailing commas are OK in JBeam, not in `.pc`/`.json` strictness checks) |

## PowerShell snippets for the user (Windows)
Always wrap pipelines in `& { }`. Read files out of the game's zips (they can't be
read from the Mac):
```powershell
& {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $out = "$env:USERPROFILE\Downloads\bng_dump.txt"; '' | Set-Content $out
  $zips = Get-ChildItem "C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content" -Recurse -Filter *.zip
  foreach ($z in $zips) {
    try { $a = [IO.Compression.ZipFile]::OpenRead($z.FullName) } catch { continue }
    foreach ($e in $a.Entries) {
      if ($e.FullName -like 'art/sound/blends/I4*') {     # <- pattern to look for
        $r = New-Object IO.StreamReader($e.Open()); Add-Content $out "===== $($z.Name) :: $($e.FullName)"; Add-Content $out $r.ReadToEnd(); $r.Close()
      }
    }
    $a.Dispose()
  }
}
```
Steam path varies: ask, or `Get-ChildItem C:\,D:\ -Recurse -Filter BeamNG.drive.exe -ErrorAction SilentlyContinue`.
