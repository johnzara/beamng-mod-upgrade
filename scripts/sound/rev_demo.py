"""Preview how a set of loops sounds in BeamNG-style playback before installing.

usage: rev_demo.py OUT.wav 'LOOPDIR/PREFIX_LOAD' 'R0:R1:SECS,R0:R1:SECS,...'
e.g. rev_demo.py demo.wav loops/b284dyno_onload '900:900:2,900:6500:5,6500:6500:3'
Loops are named PREFIX_LOAD_RPM.wav (4-digit rpm). Each is pitch-shifted to the
current rpm and the two nearest are equal-power crossfaded, like the game does.
Convert for the user: ffmpeg -i OUT.wav -c:a aac -b:a 192k OUT.m4a
"""
import sys, glob, wave, numpy as np
out, pattern, segs = sys.argv[1], sys.argv[2], sys.argv[3]
SR = 48000
loops = []
for p in sorted(glob.glob(pattern + '_*.wav')):
    with wave.open(p) as w: a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2') / 32768.0
    loops.append((int(p[-8:-4]), a))
Rs = np.array([r for r, _ in loops], dtype=float)
rpm = np.concatenate([np.linspace(float(a), float(b), int(float(s) * SR)) for a, b, s in (x.split(':') for x in segs.split(','))])
rpm = np.maximum(rpm, Rs.min())
y = np.zeros_like(rpm)
for i, (R, a) in enumerate(loops):
    lo = Rs[i-1] if i > 0 else R; hi = Rs[i+1] if i + 1 < len(Rs) else R
    wgt = np.where(rpm <= R, np.clip((rpm - lo) / max(R - lo, 1), 0, 1) if i > 0 else (rpm <= R) * 1.0,
                   np.clip((hi - rpm) / max(hi - R, 1), 0, 1) if i + 1 < len(Rs) else (rpm >= R) * 1.0)
    wgt = np.sin(wgt * np.pi / 2)                               # equal-power crossfade
    if wgt.max() == 0: continue
    pos = np.cumsum(rpm / R) % len(a)
    i0 = pos.astype(int); fr = pos - i0
    y += wgt * (a[i0] * (1 - fr) + a[(i0 + 1) % len(a)] * fr)
y *= 0.9 / (np.abs(y).max() + 1e-9)
fade = int(0.05 * SR); y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype('<i2').tobytes())
print('demo', out, '%.1fs' % (len(y) / SR), 'loops', list(Rs.astype(int)))
