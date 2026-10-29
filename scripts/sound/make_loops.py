"""Cut constant-rpm, seamless engine loops out of a recorded rev sweep or a steady hold.

usage: make_loops.py CLIP TRACK.json --order N --t0 S --t1 S --rpm LO HI STEP --out DIR --prefix NAME --load onload|offload|idle [--loop-sec 2.5] [--fade 6]
  TRACK.json: rpm_track.py output for the same clip
  --order: engine orders the tracked f0 represents (rpm = f0*60/order). Firing order is
           cylinders/2 (I4 = 2, V6 = 3) but the tracker can lock onto another order
           (e.g. 1.5 on a V6): check with track_plot.py / order_test.py and a known rpm.
  --t0/--t1: the part of the clip to use (one pull, one coast, one hold)

Each loop is phase-warped to exactly the target rpm (pitch is flat), cut to a whole
number of engine cycles (2 revs), and its extra tail is crossfaded into its head so
it wraps without a click. Output: DIR/<prefix>_<load>_<rpm>.wav, 48 kHz mono 16-bit,
RMS-normalised to -15 dBFS. Skipped rpms are those the clip segment doesn't cover with
enough audio around them; shorten --loop-sec for fast sweeps.

Loop length: 0.9 s loops are audible as a repeat at steady cruise. Use ~2.5 s where
the source allows it, then run flatten_env.py to remove the slow volume swell a long
window of a sweep picks up, and loop_qc.py to check.
"""
import argparse, json, subprocess, wave, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('track')
ap.add_argument('--order', type=float, required=True)
ap.add_argument('--t0', type=float, required=True); ap.add_argument('--t1', type=float, required=True)
ap.add_argument('--rpm', type=float, nargs=3, metavar=('LO', 'HI', 'STEP'), required=True)
ap.add_argument('--out', required=True); ap.add_argument('--prefix', required=True); ap.add_argument('--load', required=True)
ap.add_argument('--loop-sec', type=float, default=2.5); ap.add_argument('--fade', type=int, default=6, help='crossfade = loop/N')
a = ap.parse_args()
import os; os.makedirs(a.out, exist_ok=True)
SR = 48000
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', a.clip, '-ac', '1', '-ar', str(SR),
     '-af', 'highpass=f=22,lowpass=f=14000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout, dtype=np.float32).astype(np.float64)
d = json.load(open(a.track)); t = np.array(d['t']); rpm = np.array(d['f0']) * 60 / a.order
sel = (t >= a.t0) & (t <= a.t1); t, rpm = t[sel], rpm[sel]
assert len(t) > 8, 'no tracked frames between t0 and t1'
k = np.ones(7) / 7; rpm = np.convolve(np.pad(rpm, 3, mode='edge'), k, mode='valid')   # light smoothing
ts = np.arange(int(t[0] * SR), int(t[-1] * SR)) / SR
r_s = np.interp(ts, t, rpm)
phase = np.cumsum(r_s / 120.0) / SR            # engine cycles (2 revs each)
seg_x = x[int(t[0] * SR):int(t[0] * SR) + len(ts)]
lo, hi, step = a.rpm
print('segment rpm %d-%d over %.1f s' % (r_s.min(), r_s.max(), t[-1] - t[0]))
for R in np.arange(lo, hi + 1, step):
    if not (r_s.min() <= R <= r_s.max()): print('  %5d rpm  skipped: outside segment' % R); continue
    centre = np.abs(np.arange(len(r_s)) - len(r_s) / 2) / len(r_s)     # prefer crossings near the middle
    i_c = int(np.argmin(np.abs(r_s - R) / R + 0.05 * centre))
    cyc_len = 120.0 / R
    n_cyc = max(4, int(round(a.loop_sec / cyc_len)))
    fade_cyc = max(1, n_cyc // a.fade)
    need = n_cyc + fade_cyc
    p0 = phase[i_c] - need / 2
    if p0 < phase[0] or p0 + need > phase[-1]: print('  %5d rpm  skipped: not enough audio around it (try a shorter --loop-sec)' % R); continue
    n_out = int(round(need * cyc_len * SR))
    p_grid = p0 + np.arange(n_out) / (cyc_len * SR)
    src_t = np.interp(p_grid, phase, np.arange(len(phase)))
    y = np.interp(src_t, np.arange(len(seg_x)), seg_x)
    L = int(round(n_cyc * cyc_len * SR)); F = n_out - L
    fade = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, F))
    loop = y[:L].copy(); loop[:F] = y[:F] * fade + y[L:L + F] * (1 - fade)
    loop *= 0.18 / (np.sqrt(np.mean(loop ** 2)) + 1e-9)
    pk = np.abs(loop).max()
    if pk > 0.98: loop *= 0.98 / pk
    name = '%s/%s_%s_%04d.wav' % (a.out, a.prefix, a.load, R)
    with wave.open(name, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(loop, -1, 1) * 32767).astype('<i2').tobytes())
    half = int(need * cyc_len * SR / 2); spread = r_s[max(0, i_c - half):i_c + half]
    print('  %5d rpm  loop %.2fs  (source rpm %d-%d)' % (R, L / SR, spread.min(), spread.max()))
