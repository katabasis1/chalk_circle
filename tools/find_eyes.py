"""Подсказка для art_src/eyes.json: ищет глаза нечисти на импортированных PNG (assets/art/gen/<id>.png).

Глаза = самые яркие насыщенные пятна сигнатурного цвета персонажа. Скрипт печатает кандидатов
(доли картинки u, v — как нужно в eyes.json) и при --preview рисует их номера поверх картинки.
Выбери нужные 1–2 точки, впиши в art_src/eyes.json и запусти tools/build_data.py (или import_art.py).
ВАЖНО: координаты — в долях ИТОГОВОЙ PNG. После замены картинки или добавления состояний
(import_art.py кадрирует все состояния персонажа общей рамкой) — разметку надо обновить.

  python3 tools/find_eyes.py                      # все idle нечисти
  python3 tools/find_eyes.py moshkara_idle --preview /tmp/eyes.png
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIG = {'moshkara': '#A6D23A', 'svecheed': '#FF8A2A', 'sheptuha': '#B768FF', 'motanka': '#E0283C',
       'podpolnik': '#38D6B0', 'hozyaika': '#FF1F3D'}


def candidates(path, hexc, top=6):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    H, W = al.shape
    c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)], float)
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / (mx + 1e-6)
    dist = np.linalg.norm(rgb / (mx[..., None] + 1e-6) - c / c.max(), axis=-1)
    lab, k = ndimage.label((al > 200) & (mx > 170) & (sat > 0.45) & (dist < 0.35))
    out = []
    for i in range(1, k + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 25:
            continue
        r = math.sqrt(len(ys) / math.pi) / H * 0.8
        out.append(dict(area=len(ys), u=round(xs.mean() / W, 3), v=round(ys.mean() / H, 3),
                        size=round(min(max(r, 0.014), 0.024), 4)))
    out.sort(key=lambda d: -d['area'])
    return out[:top], (W, H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*', default=[f'{n}_idle' for n in SIG])
    ap.add_argument('--color', help='сигнатурный цвет #RRGGBB (по умолчанию — из таблицы SIG)')
    ap.add_argument('--preview', help='куда сохранить картинку с номерами кандидатов (один id)')
    a = ap.parse_args()
    for aid in a.ids:
        path = os.path.join(ROOT, 'assets', 'art', 'gen', aid + '.png')
        if not os.path.exists(path):
            print(f'{aid}: нет {path} — сначала import_art.py'); continue
        hexc = a.color or SIG.get(aid.split('_')[0])
        if not hexc:
            print(f'{aid}: неизвестен цвет, укажи --color'); continue
        cands, (W, H) = candidates(path, hexc)
        print(f'{aid} ({W}×{H}), цвет {hexc}:')
        for i, d in enumerate(cands):
            print(f'  [{i}] u={d["u"]:.3f} v={d["v"]:.3f}  площадь {d["area"]} px  size≈{d["size"]}')
        if a.preview:
            im = Image.open(path).convert('RGBA')
            bg = Image.new('RGBA', im.size, (40, 40, 48, 255)); bg.alpha_composite(im)
            dr = ImageDraw.Draw(bg)
            for i, d in enumerate(cands):
                x, y = d['u'] * W, d['v'] * H
                dr.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(255, 255, 255, 255), width=2)
                dr.text((x + 9, y - 9), str(i), fill=(255, 255, 0, 255))
            bg.convert('RGB').save(a.preview)
            print(f'  превью: {a.preview}')


if __name__ == '__main__':
    main()
