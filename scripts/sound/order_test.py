"""Which engine order the tracked f0 really is: prominence of peaks at f0 x 1/3, 1/2, 2/3, 1.5, 2.

usage: order_test.py CLIP TRACK.json
Strong peaks at f0/2 mean the tracker sits on the 2nd harmonic of the real fundamental.
"""
import sys, json, subprocess, numpy as np
path, track = sys.argv[1], sys.argv[2]
d = json.load(open(track)); t = np.array(d['t']); f0 = np.array(d['f0'])
SR = 8000
x = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout, dtype=np.float32)
win = 4096; w = np.hanning(win); freqs = np.fft.rfftfreq(win*4, 1/SR)
res = {r: [] for r in (1/3, 1/2, 2/3, 1.5, 2.0)}
for ti, fi in zip(t[::4], f0[::4]):
    i = int(ti * SR - win / 2)
    if i < 0 or i + win > len(x): continue
    sp = np.abs(np.fft.rfft(x[i:i+win] * w, n=win*4))
    def band(f):  # peak within +-2% vs local floor
        lo, hi = np.searchsorted(freqs, [f*0.98, f*1.02]); flo, fhi = np.searchsorted(freqs, [f*0.85, f*1.15]); hi = max(hi, lo+1); fhi = max(fhi, flo+2)
        return 20*np.log10((sp[lo:hi].max()+1e-9)/(np.median(sp[flo:fhi])+1e-9))
    for r in res: res[r].append(band(fi * r))
print('  prominence dB at f*1/3=%.1f  f*1/2=%.1f  f*2/3=%.1f  f*1.5=%.1f  f*2=%.1f' % tuple(np.median(res[r]) for r in (1/3, 1/2, 2/3, 1.5, 2.0)))
