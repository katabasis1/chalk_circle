"""Превью мелового круга с трещинами (пункт 2.5) без Godot: numpy-порт assets/shaders/chalk_ring.gdshader.

Держи в синхроне с шейдером: правишь формулы там — правь и здесь.
Запуск из корня проекта:
    python3 tools/preview_chalk_ring.py [папка]     # по умолчанию — системная временная папка
Пишет chalk_ring_sheet.png (целый / 3 трещины / 5 трещин на последней жизни + свежая рана / лечение)
и chalk_ring_zoom.png (одна трещина крупно).
"""
import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'art', 'noise.png')).convert('L'), dtype=np.float32) / 255.0
H, W = NO.shape
def tex(u, v):
    x = (u * W - 0.5) % W; y = (v * H - 0.5) % H
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    x1 = (x0 + 1) % W; y1 = (y0 + 1) % H
    return (NO[y0, x0] * (1 - fx) + NO[y0, x1] * fx) * (1 - fy) + (NO[y1, x0] * (1 - fx) + NO[y1, x1] * fx) * fy
def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def h11(x): return np.modf(np.sin(x * 127.1) * 43758.5453)[0] % 1.0
def render(cracks, danger=0.0, radius=0.769, width=0.03, pulse=0.0, TIME=0.0, N=640):
    ys, xs = np.mgrid[0:N, 0:N]
    U = (xs + 0.5) / N; V = (ys + 0.5) / N
    px = U * 2 - 1; py = V * 2 - 1
    r = np.hypot(px, py); a = np.arctan2(py, px)
    n1 = tex(a / (2*np.pi) * 5.0, r * 1.5)
    n2 = tex(px * 3.3 + 0.37, py * 3.3 + 0.11)
    wob = (n1 - 0.5) * 0.024
    d = np.abs(r - radius + wob)
    line = ss(width, width * 0.35, d)
    grain = ss(0.3, 0.72, n2 + (1 - line) * 0.25)
    ca = line * (0.45 + 0.55 * grain)
    d2 = np.abs(r - radius * 0.885 + wob * 0.5)
    inner = ss(0.007, 0.002, d2) * 0.4 * grain
    halo_k = np.ones_like(r); cut = np.zeros_like(r); bits = np.zeros_like(r); ember = np.zeros_like(r); gold = np.zeros_like(r)
    t = r - radius + wob
    for i, (ang, amt, hot, heal) in enumerate(cracks):
        da = np.mod(a - ang + np.pi, 2*np.pi) - np.pi
        m = (np.abs(da) <= 0.4) & (np.abs(t) < 0.12)
        sd = h11(ang + i * 0.731)
        s = da * radius
        side = np.where(s < 0, -1.0, 1.0)
        slant = (h11(sd + 5.0) - 0.5) * 1.2
        sp = s - t * slant
        jag = tex(sd * 7.0 + side * 0.29, t * 14.0 + sd)
        zig = np.abs(np.modf(t * 38.0 + sd * 3.0 + side * 0.5 + 100)[0] - 0.5) * 2.0
        gw = amt * (0.019 + 0.03 * jag + 0.01 * zig)
        band = ss(0.05, 0.03, np.abs(t))
        gap = (1 - ss(gw * 0.7, gw + 0.0025, np.abs(sp))) * band
        L = amt * (0.11 + 0.08 * sd)
        along = np.abs(sp) - gw
        k = np.clip(along / max(L, 1e-6), 0, 1)
        w1 = tex(sd * 3.0 + side * 0.41, along * 6.0) - 0.5
        fr = w1 * width * 2.6 * (0.4 + k)
        inside = (along > 0) & (along < L)
        fis = ss(0.005, 0.0014, np.abs(t - fr)) * (1 - k * k)
        fr2 = fr + side * (h11(sd + 3.0) - 0.5) * 2.0 * width * 1.8 * ss(0.2, 1.0, k)
        fis = np.maximum(fis, ss(0.0035, 0.001, np.abs(t - fr2)) * ss(0.15, 0.3, k) * (1 - k))
        fis = np.where(inside, fis, 0.0)
        bite_n = tex(sp * 7.0 + sd * 5.0, t * 7.0 + sd)
        bite = ss(0.55, 0.6, bite_n) * ss(L * 0.8 + gw, gw, np.abs(sp)) * ss(0.002, 0.008, np.abs(t)) * amt
        c_ = np.maximum(gap, np.maximum(fis, bite))
        b_ = np.zeros_like(r)
        for j in range(6):
            hh1 = h11(sd * 13.0 + j * 1.7); hh2 = h11(sd * 29.0 + j * 2.3)
            cx = (hh1 - 0.5) * 0.1 * amt; cy = (-0.016 - hh2 * 0.05) * amt
            if j >= 4: cy = (0.016 + hh2 * 0.03) * amt
            sz = (0.0035 + 0.004 * h11(hh1 * 7.0)) * min(amt * 2.0, 1.0)
            dd = np.hypot(s - cx, t - cy)
            b_ = np.maximum(b_, ss(sz, sz * 0.35, dd) if sz > 0 else 0)
        sc = (tex(sd * 5.0 + 0.5, t * 20.0) - 0.5) * gw * 1.1
        seam = np.abs(sp - sc)
        core = ss(0.032, 0.012, np.abs(t))
        flick = 0.75 + 0.25 * np.sin(TIME * 2.7 + sd * 31.0)
        e_ = (ss(0.0055, 0.001, seam) * 0.95 + np.exp(-seam * 80.0) * 0.35) * core * amt * flick
        dist = np.hypot(s * 0.7, t)
        e_ = e_ + hot * np.exp(-dist * 28.0) * 1.4
        g_ = heal * np.exp(-dist * 22.0) * 1.3
        soft = np.exp(-(sp / (gw + 0.012)) ** 2) * amt
        cut = np.where(m, np.maximum(cut, c_), cut)
        bits = np.where(m, np.maximum(bits, b_), bits)
        ember = np.where(m, ember + e_, ember)
        gold = np.where(m, gold + g_, gold)
        halo_k = np.where(m, np.minimum(halo_k, 1 - soft * 0.75), halo_k)
    ca = ca * (1 - cut)
    ca = np.maximum(ca, np.maximum(inner, bits * 0.8 * (0.55 + 0.45 * grain)))
    halo = np.exp(-d * 16.0) * (0.16 + pulse * 0.5) * halo_k
    chalk = np.array([0.92, 0.9, 0.83])
    col = chalk * (1 - danger * 0.65) + np.array([1.0, 0.22, 0.18]) * danger * 0.65
    base = np.clip(ca + halo, 0, 1)
    ember = np.clip(ember, 0, 1); gold = np.clip(gold, 0, 1)
    glow = np.array([1.0, 0.28, 0.1]) * ember[..., None] + np.array([1.0, 0.85, 0.45]) * gold[..., None]
    alpha = np.clip(base + ember * 0.7 + gold, 0, 1)
    rgb = np.minimum((col * base[..., None] + glow) / np.maximum(alpha, 1e-3)[..., None], 1)
    return rgb, alpha
