"""Measure the tonal difference between two parts of a recording and apply it to loops.

Typical use: a clip has the stock exhaust first and an aftermarket one later (same car,
same mic). The stock part is too quiet to cut loops from, so cut loops from the loud
part and give them the stock part's tone.

measure: match_eq.py measure CLIP OUT.json --target A B [A B ...] --ref A B [A B ...]
    pairs of time ranges (seconds) at matching rpm/load: target = the sound you want,
    ref = the sound the loops are cut from. Pairs are averaged. Prints third-octave
    differences and the overall level difference.
apply:   match_eq.py apply EQ.json IN_DIR OUT_DIR [--max-hz 1000] [--keep-level] [--strength 1]
    applies the shape (cuts only, below --max-hz; above it 0 dB) with a circular FFT,
    so seamless loops stay seamless. By default the measured overall level change is
    applied too (a stock silencer really is quieter); --keep-level skips it.
"""
import sys, os, glob, json, wave, argparse, subprocess, numpy as np
ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
m = sub.add_parser('measure'); m.add_argument('clip'); m.add_argument('out')
m.add_argument('--target', type=float, nargs='+', required=True); m.add_argument('--ref', type=float, nargs='+', required=True)
p = sub.add_parser('apply'); p.add_argument('eq'); p.add_argument('src'); p.add_argument('dst')
p.add_argument('--max-hz', type=float, default=1000); p.add_argument('--keep-level', action='store_true'); p.add_argument('--strength', type=float, default=1.0)
a = ap.parse_args()
bands = 50 * 2 ** (np.arange(0, 22) / 3)          # third octaves 50 Hz .. ~6.4 kHz
if a.cmd == 'measure':
    SR = 44100
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', a.clip, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, dtype=np.float32)
    def ltas(t0, t1):
        seg = x[int(t0 * SR):int(t1 * SR)]; n = 8192; w = np.hanning(n)
        sp = np.mean([np.abs(np.fft.rfft(seg[i:i + n] * w)) ** 2 for i in range(0, len(seg) - n, n // 2)], axis=0)
        return np.fft.rfftfreq(n, 1 / SR), sp
    def band_db(f, sp): return np.array([10 * np.log10(sp[(f >= b / 2 ** (1 / 6)) & (f < b * 2 ** (1 / 6))].mean() + 1e-20) for b in bands])
    T = list(zip(a.target[::2], a.target[1::2])); Rf = list(zip(a.ref[::2], a.ref[1::2]))
    assert len(T) == len(Rf) and T, 'give the same number of target and ref ranges'
    diffs, lvl = [], []
    for (ta, tb), (ra, rb) in zip(T, Rf):
        f, s1 = ltas(ta, tb); _, s2 = ltas(ra, rb)
        diffs.append(band_db(f, s1) - band_db(f, s2))
        band = (f > 40) & (f < 6000); lvl.append(10 * np.log10(s1[band].sum() / s2[band].sum()))
        print('pair %.1f-%.1f vs %.1f-%.1f: overall %+.1f dB' % (ta, tb, ra, rb, lvl[-1]))
    d = np.mean(diffs, axis=0) - np.mean(lvl)
    for b, v in zip(bands, d): print('%6.0f Hz  %+5.1f dB (shape)' % (b, v))
    json.dump({'bands': bands.tolist(), 'shape_db': d.tolist(), 'level_db': float(np.mean(lvl))}, open(a.out, 'w'))
    print('overall level %+.1f dB -> %s' % (np.mean(lvl), a.out))
else:
    d = json.load(open(a.eq)); b = np.array(d['bands']); lv = d['level_db']
    absd = np.array(d['shape_db']) + (0 if a.keep_level else lv)
    sm = np.array([absd[max(0, i - 1):i + 2].mean() for i in range(len(absd))])      # smooth across neighbours
    g = np.where(b < a.max_hz, np.minimum(sm, 0), 0.0) * a.strength
    g[0] = max(g[0], -3.0)
    edge = a.max_hz * 1.1
    fpts = np.concatenate([[0], b[b < edge], [edge, 24000]]); gpts = np.concatenate([[g[0]], g[b < edge], [0, 0]])
    os.makedirs(a.dst, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(a.src, '*.wav'))):
        with wave.open(f) as w: x = np.frombuffer(w.readframes(w.getnframes()), '<i2') / 32768.0; sr = w.getframerate()
        X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / sr)
        gain = np.interp(np.log10(np.maximum(fr, 1)), np.log10(np.maximum(fpts, 1)), gpts)
        y = np.fft.irfft(X * 10 ** (gain / 20), n=len(x))
        with wave.open(os.path.join(a.dst, os.path.basename(f)), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
        print('%-32s %+5.1f dB' % (os.path.basename(f), 20 * np.log10(np.sqrt(np.mean(y ** 2)) / np.sqrt(np.mean(x ** 2)))))
