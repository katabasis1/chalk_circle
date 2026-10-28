"""Импорт арта нейросети: art_src/ → assets/art/gen/*.png → пересборка сцен и данных → отчёт.

Запуск из корня проекта:
    python3 tools/import_art.py              # импорт новых/изменённых картинок, пересборка, валидация
    python3 tools/import_art.py --force      # переимпортировать всё
    python3 tools/import_art.py --only moshkara_idle,bg_fight
    python3 tools/import_art.py --no-build   # только картинки и отчёт, без build_*.py/validate.py

Что делает с каждой картинкой (art_src/<папка>/<id>.png|.webp|.jpg, список id — tools/art_registry.py):
  1. Фон → прозрачность. Сам определяет, что на картинке:
       настоящая альфа PNG | хромакей #FF00FF / #00FF00 | фальшивая «шахматка» | ровный однотонный фон.
     Хромакей: альфа по «перевесу» ключевого канала, очистка цветной каймы (despill), дырки между руками тоже.
  2. Обрезка по контуру (состояния одного персонажа — общей рамкой, чтобы не «прыгали»), поля, ресайз.
  3. Пишет assets/art/gen/<id>.png и tools/art_manifest.json.
  4. Отчёт docs/ART_STATUS.md (что подключено, чего ждём, замечания) и превью docs/art_preview.png.
  5. Запускает tools/build_data.py, tools/build_scenes.py (они берут PNG вместо SVG-заглушек) и tools/validate.py.
Папка art_src/ содержит .gdignore — Godot её не импортирует, в экспорт она не попадает."""
import argparse, datetime, difflib, hashlib, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from art_registry import ASSETS, BY_ID

VERSION = 3  # меняй при изменении обработки — всё переимпортируется
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'art_src')
OUT = os.path.join(ROOT, 'assets', 'art', 'gen')
MANIFEST = os.path.join(ROOT, 'tools', 'art_manifest.json')
REPORT = os.path.join(ROOT, 'docs', 'ART_STATUS.md')
PREVIEW = os.path.join(ROOT, 'docs', 'art_preview.png')
EXTS = ('.png', '.webp', '.jpg', '.jpeg')
KEYS = {'magenta': np.array([255., 0., 255.]), 'green': np.array([0., 255., 0.])}
MODE_RU = {'alpha': 'прозрачный PNG', 'key-magenta': 'хромакей #FF00FF', 'key-green': 'хромакей #00FF00',
           'checker': 'фальшивая шахматка → вырезана', 'solid': 'однотонный фон → вырезан', 'none': 'фон не распознан', 'bg': 'фон'}


# ======================================================================= поиск исходников
def norm(stem):
    return stem.lower().replace('-', '_').replace(' ', '_')


def index_sources():
    idx, extra = {}, []
    if not os.path.isdir(SRC):
        return idx, extra
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            stem, ext = os.path.splitext(f)
            if ext.lower() not in EXTS:
                continue
            p = os.path.join(dp, f)
            k = norm(stem)
            if k in BY_ID:
                if k in idx:  # два файла на один id — берём свежий
                    if os.path.getmtime(p) <= os.path.getmtime(idx[k]):
                        continue
                idx[k] = p
            else:
                extra.append(p)
    return idx, extra


