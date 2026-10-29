"""Loop quality check: level, volume swing (100 ms frames), spectral centroid range,
wrap-point jump (x99th-percentile sample step; < 1 is clean) and end-vs-start level.

usage: loop_qc.py LOOP.wav [...]
Look for: env swing > ~4 dB on a long loop (audible swell -> flatten_env.py), end/start
> ~1.5 dB (pumping at the wrap), centroid far from the neighbouring loops (timbre jump
when BeamNG crossfades between them).
"""
import sys, wave, numpy as np
for f in sys.argv[1:]:
    w = wave.open(f); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), '<i2') / 32768.0
    n = int(0.1 * sr); fr = x[:len(x)//n*n].reshape(-1, n)
    env = 20*np.log10(np.sqrt((fr**2).mean(1)) + 1e-9)
    win = np.hanning(n); sp = np.abs(np.fft.rfft(fr*win, axis=1)); fq = np.fft.rfftfreq(n, 1/sr)
    cen = (sp*fq).sum(1)/(sp.sum(1)+1e-12)
    d = np.abs(np.diff(x)); jump = abs(x[0]-x[-1]) / (np.percentile(d, 99)+1e-9)
    # level difference between the last and first 300 ms (what the ear compares at the wrap)
    k = int(0.3*sr); edge = 20*np.log10(np.sqrt((x[-k:]**2).mean())/np.sqrt((x[:k]**2).mean()))
    print('%-34s %4.2fs  rms %6.1f  env swing %4.1f dB  centroid %4.0f-%4.0f Hz  wrap %.2f  end/start %+.1f dB' % (
        f.split('/')[-1], len(x)/sr, 20*np.log10(np.sqrt((x**2).mean())), env.max()-env.min(), cen.min(), cen.max(), jump, edge))
