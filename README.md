# beamng-mod-upgrade

A [Claude Code](https://claude.com/claude-code) skill for upgrading an existing, rough
BeamNG.drive vehicle mod: get it loading cleanly on the current game version, fix broken
configs/parts/materials, clean up and decimate the mesh, and build real engine sounds
from recordings you supply. Built and tested on a Saab 9-3 mod on BeamNG 0.40.3.

## Install

```bash
git clone https://github.com/johnzara/beamng-mod-upgrade ~/.claude/skills/beamng-mod-upgrade
```

(If you use a custom `CLAUDE_CONFIG_DIR`, clone into its `skills/` folder instead.)
New Claude Code sessions pick it up automatically.

## Use

Ask in plain words, e.g.

> Upgrade the BeamNG mod in ~/Downloads/volvo_v70. Focus on the wagon. Sound clips are in ~/Downloads/volvo sounds.

or start with `/beamng-mod-upgrade`. Claude works on a copy, runs `scripts/audit.py`
first, and keeps a `MOD_NOTES.md` in the working folder so a later session can continue
with "continue the Volvo mod".

## What's inside

- `SKILL.md`: the workflow (passes, ground rules, lessons learned)
- `reference/`: BeamNG 0.40 file formats, compatibility/log fixes, mesh pipeline, engine sound pipeline, notes template
- `scripts/`: mod audit, config matrix, vehicle rename, material fixes, mesh stats and comparison
- `scripts/blender/`: headless Blender 4.5 import / analyze / decimate / preview / export
- `scripts/sound/`: rpm tracking, loop cutting (`make_loops.py`, `shuffle_loops.py` for fast sweeps), envelope flattening, QC, stock-vs-aftermarket EQ, rev demo, blend builder

## Requirements

- Python 3 with numpy
- ffmpeg
- Blender 4.5 LTS for the mesh pass (5.x has no COLLADA)

The game itself can run on another machine: you copy the zip over and send back `beamng.log`.

## Note on assets

Vehicle mods often contain models from paid libraries, and engine recordings taken from
videos belong to their authors. This skill is for personal-use upgrades. It contains
no models or sounds itself.
