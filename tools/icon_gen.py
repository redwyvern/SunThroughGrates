"""SunThroughGrates icon generator.

Renders at 4x (1024 px) and downsamples to 256 px with LANCZOS.
Scene: looking up from under a riveted iron cage ceiling; the sun blazes
behind it, and god-rays stream through each opening onto crops in tilled
soil, leaving a grid of light pools on the ground.

Usage: python3 tools/icon_gen.py
  -> icon.png (256, repo root); tools/preview64.png and tools/big.png for review
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(OUT_DIR)
rng = random.Random(11)


def lerp(a, b, t):
    return a + (b - a) * t


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def arr(img):
    return np.asarray(img).astype(np.float32)


def blur(a, r):
    """Gaussian-blur a float array (0..1 range, 2D)."""
    return arr(to_img(a * 255).filter(ImageFilter.GaussianBlur(r))) / 255.0


yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)

# --------------------------------------------------------------------------
# Ceiling-plane projection (viewed from below, receding upward)
# --------------------------------------------------------------------------
CX = S * 0.5
HORIZON = -330.0
Y_NEAR = 440.0
FOCAL = 800.0


def proj(X, Z):
    return (CX + X * FOCAL / Z, HORIZON + (Y_NEAR - HORIZON) / Z)


SUN = (CX, 172.0)

# --------------------------------------------------------------------------
# 1. Sky behind the grate
# --------------------------------------------------------------------------
d = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.2) ** 2)
t = np.clip(d / 640.0, 0, 1)
stops = [(0.00, (255, 255, 250)), (0.13, (255, 248, 205)), (0.30, (255, 186, 74)),
         (0.60, (200, 96, 36)), (1.00, (84, 44, 34))]
sky = np.zeros((S, S, 3), np.float32)
for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
    m = (t >= t0) & (t <= t1)
    f = ((t - t0) / (t1 - t0))[m]
    for i in range(3):
        sky[..., i][m] = lerp(c0[i], c1[i], f)

# subtle sun-rune halo ring (Norse touch) around the sun
ring = np.exp(-((d - 150) / 10) ** 2) * 0.22
sky += ring[..., None] * np.array([255, 230, 170])

# --------------------------------------------------------------------------
# 2. Dark interior below the grate
# --------------------------------------------------------------------------
ti = np.clip((yy - Y_NEAR) / (S - Y_NEAR), 0, 1)
interior = np.stack([lerp(22, 10, ti), lerp(19, 8, ti), lerp(19, 8, ti)], axis=-1)
ceil = (yy < Y_NEAR)[..., None]
base = np.where(ceil, sky, interior).astype(np.float32)

# --------------------------------------------------------------------------
# 3. Grate geometry
# --------------------------------------------------------------------------
xs = np.linspace(-1.15, 1.15, 6)          # bars running away from viewer
zs = [1.0, 1.32, 1.8, 2.6, 4.0, 7.0, 16.0]  # bars running across
BW = 0.075                                 # bar half-width (world)
BWZ = 0.045                                # cross-bar half-width (depth)
DROP = 24                                  # bar thickness in px at z = 1

cells = []
for j in range(1):  # only the nearest row casts visible shafts below
    for i in range(len(xs) - 1):
        x0, x1 = xs[i] + BW, xs[i + 1] - BW
        z0, z1 = zs[j] * (1 + BWZ), zs[j + 1] * (1 - BWZ)
        cells.append([proj(x0, z0), proj(x1, z0), proj(x1, z1), proj(x0, z1)])


def hull(points):
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# --------------------------------------------------------------------------
# 4. God rays: each opening casts a crisp shaft down to the soil
# --------------------------------------------------------------------------
SRC = (CX, -2400.0)   # distant source -> nearly parallel, slightly fanned
RAY_END = 1060.0
ray_img = Image.new("L", (S, S), 0)
rd = ImageDraw.Draw(ray_img)
for poly in cells:
    cx_ = sum(p[0] for p in poly) / 4
    cy_ = sum(p[1] for p in poly) / 4
    if cy_ < -40:
        continue
    dsun = math.hypot((cx_ - SUN[0]) * 0.75, cy_ - SUN[1])
    strength = max(0.0, 1.0 - dsun / 820.0) ** 0.8
    if strength < 0.05:
        continue
    k = (RAY_END - SRC[1]) / (cy_ - SRC[1])
    far = [(SRC[0] + (p[0] - SRC[0]) * k, SRC[1] + (p[1] - SRC[1]) * k) for p in poly]
    fc = (sum(p[0] for p in far) / 4, sum(p[1] for p in far) / 4)
    far = [(fc[0] + (p[0] - fc[0]) * 0.80, fc[1] + (p[1] - fc[1]) * 0.80) for p in far]
    rd.polygon(hull(poly + far), fill=int(255 * strength))
ray_full = arr(ray_img) / 255.0
fade = np.clip(1.0 - (yy - Y_NEAR) / 900.0, 0.45, 1.0)
ray_full *= fade
ray_raw = ray_full * (yy >= Y_NEAR)
# haze in front of the bars so shafts visibly start at the openings
haze = blur(ray_full * np.clip((yy - 230) / 200, 0, 1) * (yy < Y_NEAR + 60), 14)
rays = blur(ray_raw, 5) * 0.50 + blur(ray_raw, 30) * 0.08
RAY_COL = np.array([255, 210, 128], np.float32)

# --------------------------------------------------------------------------
# 5. Soil: raised tilled rows, lit in a grid of light pools
# --------------------------------------------------------------------------
GROUND_Y = 790
soil = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(soil)
sd.rectangle([0, GROUND_Y, S, S], fill=(44, 29, 20, 255))
sd.ellipse([-260, GROUND_Y - 40, S + 260, GROUND_Y + 120], fill=(44, 29, 20, 255))
for r, yv in enumerate([GROUND_Y + 10, GROUND_Y + 70, GROUND_Y + 145, GROUND_Y + 235]):
    h = 30 + r * 14
    sd.ellipse([-200, yv - h * 0.2, S + 200, yv + h * 1.6], fill=(30, 19, 13, 255))   # furrow
    sd.ellipse([-200, yv - h, S + 200, yv + h * 0.9], fill=(62, 41, 27, 255))          # ridge
    sd.ellipse([-120, yv - h + 4, S + 120, yv - h + 4 + h * 0.6], fill=(80, 54, 35, 255))  # ridge top
soil_np = arr(soil)
sa = soil_np[..., 3:4] / 255.0
base = base * (1 - sa) + soil_np[..., :3] * sa
pool = np.clip(blur(ray_raw, 4) * 1.1, 0, 1) * sa[..., 0]
base += pool[..., None] * np.array([165, 115, 55], np.float32)

# --------------------------------------------------------------------------
# 6. Crops
# --------------------------------------------------------------------------
crops = Image.new("RGBA", (S, S), (0, 0, 0, 0))
cd = ImageDraw.Draw(crops)


def leaf(x, y, ang, length, width, col, hi=None, bend=0.3):
    l, r, mid = [], [], []
    n = 16
    sgn = 1 if ang >= 0 else -1
    for k in range(n + 1):
        f = k / n
        a = ang + sgn * bend * f * f
        px = x + math.sin(a) * length * f
        py = y - math.cos(a) * length * f
        w = width * math.sin(math.pi * min(1.0, f * 1.05 + 0.02)) * (1 - 0.35 * f)
        nx, ny = math.cos(a), math.sin(a)
        l.append((px - nx * w, py - ny * w))
        r.append((px + nx * w, py + ny * w))
        mid.append((px, py))
    cd.polygon(l + r[::-1], fill=col)
    if hi:
        cd.polygon(l + mid[::-1], fill=hi)
    return mid


def turnip(x, y, s):
    for a, L in [(-1.0, 170), (-0.5, 215), (0.0, 240), (0.5, 210), (0.95, 170)]:
        leaf(x, y - 25 * s, a, L * s, 40 * s, (46, 112, 40, 255), (92, 164, 58, 255))
    r = 64 * s
    cd.ellipse([x - r, y - r * 0.85, x + r, y + r * 0.85], fill=(196, 180, 170, 255))
    cd.chord([x - r, y - r * 0.85, x + r, y + r * 0.85], 180, 360, fill=(140, 58, 132, 255))
    cd.ellipse([x - r * 0.6, y - r * 0.62, x - r * 0.1, y - r * 0.2], fill=(196, 116, 186, 255))
    cd.polygon([(x - 8 * s, y + r * 0.8), (x + 8 * s, y + r * 0.8), (x, y + r * 1.25)], fill=(200, 186, 170, 255))


def carrot(x, y, s):
    for a in [-0.75, -0.38, 0.0, 0.38, 0.75]:
        L = 230 * s
        mid = leaf(x, y - 10 * s, a, L, 9 * s, (52, 120, 40, 255), bend=0.15)
        for k in range(4, 16, 2):
            px, py = mid[k]
            f = k / 16
            for side in (-1, 1):
                leaf(px, py, a + side * 0.75, 70 * s * (1.15 - f * 0.6), 17 * s,
                     (64, 140, 48, 255), (118, 184, 68, 255), bend=0.1)
    cd.ellipse([x - 40 * s, y - 26 * s, x + 40 * s, y + 18 * s], fill=(240, 128, 34, 255))
    cd.ellipse([x - 26 * s, y - 20 * s, x + 4 * s, y - 2 * s], fill=(255, 176, 84, 255))


def barley(x, y, s):
    stalks = [(-30, 190, -0.34), (-14, 225, -0.15), (0, 245, 0.02), (16, 222, 0.18), (32, 185, 0.36)]
    for dx, L, a in stalks:
        bx = x + dx * s
        leaf(bx, y - 30 * s, a - 0.75, 150 * s, 15 * s, (104, 140, 46, 255), (148, 178, 70, 255))
        leaf(bx, y - 60 * s, a + 0.75, 140 * s, 15 * s, (104, 140, 46, 255), (148, 178, 70, 255))
    for dx, L, a in stalks:
        bx = x + dx * s
        tx = bx + math.sin(a) * L * s
        ty = y - math.cos(a) * L * s
        cd.line([(bx, y), (tx, ty)], fill=(184, 160, 66, 255), width=int(9 * s))
        hl = 120 * s
        for m in range(9):
            f = m / 8
            hx = tx + math.sin(a) * hl * f
            hy = ty - math.cos(a) * hl * f
            # awns, pointing up and out
            for side in (-1, 1):
                aa = a + side * 0.35
                cd.line([(hx, hy), (hx + math.sin(aa) * 80 * s, hy - math.cos(aa) * 80 * s)],
                        fill=(246, 214, 120, 255), width=max(2, int(3 * s)))
        for m in range(9):
            f = m / 8
            hx = tx + math.sin(a) * hl * f
            hy = ty - math.cos(a) * hl * f
            rr = 17 * s * (1 - f * 0.45)
            for side in (-1, 1):
                ox = math.cos(a) * rr * 0.8 * side
                oy = math.sin(a) * rr * 0.8 * side
                cd.ellipse([hx + ox - rr, hy + oy - rr * 1.25, hx + ox + rr, hy + oy + rr * 1.25],
                           fill=(250, 204, 82, 255) if side < 0 else (206, 150, 44, 255))


carrot(800, 870, 0.95)
turnip(225, 880, 1.0)
barley(515, 880, 1.0)
turnip(95, 985, 0.7)
carrot(950, 985, 0.7)

# contact shadows
sh = Image.new("L", (S, S), 0)
shd = ImageDraw.Draw(sh)
for x, y, w in [(225, 935, 120), (515, 875, 120), (800, 885, 100), (95, 1020, 80), (950, 1000, 70)]:
    shd.ellipse([x - w, y - 24, x + w, y + 24], fill=190)
sh = arr(sh.filter(ImageFilter.GaussianBlur(16)))[..., None] / 255.0
base *= 1 - sh * 0.65

c_np = arr(crops)
ca = c_np[..., 3:4] / 255.0
lit = np.clip(blur(ray_raw, 18) * 1.6, 0, 1)[..., None]
crop_rgb = c_np[..., :3] * (0.58 + 0.42 * lit) + lit * np.array([24, 18, 0], np.float32)
# golden rim on the sun-facing (top) edges
a2 = ca[..., 0]
rim = np.clip(a2 - np.roll(a2, 7, axis=0), 0, 1)[..., None]
crop_rgb += rim * np.array([255, 214, 130]) * 0.6
base = base * (1 - ca) + crop_rgb * ca

# volumetric rays over everything
base += rays[..., None] * RAY_COL

# dust motes drifting in the light
md = Image.new("L", (S, S), 0)
mdd = ImageDraw.Draw(md)
for _ in range(70):
    x, y = rng.uniform(40, S - 40), rng.uniform(Y_NEAR + 30, 820)
    if ray_raw[int(y), int(x)] > 0.25:
        r = rng.uniform(2.0, 4.0)
        mdd.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(140, 255)))
motes = blur(arr(md) / 255.0, 1.5)
base += motes[..., None] * np.array([255, 236, 190]) * 0.6

# --------------------------------------------------------------------------
# 7. The iron grate (on top): dark weathered iron, warm rim light, rivets
# --------------------------------------------------------------------------
grate = Image.new("RGBA", (S, S), (0, 0, 0, 0))
g = ImageDraw.Draw(grate)
SIDE = (16, 14, 15, 255)
FACE = (46, 42, 44, 255)
FACE2 = (60, 54, 54, 255)
HI = (214, 150, 80, 255)


def dropped(poly, z):
    return [(p[0], p[1] + DROP / z) for p in poly]


XL, XR = -2.2, 2.2
for z in reversed(zs):
    q = [proj(XL, z * (1 - BWZ)), proj(XR, z * (1 - BWZ)), proj(XR, z * (1 + BWZ)), proj(XL, z * (1 + BWZ))]
    g.polygon(dropped(q, z), fill=SIDE)
    g.polygon(q, fill=FACE)
    # sun-side (far) edge glows
    g.line([q[2], q[3]], fill=HI, width=max(2, int(9 / z)))
    g.line([q[0], q[1]], fill=FACE2, width=max(1, int(4 / z)))
for x in xs:
    q = [proj(x - BW, zs[0] * (1 - BWZ)), proj(x + BW, zs[0] * (1 - BWZ)),
         proj(x + BW, zs[-1]), proj(x - BW, zs[-1])]
    g.polygon(dropped(q, 1.0)[:2] + q[2:], fill=SIDE)
    g.polygon(q, fill=FACE)
    edge = [q[1], q[2]] if x <= 0 else [q[0], q[3]]
    g.line(edge, fill=HI, width=5)

for z in zs:
    for x in xs:
        px, py = proj(x, z)
        r = 30 / z ** 0.9
        if r < 3:
            continue
        g.ellipse([px - r, py - r + DROP / z * 0.3, px + r, py + r + DROP / z * 0.3], fill=(14, 12, 12, 255))
        g.ellipse([px - r, py - r, px + r, py + r], fill=(70, 62, 58, 255))
        g.ellipse([px - r * 0.7, py - r * 0.75, px + r * 0.2, py + r * 0.1], fill=(120, 100, 84, 255))
        g.ellipse([px - r * 0.5, py - r * 0.6, px - r * 0.1, py - r * 0.2], fill=(255, 214, 150, 255))

gn = arr(grate)
ga = gn[..., 3:4] / 255.0
# weathering: faint mottled rust on iron faces
noise = np.array([[rng.random() for _ in range(64)] for _ in range(64)], np.float32)
noise = blur(noise.repeat(16, 0).repeat(16, 1), 10)
rust = (np.clip(noise - 0.55, 0, 1) * 2.0)[..., None] * np.array([26, 10, 0])
grgb = gn[..., :3] + rust * (gn[..., :3].mean(axis=2, keepdims=True) < 90)
base = base * (1 - ga) + grgb * ga

# sun bloom bleeding over the bars
base += haze[..., None] * RAY_COL * 0.20
lum = base.mean(axis=2)
bright = np.clip((lum - 190) / 65, 0, 1) * (yy < Y_NEAR)
bloom = np.stack([blur(bright * np.clip(base[..., i], 0, 255) / 255.0, 30) for i in range(3)], -1) * 255
base += bloom * 0.6

# --------------------------------------------------------------------------
# 8. Warm vignette, rounded frame
# --------------------------------------------------------------------------
vd = np.sqrt(((xx - S / 2) / (S / 2)) ** 2 + ((yy - S * 0.45) / (S / 2)) ** 2)
vig = np.clip(1.0 - (vd - 0.8) * 0.8, 0.5, 1.0)[..., None]
base *= vig
img = to_img(base).convert("RGBA")

R = 130
frame = Image.new("RGBA", (S, S), (0, 0, 0, 0))
fd = ImageDraw.Draw(frame)
fd.rounded_rectangle([8, 8, S - 9, S - 9], R - 8, outline=(22, 18, 16, 255), width=26)
fd.rounded_rectangle([20, 20, S - 21, S - 21], R - 20, outline=(150, 108, 62, 255), width=6)
img = Image.alpha_composite(img, frame)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], R, fill=255)
final = Image.new("RGBA", (S, S), (0, 0, 0, 0))
final.paste(img, (0, 0), mask)

icon = final.resize((256, 256), Image.LANCZOS)
icon.save(os.path.join(REPO_ROOT, "icon.png"), optimize=True)
icon.resize((64, 64), Image.LANCZOS).save(os.path.join(OUT_DIR, "preview64.png"))
final.save(os.path.join(OUT_DIR, "big.png"))
print("ok")
