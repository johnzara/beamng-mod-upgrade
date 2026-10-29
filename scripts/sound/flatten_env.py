"""Even out slow loudness drift inside seamless loops (circular, so the wrap stays clean).

usage: flatten_env.py STRENGTH WINDOW_S IN_DIR OUT_DIR     e.g. 0.8 0.25
Needed for long (2 s+) loops cut from a sweep: the window covers several hundred rpm
of boost build-up, which otherwise plays back as a swell every loop.
"""
import sys, os, wave, numpy as np
k, win, src, dst = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(dst, exist_ok=True)
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.wav'): continue
    w = wave.open(os.path.join(src, fn)); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i2') / 32768.0
    n = len(x); m = int(win * sr)
    h = np.zeros(n); h[:m] = np.hanning(m); h /= h.sum(); h = np.roll(h, -m // 2)
    p = np.real(np.fft.ifft(np.fft.fft(x**2) * np.fft.fft(h)))       # circular smoothed power
    env = np.sqrt(np.maximum(p, 1e-12))
    y = x * (env.mean() / env) ** k
    y *= 0.18 / np.sqrt((y**2).mean())
    pk = np.abs(y).max()
    if pk > 0.98: y *= 0.98 / pk
    with wave.open(os.path.join(dst, fn), 'wb') as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
        o.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
