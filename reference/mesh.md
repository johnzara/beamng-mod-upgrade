# Pass 3: mesh and texture cleanup

Blender **4.5 LTS** (5.x has no COLLADA). macOS binary:
`/Applications/Blender 4.5.app/Contents/MacOS/Blender`; its python (with numpy):
`/Applications/Blender 4.5.app/Contents/Resources/4.5/python/bin/python3.11`.
Ask before downloading it (blender.org, ~400 MB). The Blender MCP may not be connected;
headless CLI is enough.

```bash
B="/Applications/Blender 4.5.app/Contents/MacOS/Blender"; K=SKILL/scripts
python3 -I $K/dae_stats.py model.dae $SCR/dae.json                 # quick numbers
python3 -I $K/audit.py "$W" --usage-out $SCR/usage.json            # which meshes parts use
"$B" -b --python $K/blender/bl_import.py -- model.dae $SCR/orig.blend
"$B" -b $SCR/orig.blend --python $K/blender/bl_analyze.py -- $SCR/stats.json $SCR/usage.json
python3 -I $K/config_tris.py "$W/vehicles/<id>" $SCR/stats.json   # tris per spawned config
"$B" -b $SCR/orig.blend --python $K/blender/bl_decimate.py -- $SCR/usage.json $SCR/dec.blend $SCR/dec.json [caps.json]
"$B" -b $SCR/orig.blend --python $K/blender/bl_preview.py -- $SCR/prev before OBJ1 OBJ2 ...
"$B" -b $SCR/dec.blend  --python $K/blender/bl_preview.py -- $SCR/prev after  OBJ1 OBJ2 ...
# look at the PNGs side by side; add artifacting objects to "keep" in caps.json and redo
"$B" -b $SCR/dec.blend --python $K/blender/bl_export.py -- $SCR/new.dae
python3 -I $K/dae_compare.py model.dae $SCR/new.dae $SCR/dec.json   # names/transforms/UVs intact?
```
Blender may end with `Error: Not freed memory blocks ...`: harmless.
Then move the original DAE to `_removed/`, put the new one in place under the same name.

Targets that worked (Saab): whole model 3.7M -> 2.6M tris, a spawned car ~0.9M.
Interior props (steering wheels, radios, headliners, seats) are usually the most
over-dense. Keep at full detail anything that showed artifacts in previews (on the
Saab: dashboard, engine, upper trim, body shell, quarter panels).

Rules:
- Never rename objects or change transforms: JBeam flexbodies bind by name and position.
- Keep all UV sets (damage/decals use UV2) and vertex colours.
- Objects shared by several parts: decimate the datablock once.
- Delete only objects no part references AND that have no children.

## Textures
Unused images: list every image path referenced by `*.materials.json`, `.jbeam`,
`.html/.css/.js` in the mod; images in the folder that nothing references -> `_removed/`.
Also move local copies of vanilla textures the materials actually load from the
game's own paths, and duplicate `_Normal` / `_Normal_DirectX` sets. Saved 330 MB on the Saab.