def comp(rgb, alpha, bg=(0.05, 0.04, 0.05)):
    out = np.array(bg) * (1 - alpha[..., None]) + rgb * alpha[..., None]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()
    os.makedirs(out, exist_ok=True)
    # Трещина: (угол, раскрытие 0..1, вспышка раны 0..1, свечение лечения 0..1) — как crack_* в шейдере.
    cr = [(0.3, 1.0, 0.0, 0.0), (2.1, 1.0, 0.0, 0.0), (4.0, 1.0, 0.0, 0.0)]
    cr5 = cr + [(5.3, 1.0, 0.0, 0.0), (1.2, 0.6, 0.9, 0.0)]
    heal = [(0.3, 1.0, 0, 0), (2.1, 0.4, 0, 0.95)]
    imgs = [comp(*render([])), comp(*render(cr)), comp(*render(cr5, danger=0.55)), comp(*render(heal))]
    sheet = Image.new('RGB', (1280, 1280))
    for k, im in enumerate(imgs):
        sheet.paste(im, ((k % 2) * 640, (k // 2) * 640))
    sheet.save(os.path.join(out, 'chalk_ring_sheet.png'))
    rgb, al = render([(math.pi / 2, 1.0, 0, 0)], N=1280)
    comp(rgb, al).crop((480, 1022, 800, 1202)).resize((960, 540), Image.NEAREST).save(os.path.join(out, 'chalk_ring_zoom.png'))
    print('превью:', os.path.join(out, 'chalk_ring_sheet.png'), os.path.join(out, 'chalk_ring_zoom.png'))
