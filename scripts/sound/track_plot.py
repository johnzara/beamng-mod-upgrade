"""Spectrogram (0-700 Hz) with the tracked f0 (green) and 2x f0 (blue) drawn on top.

usage: track_plot.py CLIP TRACK.json OUT.ppm ORDER TITLE
Writes a PPM image (convert: sips -s format png OUT.ppm --out OUT.png) and prints the
rpm range at ORDER. If the green line sits on a weaker band below the strongest
harmonic, or jumps, the order/octave is wrong.
"""
import sys, json, subprocess, numpy as np
path, track, out, order_of_track, rpm_per_hz_title = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
d = json.load(open(track)); t = np.array(d['t']); f0 = np.array(d['f0'])
SR = 8000; t0 = t[0] - 0.256
x = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-ss',str(max(t0,0)),'-t',str(t[-1]-t0+0.6),'-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout, dtype=np.float32)
win, hop = 2048, 200; w = np.hanning(win)
fr = np.array([np.abs(np.fft.rfft(x[i:i+win]*w)) for i in range(0, len(x)-win, hop)])
freqs = np.fft.rfftfreq(win, 1/SR); top = np.searchsorted(freqs, 700)
img = 20*np.log10(fr[:, :top].T + 1e-6); img = np.clip((img - np.percentile(img, 40)) / (img.max() - np.percentile(img, 40)), 0, 1)
H, W = img.shape; rgb = np.stack([img*255, img*180, img*60], axis=2).astype(np.uint8)[::-1].copy()
ft = (np.arange(W) * hop + win/2) / SR + max(t0, 0)
for mult, col in ((1.0, (0,255,0)), (2.0, (0,180,255))):    # tracked line and its double
    fi = np.interp(ft, t, f0) * mult
    rows = H - 1 - np.searchsorted(freqs[:top], fi)
    for c in range(W):
        r = rows[c]
        if 1 <= r < H-1: rgb[r-1:r+2, c] = col
rgb = np.repeat(np.repeat(rgb, 2, axis=0), 1, axis=1)
with open(out, 'wb') as fh:
    fh.write(b'P6 %d %d 255\n' % (rgb.shape[1], rgb.shape[0])); fh.write(rgb.tobytes())
r = f0 * 60 / order_of_track
print('%s: rpm %d -> %d (min %d, max %d), %.1f s' % (rpm_per_hz_title, r[:5].mean(), r[-5:].mean(), r.min(), r.max(), t[-1]-t[0]))
