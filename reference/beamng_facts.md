# BeamNG vehicle mod facts (checked on 0.40.3)

## Layout
```
mod.zip
  vehicles/<id>/            info.json, *.pc, *.jbeam (any subfolders), *.dae / *.cdae,
                            *.materials.json, textures, ui html/lua
  vehicles/common/          shared parts (other mods put things here too -> duplicate-part noise)
  art/sound/blends/         *.sfxBlend2D.json
  art/sound/engine/<id>/    WAV loops
```
User mods folder: `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\` (one zip per mod;
remove the old zip when replacing, or both load). Log: `...\current\beamng.log`.

## JBeam
- Relaxed JSON: comments, missing/trailing commas OK. Parse with `scripts/jbeam.py`.
- Part = top-level key; `slotType` = which slot it fits; `slots` table
  `["type","default","description"]` lists child slots; `"main"` slotType = root.
- `flexbodies` table: `["mesh", "[group]:", "nonFlexMaterials"]`, rows bind a mesh name
  to node groups. `props` = moving meshes (needles, wheel...).
- Table rows can carry inline `{...}` modifier dicts that apply to following rows.
- Engines: `mainEngine` (torque curve, `maxRPM`, `idleRPM`, inertia, `turbocharger`
  name), `soundConfig`/`soundConfigExhaust`. ECU parts set `revLimiterRPM`.
- Turbo: a part with a `"turbocharger": {...}` section (pressurePSI by turbine rpm,
  engineDef efficiency curve, sounds) and `mainEngine.turbocharger` naming it.

## .pc configs (format 2, strict JSON)
`{"format":2,"model":"<id>","mainPartName":"<main>","parts":{"slot":"part",...},"vars":{},"paints":[...]}`
A slot missing from `parts` takes the slot's default. `""` = empty slot.

## Materials (`*.materials.json`, version 1.5)
`{"name":{"name":..,"mapTo":..,"class":"Material","version":1.5,"Stages":[{...},{},{},{}],...}}`
Stage keys: `baseColorMap`, `normalMap`, `roughnessMap`, `metallicMap`, `opacityMap`,
`colorPaletteMap`, `ambientOcclusionMap`, `baseColorFactor`, `instanceDiffuse` ...
Vanilla texture paths (`/vehicles/etk800/...`) load from the game; keep them.
Damage swaps: JBeam `deformMaterialBase` / `deformMaterialDamaged` name materials.

## Engine sound blend
See `sound.md`. `event:>Engine>default` + `samples:[[off],[on]]`.

## Powertrain realism pass (when asked)
Source real data (manufacturer torque/power, redline, gear ratios, final drive,
weights) and say where each number came from. Typical mod problem: engine copied from
a vanilla car with that car's curves and redline (the Saab "2.8 V6" was the ETK V8
tune, 9000 rpm, 24 psi). Change torque curve, maxRPM/revLimiter, inertia, turbo
pressure curve, gearbox ratios; keep a CHANGES entry per config family.

## HD damage pass (when asked)
Means a denser body node/beam structure fitted to the mesh (more nodes on panels,
proper deformGroups, breakGroups for doors/hood/bumpers). Big job: plan it with the
user, start from the donor vanilla car's JBeam structure, and test one panel first.