def sha(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()[:16]


# ======================================================================= фон → альфа
def load(path):
    im = Image.open(path)
    im.load()
    return np.asarray(im.convert('RGBA')).astype(np.float32)  # 0..255


def border(rgb, frac=0.015):
    h, w = rgb.shape[:2]
    b = max(2, int(min(h, w) * frac))
    return np.concatenate([rgb[:b].reshape(-1, 3), rgb[-b:].reshape(-1, 3),
                           rgb[:, :b].reshape(-1, 3), rgb[:, -b:].reshape(-1, 3)])


def detect(img, hint):
    a = img[..., 3]
    if (a < 128).mean() > 0.01:
        return 'alpha', None
    bp = border(img[..., :3])
    order = [hint] + [k for k in KEYS if k != hint] if hint in KEYS else list(KEYS)
    for name in order:
        if (np.linalg.norm(bp - KEYS[name], axis=1) < 110).mean() > 0.6:
            return 'key-' + name, np.median(bp[np.linalg.norm(bp - KEYS[name], axis=1) < 110], axis=0)
    neutral = (bp.max(1) - bp.min(1)) < 16
    if neutral.mean() > 0.85:
        lum = bp[neutral].mean(1)
        lo, hi = np.percentile(lum, 8), np.percentile(lum, 92)
        if hi - lo > 14:
            return 'checker', (lo, hi)
    if bp.std(0).max() < 12:
        return 'solid', np.median(bp, axis=0)
    return 'none', None


def touching_or_big(mask, min_area):
    """Компоненты маски, касающиеся края кадра или площадью ≥ min_area (дырки между руками и т. п.)."""
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask & False
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    area = ndimage.sum(mask, lab, index=np.arange(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[edge] = True
    keep[1:][area >= min_area] = True
    keep[0] = False
    return keep[lab]


def matte_key(img, name, bgcol):
    rgb = img[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if name == 'green':
        dom = g - np.maximum(r, b)
        full = max(80.0, bgcol[1] - max(bgcol[0], bgcol[2]))
    else:
        dom = np.minimum(r, b) - g
        full = max(80.0, min(bgcol[0], bgcol[2]) - bgcol[1])
    lo = 48.0
    a_dom = np.clip(1.0 - (dom - lo) / (full * 0.85 - lo), 0.0, 1.0)
    core = np.linalg.norm(rgb - bgcol, axis=2) < 100
    bg = touching_or_big(core, 64)
    band = ndimage.binary_dilation(bg, iterations=3) & ~bg
    alpha = np.ones(rgb.shape[:2], np.float32)
    alpha[bg] = 0.0
    alpha[band] = a_dom[band]
    # «размешиваем» цвет каймы: Obs = a*C + (1-a)*K
    out = rgb.copy()
    m = band & (alpha > 0.02)
    a3 = alpha[m][:, None]
    out[m] = np.clip((rgb[m] - (1 - a3) * bgcol) / a3, 0, 255)
    # despill в кайме
    o = out[band]
    if name == 'green':
        o[:, 1] = np.minimum(o[:, 1], np.maximum(o[:, 0], o[:, 2]))
    else:
        ex = np.clip(np.minimum(o[:, 0], o[:, 2]) - o[:, 1], 0, None)
        o[:, 0] -= ex; o[:, 2] -= ex
    out[band] = o
    left = ((np.linalg.norm(out - bgcol, axis=2) < 60) & (alpha > 0.5)).mean()
    warns = []
    if left > 0.001:
        warns.append(f'внутри осталось {left*100:.1f}% цвета хромакея — проверь превью')
    return np.dstack([out, alpha * 255]), warns


def matte_flood(img, bgmask_fn, hole_test):
    rgb = img[..., :3]
    cand = bgmask_fn(rgb)
    lab, n = ndimage.label(cand)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge)) if edge else np.zeros_like(cand)
    holes = 0
    if n:
        objs = ndimage.find_objects(lab)
        for i, sl in enumerate(objs, start=1):
            if i in edge or sl is None:
                continue
            comp = lab[sl] == i
            if comp.sum() < 400:
                continue
            if hole_test(rgb[sl][comp]):
                bg[sl] |= comp
                holes += 1
    alpha = (~bg).astype(np.float32)
    soft = ndimage.gaussian_filter(alpha, 0.7)
    alpha = np.where(bg, 0.0, np.minimum(1.0, soft * 1.25))
    warns = [f'вырезано внутренних «дырок»: {holes} — проверь превью'] if holes else []
    return np.dstack([rgb, alpha * 255]), warns


def make_alpha(img, hint):
    mode, info = detect(img, hint)
    if mode == 'alpha':
        img = img.copy()
        img[..., 3][img[..., 3] < 4] = 0
        return img, mode, []
    if mode.startswith('key-'):
        out, w = matte_key(img, mode[4:], info)
        return out, mode, w
    if mode == 'checker':
        lo, hi = info
        def cand(rgb):
            return ((rgb.max(2) - rgb.min(2)) < 18) & (rgb.mean(2) > lo - 18)
        def hole(px):
            l = px.mean(1)
            return (l > (lo + hi) / 2).mean() > 0.2 and (l < (lo + hi) / 2).mean() > 0.2
        out, w = matte_flood(img, cand, hole)
        return out, mode, w + ['у картинки была фальшивая прозрачность (шахматка) — лучше перегенерировать с хромакеем']
    if mode == 'solid':
        col = info
        def cand(rgb):
            return np.linalg.norm(rgb - col, axis=2) < 40
        def hole(px):
            return np.linalg.norm(px.mean(0) - col) < 25
        out, w = matte_flood(img, cand, hole)
        return out, mode, w
    return img, mode, ['фон не распознан (нет прозрачности, хромакея или шахматки) — картинка взята как есть']


# ======================================================================= обрезка и ресайз
def bbox(alpha, thr=12):
    ys, xs = np.where(alpha > thr)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def edge_touch(img, bb):
    h, w = img.shape[:2]
    return bb[0] <= 1 or bb[1] <= 1 or bb[2] >= w - 1 or bb[3] >= h - 1


def to_image(arr):
    return Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8), 'RGBA')


