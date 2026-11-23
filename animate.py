# seal-lofi v1: code-animated loop over a gpt-image-2 still.
# Rain on glass, blinking city windows, mug steam, lamp breathing.
# Every motion completes a whole number of cycles in T frames, so the loop is seamless.
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 24
T = 240                      # 10 s loop
SRC = 'room.png'
CROP_Y = 40                  # 1536x1024 -> 1536x864 (16:9)
W, H = 1536, 864
rng = np.random.default_rng(7)

base = Image.open(SRC).convert('RGB').crop((0, CROP_Y, W, CROP_Y + H))
B = np.asarray(base).astype(np.float32) / 255.0

# ---------- regions (from vision review, original coords shifted by CROP_Y) ----------
WIN = (60, 0, 1430, 530 - CROP_Y)          # glass
MUG = (630, 505 - CROP_Y)                  # mug mouth centre
LAMP = (1245, 385 - CROP_Y)                # bulb centre

# ---------- city window flicker ----------
x0, y0, x1, y1 = WIN
lum = B[..., 0] * 0.3 + B[..., 1] * 0.59 + B[..., 2] * 0.11
warm = (B[..., 0] > B[..., 2])
lit = np.zeros((H, W), np.float32)
R_, G_, B_ = B[..., 0], B[..., 1], B[..., 2]
win_lit = (lum > 0.5) & (R_ > 0.6) & (G_ > 0.42) & (B_ < 0.55) & (R_ - B_ > 0.25)
ROOF = 180                                   # nothing above this flickers (sky)
lit[ROOF:y1, x0:x1] = win_lit[ROOF:y1, x0:x1].astype(np.float32)
for (a, b, c, e) in [(230, 400 - CROP_Y, 580, 560 - CROP_Y), (80, 270 - CROP_Y, 300, 540 - CROP_Y)]:
    lit[b:e, a:c] = 0                         # cat, monstera
lit = np.asarray(Image.fromarray((lit * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
CELL = 14
gh, gw = H // CELL + 1, W // CELL + 1
kind = rng.random((gh, gw))
phase = rng.random((gh, gw))
freq = rng.integers(1, 4, (gh, gw))

def flicker_field(t):
    s = np.ones((gh, gw), np.float32)
    off = kind < 0.06
    p = (t / T * freq + phase) % 1.0
    s[off] = np.where(p[off] < 0.35, 0.6, 1.0)
    sh = (kind >= 0.06) & (kind < 0.20)
    s[sh] = 1.0 + 0.22 * np.sin(2 * math.pi * p[sh])
    return np.kron(s, np.ones((CELL, CELL), np.float32))[:H, :W]

# ---------- rain ----------
Hr = y1 - y0
drops_fast = [dict(x=rng.uniform(x0, x1), y=rng.uniform(0, Hr), k=int(rng.integers(7, 12)),
                   L=rng.uniform(18, 40), a=rng.uniform(0.10, 0.22), s=rng.uniform(0.05, 0.2)) for _ in range(260)]
drips = [dict(x=rng.uniform(x0, x1), y=rng.uniform(0, Hr), k=int(rng.integers(1, 3)),
              L=rng.uniform(10, 26), a=rng.uniform(0.25, 0.45), w=rng.uniform(1.5, 2.5),
              wob=rng.uniform(0, 6.28)) for _ in range(70)]

def rain_layer(t):
    lay = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(lay)
    for r in drops_fast:
        y = (r['y'] + Hr * r['k'] * t / T) % Hr + y0
        d.line([(r['x'] + r['s'] * r['L'], y - r['L']), (r['x'], y)], fill=int(255 * r['a']), width=1)
    for r in drips:
        y = (r['y'] + Hr * r['k'] * t / T) % Hr + y0
        x = r['x'] + 1.5 * math.sin(2 * math.pi * 3 * t / T + r['wob'])
        d.line([(x, y - r['L']), (x, y)], fill=int(255 * r['a'] * 0.6), width=int(r['w']))
        d.ellipse([x - r['w'], y - r['w'], x + r['w'], y + r['w']], fill=int(255 * r['a']))
    return np.asarray(lay.filter(ImageFilter.GaussianBlur(1.1))).astype(np.float32) / 255 * RMASK

# glass-only mask: window rect minus cat, monstera, mullions; soft edges
_m = Image.new('L', (W, H), 0)
_d = ImageDraw.Draw(_m)
_d.rectangle([x0, y0, x1, y1], fill=255)
for box in [(220, 390 - CROP_Y, 590, 600), (70, 260 - CROP_Y, 310, 600), (520, 0, 545, H), (1050, 0, 1075, H)]:
    _d.rectangle(box, fill=0)
RMASK = np.asarray(_m.filter(ImageFilter.GaussianBlur(8))).astype(np.float32) / 255

RAIN_COL = np.array([0.82, 0.86, 1.0], np.float32)

# ---------- steam ----------
SW, SH = 160, 190
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
puffs = [dict(p0=rng.random(), dx=rng.uniform(-6, 6), wob=rng.uniform(0, 6.28)) for _ in range(9)]

def steam_patch(t):
    acc = np.zeros((SH, SW), np.float32)
    for f in puffs:
        p = (f['p0'] + t / T) % 1.0
        cy = SH - 10 - p * (SH - 30)
        cx = SW / 2 + f['dx'] + 14 * p * math.sin(2 * math.pi * (2 * t / T) + f['wob'])
        sig = 6 + 16 * p
        a = math.sin(math.pi * p) ** 1.5 * 0.16
        acc += a * np.exp(-(((xx - cx) ** 2) / (2 * sig ** 2) + ((yy - cy) ** 2) / (2 * (sig * 1.6) ** 2)))
    return np.clip(acc, 0, 0.35)

# ---------- lamp breathing ----------
ly, lx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.exp(-(((lx - LAMP[0]) ** 2) + ((ly - LAMP[1]) ** 2) / 1.3) / (2 * 140 ** 2)).astype(np.float32)
GLOW_COL = np.array([1.0, 0.72, 0.38], np.float32)

def frame(t):
    img = B.copy()
    fl = flicker_field(t)
    img *= (1 + (fl[..., None] - 1) * lit[..., None])
    r = rain_layer(t)[..., None]
    img = img * (1 - r * 0.35) + RAIN_COL * r * 0.35
    st = steam_patch(t)[..., None]
    sx, sy = MUG[0] - SW // 2, MUG[1] - SH
    reg = img[sy:sy + SH, sx:sx + SW]
    img[sy:sy + SH, sx:sx + SW] = reg * (1 - st) + np.array([1.0, 0.97, 0.92]) * st
    k = 0.035 * (1 + math.sin(2 * math.pi * 2 * t / T)) + 0.01 * math.sin(2 * math.pi * 11 * t / T)
    img += glow[..., None] * GLOW_COL * k
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'loop'
    if mode == 'stills':
        for t in (0, 60, 120, 180):
            Image.fromarray(frame(t)).save(f'still_{t:03d}.png')
        Image.fromarray(np.concatenate([frame(0)[:, :768], frame(120)[:, 768:]], 1)).save('split.png')
    else:
        p = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
                              '-crf', '14', '-pix_fmt', 'yuv420p', '-g', str(T), 'loop_master.mp4'], stdin=subprocess.PIPE)
        for t in range(T):
            p.stdin.write(frame(t).tobytes())
        p.stdin.close(); p.wait()
