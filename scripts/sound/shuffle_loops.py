"""Build long constant-rpm loops from a fast rev sweep (or a short hold) by shuffling engine cycles.

usage: shuffle_loops.py CLIP TRACK.json --order N --t0 S --t1 S --rpm LO HI STEP --out DIR --prefix NAME --load L
                        [--loop-sec 2.5] [--spread 0.05] [--grain 2 4] [--xfade 0.25] [--seed 1]

make_loops.py needs loop-sec of audio around each rpm. A quick pull (2500->6000 rpm in
3 s) only has ~0.4 s near any rpm, and 0.5 s loops repeat audibly at cruise. This takes
every engine cycle within +-spread of the target rpm, phase-warps them to exactly that
rpm, and strings random runs of GRAIN consecutive cycles together (each run aligned to
the previous one by cross-correlation, joined with a crossfade of XFADE cycles) into a
loop of loop-sec that wraps seamlessly. The shortest repeat the ear can lock onto is then
the whole loop. Grain levels are evened out (the sweep gets louder with rpm).
Output names/format match make_loops.py. Afterwards: flatten_env.py, loop_qc.py, and
compare centroids with make_loops.py output from the same segment (should be close).
"""
import argparse, json, os, subprocess, wave, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('track')
ap.add_argument('--order', type=float, required=True)
ap.add_argument('--t0', type=float, required=True); ap.add_argument('--t1', type=float, required=True)
ap.add_argument('--rpm', type=float, nargs=3, metavar=('LO', 'HI', 'STEP'), required=True)
ap.add_argument('--out', required=True); ap.add_argument('--prefix', required=True); ap.add_argument('--load', required=True)
ap.add_argument('--loop-sec', type=float, default=2.5)
ap.add_argument('--spread', type=float, default=0.05, help='use cycles within +-spread*rpm (widened up to 2x if too few)')
ap.add_argument('--grain', type=int, nargs=2, default=[2, 4], metavar=('MIN', 'MAX'), help='cycles per run')
ap.add_argument('--xfade', type=float, default=0.25, help='crossfade between runs, in cycles')
ap.add_argument('--seed', type=int, default=1)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
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
rng = np.random.default_rng(a.seed)
g_lo, g_hi = a.grain
lo, hi, step = a.rpm
print('segment rpm %d-%d over %.1f s' % (r_s.min(), r_s.max(), t[-1] - t[0]))

def longest_run(mask):
    edges = np.flatnonzero(np.diff(np.concatenate([[0], mask.astype(int), [0]])))
    runs = list(zip(edges[::2], edges[1::2]))
    return max(runs, key=lambda se: phase[se[1] - 1] - phase[se[0]]) if runs else None

for R in np.arange(lo, hi + 1, step):
    M = int(round(SR * 120.0 / R))             # samples per engine cycle at exactly R
    X = max(16, int(M * a.xfade))
    for spread in (a.spread, a.spread * 1.5, a.spread * 2):
        run = longest_run(np.abs(r_s - R) / R <= spread)
        if run and phase[run[1] - 1] - phase[run[0]] >= 2 * g_hi + 2: break
    else:
        print('  %5d rpm  skipped: fewer than %d cycles within +-%d%%' % (R, 2 * g_hi + 2, spread * 100)); continue
    s, e = run
    n_w = int((phase[e - 1] - phase[s]) * M)
    src_i = np.interp(phase[s] + np.arange(n_w) / M, phase, np.arange(len(phase)))
    w = np.interp(src_i, np.arange(len(seg_x)), seg_x)               # warped: every cycle is M samples
    nc = n_w // M
    c_rms = np.array([np.sqrt(np.mean(w[i * M:(i + 1) * M] ** 2)) + 1e-9 for i in range(nc)])
    target = np.median(c_rms)
    n_cyc = max(4, int(round(a.loop_sec * R / 120)))
    L = n_cyc * M
    fin = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, X)); fout = 1 - fin
    buf = np.zeros(L + (g_hi + 2) * M + X)
    pos, recent, sh_max = 0, [], max(1, M // 12)
    while pos < L + X:
        g = int(rng.integers(g_lo, min(g_hi, nc - 2) + 1))
        cands = [c for c in range(0, nc - g) if all(abs(c - r) >= g for r in recent[-3:])] or list(range(0, nc - g))
        st = int(rng.choice(cands)) * M
        if pos:                                    # line the new run up with the tail already written
            ref = buf[pos:pos + X]
            shifts = [sh for sh in range(-sh_max, sh_max + 1) if 0 <= st + sh and st + sh + g * M + X <= n_w]
            st += max(shifts, key=lambda sh: np.dot(ref, w[st + sh:st + sh + X]))
        seg = w[st:st + g * M + X]
        seg = seg * (target / (np.sqrt(np.mean(seg ** 2)) + 1e-9)) ** 0.8
        if pos: buf[pos:pos + X] = buf[pos:pos + X] * fout + seg[:X] * fin; buf[pos + X:pos + len(seg)] = seg[X:]
        else: buf[:len(seg)] = seg
        recent.append(st // M); pos += g * M
    loop = buf[:L].copy(); loop[:X] = buf[:X] * fin + buf[L:L + X] * fout    # wrap: tail fades into head
    loop *= 0.18 / (np.sqrt(np.mean(loop ** 2)) + 1e-9)
    pk = np.abs(loop).max()
    if pk > 0.98: loop *= 0.98 / pk
    name = '%s/%s_%s_%04d.wav' % (a.out, a.prefix, a.load, R)
    with wave.open(name, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(loop, -1, 1) * 32767).astype('<i2').tobytes())
    print('  %5d rpm  loop %.2fs  from %d source cycles (+-%d%%, source rpm %d-%d)' % (
        R, L / SR, nc, round(spread * 100), r_s[s:e].min(), r_s[s:e].max()))
