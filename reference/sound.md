# Pass 4: engine sounds from user clips

## What BeamNG 0.40 expects (mod engine sound)
- `art/sound/blends/<name>.sfxBlend2D.json`:
  `{"header":{"version":1},"eventName":"event:>Engine>default","samples":[[OFF-LOAD...],[ON-LOAD...]]}`
  each entry `["art/sound/engine/<id>/<folder>/<file>.wav", rpm]`, **off-load list first**.
- WAVs: mono, 48 kHz, 16-bit PCM, seamless loops at a constant rpm.
- The engine part: `"soundConfig": {"sampleName": "<name_engine>", ...}` and
  `"soundConfigExhaust": {"sampleName": "<name_exhaust>", ...}`. Useful keys:
  `mainGain` (dB), `fundamentalFrequencyCylinderCount` (real cylinder count),
  `onLoadGain`/`offLoadGain`, EQ shelves. When both layers come from the same
  recording, put the engine layer ~12–18 dB under the exhaust (e.g. -15.5 vs +2.5).
- Vanilla blends (e.g. `I4_3_engine`) are 115-byte stubs pointing at FMOD events -
  they can't be edited, only replaced by your own blend name.
- Intake/exhaust parts can carry `soundConfig` overrides (`intakeMuffling`,
  `exhaustAudioGainChange`) and turbo sounds (`bovSoundFileName`, `whineLoopEvent`).

## Getting clips
User supplies them (mp3/m4a from videos is fine). Best sources, in order:
1. dyno pulls (steady load, clean sweep), 2. steady holds at several rpm,
3. exterior drive-bys with clear revs. Note per clip: engine, mods (stock/catback/
tuned), mic position, and useful time ranges. Same car + same mic for a whole engine.

## Pipeline
```bash
K=SKILL/scripts/sound; PY=<python with numpy>
# 1. look: where are pulls, coasts, idle?
ffmpeg -i clip.mp3 -lavfi showspectrumpic=s=1600x600:legend=1 $SCR/spec.png
$PY -I $K/rpm_track.py clip.mp3 $SCR/track.json 0 0
$PY -I $K/track_plot.py clip.mp3 $SCR/track.json $SCR/plot.ppm 2 "clip" && sips -s format png $SCR/plot.ppm --out $SCR/plot.png
$PY -I $K/order_test.py clip.mp3 $SCR/track.json
#    pick ORDER so idle/redline make sense (I4 2, V6 3; tracker may sit on 1.5 for a V6)
# 2. cut loops: one pull for on-load, coast-downs for off-load, a steady idle
$PY -I $K/make_loops.py clip.mp3 $SCR/track.json --order 2 --t0 12.0 --t1 18.5 --rpm 2500 6500 500 --out $SCR/loops --prefix car --load onload --loop-sec 2.5
$PY -I $K/flatten_env.py 0.8 0.25 $SCR/loops $SCR/loops_f
$PY -I $K/loop_qc.py $SCR/loops_f/*.wav
# 3. listen before installing
$PY -I $K/rev_demo.py $SCR/demo.wav $SCR/loops_f/car_onload '900:900:2,900:6500:5,6500:6500:2,6500:1200:4'
ffmpeg -y -v error -i $SCR/demo.wav -c:a aac -b:a 192k ~/Downloads/<preview>.m4a      # give the user this
# 4. install + blends (write spec.json first, see build_blends.py docstring)
$PY -I $K/build_blends.py $SCR/spec.json "$W"
#    then set sampleName in the engine JBeam(s) and rebuild the zip
```

## Stock vs aftermarket from one clip
If a clip has the stock exhaust briefly then a louder one (same car/mic): measure
pairs at matching rpm, then apply the cut to loops from the loud part:
```bash
$PY -I $K/match_eq.py measure clip.mp3 $SCR/eq.json --target 8.9 10 12.9 14.3 --ref 27 29 23 27
$PY -I $K/match_eq.py apply $SCR/eq.json $SCR/loops_f $SCR/loops_stock
```

## Lessons
- One recording per engine. Mixing mics/cars gave a "weird above 5000" sound
  (bright front-mic loops next to dark dyno loops). Check `loop_qc.py` centroids:
  neighbours should be in the same range.
- Loops 2–2.5 s, flattened. 0.9 s loops repeat audibly at cruise.
- Fast pull (e.g. 2500->6000 in 3 s, ~0.4 s per rpm) or a hold shorter than the loop:
  `shuffle_loops.py` (same args as make_loops; `--spread 0.08 --grain 1 2` for the
  fastest part of a sweep, `--grain 3 6` for holds). Check: run rev_demo at a steady
  rpm and look at the envelope spectrum; a strong peak at 1/old-loop-length Hz = repeat.
  Saab 2.0T: 2 Hz peak 12-19x background with 0.5 s loops, 3-4x (none) after shuffling.
- Check a hold segment's level per 0.1 s before using it: coasts often end with a
  clutch/throttle drop (Saab 2000 rpm coast: -12 dB in its last 0.7 s).
- Off-load: real coast-down loops if the clip has steady coasts; else reuse on-load.
- The top loop gets pitched up for rpm above it; that's fine for a few hundred rpm.
- Octave errors on fast blips: the tracker jumps; detect by continuity and skip.
- Gains: get them close, then tune from the user's in-game feedback.
- Turbo/BOV sounds come from the intake part, not the engine sound - a "turbo" car
  on a non-turbo intake sounds flat (see config_matrix.py).
