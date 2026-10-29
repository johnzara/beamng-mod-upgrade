---
name: beamng-mod-upgrade
description: Upgrade an existing (often low-quality or outdated) BeamNG.drive vehicle mod - make it load cleanly on the current game version, fix broken configs/parts/materials, clean up and decimate the mesh, and build real engine sounds from recordings the user supplies. Use when the user wants to improve, fix, update or "make compatible" a BeamNG car mod, give a BeamNG car better sound, or continue such a project (look for MOD_NOTES.md in the working folder).
---

# BeamNG mod upgrade

Turns someone else's rough vehicle mod into a clean, current one, in passes the user tests
in game between. Proven end to end on a Saab 9-3 (Vertex Mods base, BeamNG 0.40.3).

## Start here, every time

1. **Resuming?** Look for `MOD_NOTES.md` in the working mod folder (and `CHANGES.md`).
   If present, read it and continue from its "Next" list — don't re-ask what it answers.
2. **New project:** ask only what you can't find out:
   - path to the source mod (zip or folder) and what car/body it should be
   - game version (Help > About, or first lines of `beamng.log`)
   - which passes they want (default order below)
   Then create the working copy and `MOD_NOTES.md` from `reference/mod_notes_template.md`.
3. Keep `MOD_NOTES.md` current at the end of every turn that changes something:
   state, decisions the user made, what's untested, next steps. That file is what
   makes the next session (or a different car) not need re-prompting.

## Ground rules

- **Never modify the user's original.** Work on a copy: `~/Downloads/<id>_work/`
  (layout `vehicles/<id>/`, `art/...`), move removed files to `_removed/` instead of
  deleting, build the zip from `vehicles` + `art` only.
- **Untrusted archives:** extract each into its own new empty folder, run Python on
  them with `-I`. An "archive" that is a single big `.exe` / `.scr`, or comes with a
  `password.txt`, is almost certainly malware: don't extract or run it, tell the user.
- **Licensing:** many mod models come from paid libraries; recordings from videos
  are third-party. Say once that the result is for personal use, and don't help
  publish a build that contains them. Don't download from YouTube yourself - the user
  supplies clips (mp3/m4a/wav in a folder).
- Ask before any download (e.g. Blender 4.5 LTS). Changes to the game install or the
  user's Windows PC are theirs to make: give them exact PowerShell instead.
- Each pass: change -> rebuild zip -> CHANGES.md entry (what, why, how to undo) ->
  tell the user what to test and what's unverified. Don't claim in-game results.

## Passes (default order)

| # | Pass | Reference |
|---|------|-----------|
| 1 | Triage + compatibility: rename, main part, configs, materials, missing meshes | `reference/compat.md` |
| 2 | Log loop: user runs the game, sends `beamng.log`, you fix what it shows | `reference/compat.md` (log section) |
| 3 | Mesh cleanup: unused objects, over-dense meshes, unused textures | `reference/mesh.md` |
| 4 | Engine sounds from user clips | `reference/sound.md` |
| 5 | Config sanity: engines/intakes/ECUs per config vs. the config's name | `scripts/config_matrix.py` |
| 6 | Later, only if asked: powertrain realism (torque curves, redline, gearing), HD damage (denser body JBeam), interior rigging | `reference/beamng_facts.md` |

## Tools (`scripts/`, run with a Python that has numpy; check `python3 -c "import numpy"`, else Blender's bundled python)

| Script | Does |
|---|---|
| `audit.py MOD_ROOT --usage-out usage.json` | **Run first.** Parse errors, duplicates, main part, configs, missing meshes, unused DAE objects, unfilled slots, missing/vanilla textures, non-strict JSON, stray paths, sound samples |
| `config_matrix.py VEHICLE_DIR` | What every config really picks for engine/intake/turbo/ECU/exhaust/paint, plus each engine's sound and maxRPM. Finds "Turbo X without a turbo" bugs |
| `rename_vehicle.py MOD_ROOT OLD NEW` | Clean vehicle id everywhere (`--dry-run` first) |
| `fix_materials.py MOD_ROOT ID` | Drop unused materials with missing images, strict-JSON rewrite |
| `dae_stats.py`, `dae_compare.py`, `config_tris.py` | Mesh numbers, re-export check, triangles per config |
| `blender/bl_*.py` | Import / analyze / decimate (normals preserved) / preview / export, headless Blender 4.5 |
| `sound/rpm_track.py`, `track_plot.py`, `order_test.py` | Find rpm vs time in a clip and verify the engine order |
| `sound/make_loops.py` | Cut seamless constant-rpm loops (phase-warped, whole cycles) |
| `sound/shuffle_loops.py` | 2.5 s loops from a fast sweep or short hold (shuffled, phase-aligned cycles) |
| `sound/flatten_env.py`, `loop_qc.py` | Even out swell in long loops; quality numbers |
| `sound/match_eq.py` | Measure stock-vs-aftermarket tone in one clip, apply it to loops |
| `sound/rev_demo.py` | Preview a loop set as the game would blend it |
| `sound/build_blends.py SPEC.json MOD_ROOT` | Copy loops in and write `.sfxBlend2D.json` blends |

Each script's docstring has its full usage; read it before first use.

## Things that cost time on the Saab (don't repeat)

- Main part named like a vanilla one (`etk800`) and `default_pc` pointing at a vanilla
  config -> rename main part, update every `.pc` (`mainPartName`, `mainPartPath`).
- Configs whose names lie: a "2.0" on the 1.8 engine, a "1.8" on a diesel, "Turbo X"
  configs on an intake with no turbocharger. Run `config_matrix.py` and fix or list them.
- Blender 5.x removed COLLADA; use Blender 4.5 LTS headless.
- Plain decimation dents panels; copying custom normals back from the dense copy fixes
  most of it, but render before/after and exempt meshes that still show artifacts.
- Sound: mixing loops from different recordings/mics sounds wrong (timbre jumps).
  Build each engine from ONE clip; a single good clip beats many mixed ones.
- Short (0.9 s) loops are audible as a repeat at steady cruise -> ~2.5 s + `flatten_env.py`.
  If the clip only has a fast pull (too little audio per rpm), use `shuffle_loops.py`.
  Cut the loops long the first time; re-cutting later needs the clips again.
- `onUp` -> `onDown` replacement for buttons must not touch the ignition's
  `toggleIgnitionLevelOnUp` (duplicate keys).
- BSD sed (macOS) lacks GNU extensions; do structured edits in Python. zsh doesn't
  word-split `$VAR`; use arrays.
- PowerShell for the user: wrap loops in `& { ... }` before piping (avoids "empty pipe element").