def resize_rgba(im, size):
    if im.size == tuple(size):
        return im
    return im.convert('RGBa').resize(tuple(size), Image.LANCZOS).convert('RGBA')


def fit(w, h, maxside):
    k = min(1.0, maxside / max(w, h))
    return max(1, round(w * k)), max(1, round(h * k))


def pad(im, frac):
    w, h = im.size
    p = int(round(max(w, h) * frac))
    out = Image.new('RGBA', (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
    out.paste(im, (p, p))
    return out


def crop(arr, bb):
    return to_image(arr[bb[1]:bb[3], bb[0]:bb[2]])


def process_group(members, srcs, args):
    """members: [Asset] одной группы (или один). Возвращает {id: (Image, mode, warns)}."""
    res, mats = {}, {}
    for a in members:
        img = load(srcs[a.id])
        if a.kind == 'bg':
            rgb = img[..., :3] * (img[..., 3:4] / 255.0)
            im = Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), 'RGB')
            W, H = a.px
            k = max(W / im.width, H / im.height)
            im = im.resize((max(W, round(im.width * k)), max(H, round(im.height * k))), Image.LANCZOS)
            l, t = (im.width - W) // 2, (im.height - H) // 2
            warns = []
            if abs(im.width / im.height - W / H) > 0.08:
                warns.append(f'пропорции исходника не {W}×{H} — края обрезаны')
            res[a.id] = (im.crop((l, t, l + W, t + H)), 'bg', warns)
            continue
        arr, mode, warns = make_alpha(img, args.key or a.key)
        mats[a.id] = (arr, mode, warns)
    # общая рамка для группы спрайтов
    sprites = [a for a in members if a.id in mats and a.kind == 'sprite']
    union = None
    if len(sprites) > 1:
        shapes = {mats[a.id][0].shape[:2] for a in sprites}
        if len(shapes) == 1:
            bbs = [bbox(mats[a.id][0][..., 3]) for a in sprites]
            bbs = [b for b in bbs if b]
            if bbs:
                union = [min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs)]
        else:
            for a in sprites:
                mats[a.id][2].append('размер холста отличается от других состояний — обрезано отдельно, масштаб может «прыгать»')
    for aid, (arr, mode, warns) in mats.items():
        a = BY_ID[aid]
        bb = bbox(arr[..., 3])
        if bb is None:
            res[aid] = (None, mode, warns + ['картинка пустая после удаления фона'])
            continue
        if a.kind in ('sprite', 'icon', 'logo') and edge_touch(arr, bb):
            warns.append('фигура касается края кадра — возможно, обрезана')
        if a.kind == 'sprite':
            im = pad(crop(arr, union or bb), 0.03)
            im = resize_rgba(im, fit(*im.size, a.px))
        elif a.kind == 'logo':
            im = pad(crop(arr, bb), 0.02)
            im = resize_rgba(im, fit(*im.size, a.px))
        elif a.kind == 'icon':
            im = crop(arr, bb)
            side = int(round(max(im.size) / 0.9))
            sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
            sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
            im = resize_rgba(sq, (a.px, a.px))
        else:  # overlay — холст целиком
            im = resize_rgba(to_image(arr), fit(arr.shape[1], arr.shape[0], a.px))
        res[aid] = (im, mode, warns)
    return res


