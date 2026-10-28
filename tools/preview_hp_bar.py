"""Превью дуги здоровья с «призраком» (пункт 2.7) без Godot: numpy-порт assets/shaders/arc.gdshader
(без зоны «Идеально» и замаха) + тайминги из scenes/fight/hp_bar.gd (константы читаются из файла).

Держи в синхроне с шейдером и hp_bar.gd: правишь формулы или кривые там — правь и здесь.
Запуск из корня проекта:
    python3 tools/preview_hp_bar.py [папка]     # по умолчанию — системная временная папка
Пишет hp_bar_timeline.png: два удара подряд (крупный 100→78 и 78→66 через 0.25 с) — кадры от удара до того,
как след стёк. Цвета дуг — из tscn hp_bar (Ghost / Arc).
"""
import math
import os
import re
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'art', 'noise.png')).convert('L'), dtype=np.float32) / 255.0
NH, NW = NO.shape
SRC = open(os.path.join(ROOT, 'scenes', 'fight', 'hp_bar.gd'), encoding='utf-8').read()
TSCN = open(os.path.join(ROOT, 'scenes', 'fight', 'hp_bar.tscn'), encoding='utf-8').read()
def const(name): return float(re.search(rf'^const {name}: float = ([0-9.]+)', SRC, re.M).group(1))
SNAP, HOLD, DRAIN, BIG = const('SNAP_TIME'), const('GHOST_HOLD'), const('GHOST_DRAIN'), const('BIG_CHUNK')
AF, AF_BIG = const('ARC_FLASH'), const('ARC_FLASH_BIG')

def mat_params(node):
    """shader_parameter/* материала узла node из hp_bar.tscn."""
    mid = re.search(rf'\[node name="{node}"[^\]]*\]\n(?:.*\n)*?material = SubResource\("([^"]+)"\)', TSCN).group(1)
    block = TSCN.split(f'id="{mid}"]', 1)[1].split('\n[', 1)[0]
    out = {}
    for k, v in re.findall(r'shader_parameter/(\w+) = (.+)', block):
        m = re.match(r'Color\(([^)]+)\)', v)
        out[k] = np.array([float(x) for x in m.group(1).split(',')]) if m else (float(v) if re.match(r'^-?[0-9.]+$', v) else v)
    return out
GHOST, ARC = mat_params('Ghost'), mat_params('Arc')

def tex(u, v):
    x = (u * NW - 0.5) % NW; y = (v * NH - 0.5) % NH
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    x1 = (x0 + 1) % NW; y1 = (y0 + 1) % NH
    return (NO[y0, x0] * (1 - fx) + NO[y0, x1] * fx) * (1 - fy) + (NO[y1, x0] * (1 - fx) + NO[y1, x1] * fx) * fy
def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def arc(P, arc_size, flash=0.0, TIME=0.0, N=300):
    ys, xs = np.mgrid[0:N, 0:N]
    px = (xs + 0.5) / N * 2 - 1; py = (ys + 0.5) / N * 2 - 1
    r = np.hypot(px, py); a = np.arctan2(py, px)
    hot = P.get('hot', 0.0); alpha = P.get('alpha', 1.0)
    d = np.abs(np.mod(a - P['center'] + math.pi, 2 * math.pi) - math.pi)
    hw = max(arc_size * P['grow'] * 0.5, 0.0)
    n = tex(a / (2 * math.pi) * 4.0 + TIME * 0.03, r * 1.3 - TIME * 0.45 * hot)
    wob = (n - 0.5) * 0.045 * hot
    sd = np.minimum((hw - d) * r, np.minimum(r - P['r_in'], P['r_out'] - r) + wob)
    gy, gx = np.gradient(sd)
    aa = np.abs(gx) + np.abs(gy) + 0.002
    body = ss(-aa, aa, sd); core = ss(0.0, 0.05, sd); glow = np.exp(-np.maximum(-sd, 0) * 26.0)
    c = P['color'][:3]; g = P['glow_color'][:3]
    col = c * 0.8 + (c * 1.2 - c * 0.8) * core[..., None]
    col = col + ((n - 0.4) * 0.35 * hot)[..., None] * g
    col = col + (1.0 - col) * flash
    ga = glow * (0.5 + 0.7 * flash) * P.get('glow_amount', 1.0) * (1 - body)
    outc = g + (col - g) * body[..., None]
    return np.clip(outc, 0, 1), np.clip(np.maximum(body, ga) * alpha, 0, 1)

