"""Track the engine's dominant firing frequency (f0) over time in a clip.

usage: rpm_track.py CLIP OUT.json START_S DUR_S   (DUR_S 0 = to the end)
Harmonic-sum f0 per 50 ms frame with Viterbi smoothing (no wild jumps). Prints the rpm
range for the I4 (order 2) and V6 (order 3) hypotheses. The tracked line can lock onto
another engine order (a V6 often shows 1.5) or jump an octave on fast blips: always
check with track_plot.py and a known reference rpm (idle, redline, tacho in the video).
"""
import sys, subprocess, json, numpy as np
path, out, start, dur = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
SR = 8000
cmd = ['ffmpeg', '-v', 'error', '-ss', str(start)] + (['-t', str(dur)] if dur > 0 else []) + ['-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
win, hop = 2048, 200                      # 0.51 s window, 50 ms hop
w = np.hanning(win)
frames = [x[i:i+win] * w for i in range(0, len(x) - win, hop)]
spec = np.abs(np.fft.rfft(np.array(frames), n=win*4, axis=1))   # zero-padded: ~0.5 Hz bins
freqs = np.fft.rfftfreq(win*4, 1/SR)
spec = np.log1p(spec / (np.median(spec) + 1e-9))
cands = np.arange(25.0, 420.0, 1.0)
def score(f0):  # harmonic sum, weighted towards lower harmonics
    s = 0
    for k, wk in zip(range(1, 7), (1.0, 0.8, 0.6, 0.5, 0.4, 0.3)):
        idx = np.searchsorted(freqs, f0 * k)
        if idx < len(freqs): s = s + wk * spec[:, idx]
    return s
S_ = np.stack([score(f) for f in cands], axis=1)            # frames x cands
# Viterbi smoothing: penalise jumps in log-frequency
lc = np.log(cands); n, m = S_.shape
jump = 12.0 * np.abs(lc[:, None] - lc[None, :])
dp = S_[0].copy(); back = np.zeros((n, m), dtype=np.int32)
for t in range(1, n):
    tot = dp[None, :] - jump          # m x m  (to, from)
    back[t] = np.argmax(tot, axis=1); dp = tot[np.arange(m), back[t]] + S_[t]
path_idx = np.zeros(n, dtype=np.int32); path_idx[-1] = int(np.argmax(dp))
for t in range(n - 1, 0, -1): path_idx[t-1] = back[t][path_idx[t]]
f0 = cands[path_idx]; conf = S_[np.arange(n), path_idx] / (np.median(S_, axis=1) + 1e-9)
t = start + (np.arange(n) * hop + win / 2) / SR
json.dump({'t': t.round(3).tolist(), 'f0': f0.tolist(), 'conf': conf.round(3).tolist()}, open(out, 'w'))
print('frames', n, 'f0 range %.1f-%.1f Hz' % (np.percentile(f0, 5), np.percentile(f0, 95)))
for lab, order in (('I4 (2nd order)', 2), ('V6 (3rd order)', 3)):
    r = f0 * 60 / order
    print('  if %s: rpm %d-%d' % (lab, np.percentile(r, 5), np.percentile(r, 95)))