# ======================================================================= отчёт
def write_report(man, srcs, extra):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    done = sum(1 for a in ASSETS if a.id in man)
    L = ['# Статус арта — генерируется `tools/import_art.py`, руками не править', '',
         f'Обновлено: {now}. Подключено **{done} из {len(ASSETS)}**.', '',
         'Как добавить картинку: положи её в `art_src/<папка>/<id>.png` (имена — в таблицах ниже, промты — `docs/ART_PROMPTS.md`) '
         'и запусти `python3 tools/import_art.py`. Можно слать мне партиями — импорт сделаю сам.', '',
         'Статусы: ✅ подключено · ⚠️ подключено, но есть замечания · ⏳ ждём картинку (в игре — SVG-заглушка) · ➕ ждём картинку (новый ассет, заглушки нет)', '']
    sec = None
    for a in ASSETS:
        if a.section != sec:
            sec = a.section
            L += ['', f'## {sec}', '', '| Файл | Статус | Итог | Где в игре | Замечания |', '|---|---|---|---|---|']
        f = f'`art_src/{a.dir}/{a.id}.png`'
        if a.id in man:
            m = man[a.id]
            st = '⚠️' if m['warnings'] else '✅'
            size = f"{m['w']}×{m['h']}"
            note = '; '.join([MODE_RU.get(m['mode'], m['mode'])] + m['warnings'])
        else:
            st = f'⏳ заглушка `{a.fallback}`' if a.fallback else '➕'
            size, note = '—', ''
        L.append(f'| {f} | {st} | {size} | {a.uses} | {note} |')
    if extra:
        L += ['', '## Файлы в art_src, которые не узнаны', '', 'Имя не совпадает ни с одним id из `tools/art_registry.py` — переименуй:', '']
        ids = [a.id for a in ASSETS]
        for p in extra:
            stem = norm(os.path.splitext(os.path.basename(p))[0])
            sug = difflib.get_close_matches(stem, ids, n=2, cutoff=0.5)
            L.append(f"* `{os.path.relpath(p, ROOT)}`" + (f" → может, `{'` или `'.join(sug)}`?" if sug else ''))
    L.append('')
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))