def ease_out_quad(t): return 1 - (1 - t) ** 2
def ease_in_out_quad(t): return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2

def state(t, hits):
    """(shown, ghost, ghost_flash, arc_flash) в момент t — как hp_bar.gd: hits = [(время, доля после удара)], до них 1.0."""
    shown = ghost = ratio = 1.0
    arc_from, arc_t0, g_from, g_t0, last = 1.0, -9.0, 1.0, -9.0, None
    for th, r in hits:
        if th > t: break
        # состояние на момент удара
        k = min((th - arc_t0) / SNAP, 1.0); cur = arc_from + (ratio - arc_from) * ease_out_quad(max(k, 0)) if arc_t0 > -9 else ratio
        gk = (th - g_t0 - HOLD) / DRAIN
        gcur = g_from if gk <= 0 else (g_from + (ratio - g_from) * ease_in_out_quad(min(gk, 1.0)))
        if g_t0 <= -9: gcur = cur
        chunk = ratio - r
        g_from = max(gcur, cur, r); g_t0 = th
        arc_from, arc_t0 = cur, th
        ratio = r; last = (th, chunk >= BIG)
    if last is None: return 1.0, 1.0, 0.0, 0.0
    k = min((t - arc_t0) / SNAP, 1.0); shown = arc_from + (ratio - arc_from) * ease_out_quad(k)
    gk = (t - g_t0 - HOLD) / DRAIN
    ghost = g_from if gk <= 0 else g_from + (ratio - g_from) * ease_in_out_quad(min(gk, 1.0))
    dt = t - last[0]
    gf = max(0.0, 1 - dt / 0.3); af = max(0.0, (AF_BIG if last[1] else AF) * (1 - dt / 0.15))
    return shown, ghost, gf, af

def frame(t, hits, hp_max, N=300):
    shown, ghost, gf, af = state(t, hits)
    bg = np.ones((N, N, 3)) * np.array([0.05, 0.04, 0.05])
    if ghost > shown + 0.001:
        c, a = arc(GHOST, 2 * math.pi * ghost, gf, t, N); bg = bg * (1 - a[..., None]) + c * a[..., None]
    c, a = arc(ARC, 2 * math.pi * shown, af, t, N); bg = bg * (1 - a[..., None]) + c * a[..., None]
    img = Image.fromarray((bg * 255).astype(np.uint8))
    hp = hp_max
    for th, r in hits:
        if th <= t: hp = round(hp_max * r)
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', 'Title.ttf'), 72)
    dr.text((N / 2, N / 2), str(hp), font=font, fill=(255, 255, 255), anchor='mm', stroke_width=4, stroke_fill=(5, 3, 5))
    return img, shown, ghost

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()
    hits = [(0.0, 0.78), (0.25, 0.66)]
    times = [-0.05, 0.03, 0.2, 0.3, 0.6, 0.85, 1.0, 1.25]
    N = 300; pad = 46
    sheet = Image.new('RGB', (N * len(times), N + pad), (12, 10, 12))
    small = ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', 'Body.ttf'), 20)
    dr = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        img, shown, ghost = frame(t, hits, 100, N)
        sheet.paste(img, (i * N, 0))
        dr.text((i * N + N / 2, N + pad / 2), f't={t:+.2f}  дуга {shown:.2f}  след {ghost:.2f}', font=small, fill=(220, 210, 190), anchor='mm')
    p = os.path.join(out, 'hp_bar_timeline.png'); sheet.save(p); print(p)

if __name__ == '__main__':
    main()