def write_preview(man):
    ids = [a.id for a in ASSETS if a.id in man]
    if not ids:
        if os.path.exists(PREVIEW):
            os.remove(PREVIEW)
        return
    cell, cols, lab = 180, 6, 26
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * cell, rows * (cell + lab)), (24, 22, 30, 255))
    try:
        font = ImageFont.truetype(os.path.join(ROOT, 'assets/fonts/Body.ttf'), 16)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, aid in enumerate(ids):
        x, y = (i % cols) * cell, (i // cols) * (cell + lab)
        # шахматка под альфой, чтобы видеть кайму
        for cy in range(0, cell, 15):
            for cx in range(0, cell, 15):
                if (cx // 15 + cy // 15) % 2:
                    d.rectangle([x + cx, y + cy, x + cx + 14, y + cy + 14], fill=(52, 48, 60, 255))
        im = Image.open(os.path.join(OUT, man[aid]['file'])).convert('RGBA')
        im.thumbnail((cell - 12, cell - 12), Image.LANCZOS)
        sheet.alpha_composite(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        col = (255, 200, 90, 255) if man[aid]['warnings'] else (225, 220, 205, 255)
        d.text((x + 6, y + cell + 3), aid, font=font, fill=col)
    sheet.convert('RGB').save(PREVIEW, optimize=True)


# ======================================================================= main
def main():
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--only', default='')
    ap.add_argument('--key', choices=['magenta', 'green'], default=None, help='принудительный цвет хромакея')
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SRC, exist_ok=True)
    gd = os.path.join(SRC, '.gdignore')
    if not os.path.exists(gd):
        open(gd, 'w').close()
    old = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding='utf-8') as f:
            old = json.load(f).get('assets', {})
    srcs, extra = index_sources()
    only = set(x.strip() for x in args.only.split(',') if x.strip())
    bad = only - set(BY_ID)
    if bad:
        sys.exit(f'--only: нет таких id: {", ".join(sorted(bad))}')

    hashes = {aid: sha(p) + f'v{VERSION}' for aid, p in srcs.items()}
    groups = {}
    for a in ASSETS:
        if a.id in srcs:
            groups.setdefault(a.group or a.id, []).append(a)
    man, n_new = {}, 0
    for g, members in groups.items():
        ghash = hashlib.sha1(''.join(hashes[a.id] + repr(a) for a in members).encode()).hexdigest()[:16]
        same = all(a.id in old and old[a.id].get('group_hash') == ghash and os.path.exists(os.path.join(OUT, old[a.id]['file']))
                   for a in members)
        want = not only or any(a.id in only for a in members)
        if same and not args.force or not want:
            for a in members:
                if a.id in old and os.path.exists(os.path.join(OUT, old[a.id]['file'])):
                    man[a.id] = old[a.id]
            continue
        res = process_group(members, srcs, args)
        for a in members:
            im, mode, warns = res[a.id]
            if im is None:
                print(f'  ✗ {a.id}: {"; ".join(warns)}')
                continue
            fn = a.id + '.png'
            im.save(os.path.join(OUT, fn), optimize=True)
            man[a.id] = dict(file=fn, w=im.width, h=im.height, mode=mode, warnings=warns,
                             src=os.path.relpath(srcs[a.id], ROOT), group_hash=ghash)
            n_new += 1
            print(f'  ✓ {a.id}: {im.width}×{im.height}, {MODE_RU.get(mode, mode)}' + (f'  ⚠ {"; ".join(warns)}' if warns else ''))
    # убрать устаревшие (исходник удалён)
    for f in os.listdir(OUT):
        stem, ext = os.path.splitext(f)
        if ext == '.png' and stem not in man:
            os.remove(os.path.join(OUT, f))
            imp = os.path.join(OUT, f + '.import')
            if os.path.exists(imp):
                os.remove(imp)
            print(f'  − {stem}: исходника больше нет, удалено из assets/art/gen')
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump({'version': VERSION, 'assets': dict(sorted(man.items()))}, f, ensure_ascii=False, indent=1)
    write_report(man, srcs, extra)
    write_preview(man)
    print(f'арт: подключено {len(man)} из {len(ASSETS)}, обработано сейчас {n_new}; отчёт docs/ART_STATUS.md')
    for p in extra:
        print(f'  ? не узнан: {os.path.relpath(p, ROOT)} (см. отчёт)')
    if args.no_build:
        return
    py = sys.executable
    for s in ('build_data.py', 'build_scenes.py'):
        subprocess.run([py, os.path.join(ROOT, 'tools', s)], cwd=ROOT, check=True)
    r = subprocess.run([py, os.path.join(ROOT, 'tools', 'validate.py')], cwd=ROOT)
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()
