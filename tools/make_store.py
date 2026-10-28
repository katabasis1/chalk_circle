"""Материалы каталога Яндекс Игр: art_src/store/ → store/ в точных размерах (см. docs/STORE.md, раздел 6).

    python3 tools/make_store.py [--logo-pos left|top|right]

art_src/store/icon.png              → store/icon_512.png + store/icon_preview.png (64 и 32 px)
art_src/store/cover.png             → store/<lang>/cover_800x470.png (+ логотип assets/art/gen/logo_<lang>.png)
art_src/store/screens/<lang>/*.png  → store/<lang>/screens/*.png (1080×1920 или 1920×1080)"""
import argparse, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'art_src', 'store')
OUT = os.path.join(ROOT, 'store')
LANGS = ('ru', 'en', 'tr')
COVER = (800, 470)
SHOTS = {'portrait': (1080, 1920), 'landscape': (1920, 1080)}
EXTS = ('.png', '.jpg', '.jpeg', '.webp')


def find(base):
    for e in EXTS:
        if os.path.exists(base + e):
            return base + e
    return None


def cover_crop(im, size):
    W, H = size
    k = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * k)), max(H, round(im.height * k))), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((l, t, l + W, t + H))


def main():
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument('--logo-pos', choices=['left', 'top', 'right'], default='left')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, '.gdignore'), 'a').close()
    warns = []

    p = find(os.path.join(SRC, 'icon'))
    if p:
        im = Image.open(p).convert('RGBA')
        if abs(im.width / im.height - 1) > 0.02:
            warns.append('icon: не квадрат — обрезан по центру')
        if min(im.size) < 512:
            warns.append(f'icon: исходник {im.width}×{im.height} меньше 512 — будет мыльно')
        icon = cover_crop(im, (512, 512))
        if icon.getextrema()[3][0] < 255:
            warns.append('icon: есть прозрачность — для каталога лучше залитый фон (прозрачное подложено тёмным)')
            bg = Image.new('RGBA', icon.size, (12, 10, 14, 255)); bg.alpha_composite(icon); icon = bg
        icon.convert('RGB').save(os.path.join(OUT, 'icon_512.png'), optimize=True)
        prev = Image.new('RGB', (64 + 32 + 48, 64 + 24), (40, 40, 44))
        prev.paste(icon.resize((64, 64), Image.LANCZOS).convert('RGB'), (12, 12))
        prev.paste(icon.resize((32, 32), Image.LANCZOS).convert('RGB'), (64 + 28, 28))
        prev = prev.resize((prev.width * 3, prev.height * 3), Image.NEAREST)
        prev.save(os.path.join(OUT, 'icon_preview.png'))
        print('✓ store/icon_512.png (+ icon_preview.png: так иконка выглядит в 64 и 32 px, увеличено ×3)')
    else:
        print('· нет art_src/store/icon.png — иконка пропущена')

    p = find(os.path.join(SRC, 'cover'))
    if p:
        base = cover_crop(Image.open(p).convert('RGBA'), COVER)
        for lang in LANGS:
            im = base.copy()
            lp = os.path.join(ROOT, 'assets', 'art', 'gen', f'logo_{lang}.png')
            if os.path.exists(lp):
                logo = Image.open(lp).convert('RGBA')
                box = (int(COVER[0] * 0.40), int(COVER[1] * 0.62)) if args.logo_pos != 'top' else (int(COVER[0] * 0.62), int(COVER[1] * 0.34))
                logo.thumbnail(box, Image.LANCZOS)
                if args.logo_pos == 'left':
                    xy = (int(COVER[0] * 0.05), (COVER[1] - logo.height) // 2)
                elif args.logo_pos == 'right':
                    xy = (COVER[0] - logo.width - int(COVER[0] * 0.05), (COVER[1] - logo.height) // 2)
                else:
                    xy = ((COVER[0] - logo.width) // 2, int(COVER[1] * 0.04))
                # мягкая тень под логотипом для читаемости
                sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
                sh.paste((0, 0, 0, 110), (xy[0] + 3, xy[1] + 5), logo.split()[3].point(lambda a: a))
                im.alpha_composite(sh)
                im.alpha_composite(logo, xy)
            else:
                warns.append(f'cover/{lang}: нет assets/art/gen/logo_{lang}.png — обложка без логотипа')
            os.makedirs(os.path.join(OUT, lang), exist_ok=True)
            im.convert('RGB').save(os.path.join(OUT, lang, 'cover_800x470.png'), optimize=True)
            print(f'✓ store/{lang}/cover_800x470.png')
    else:
        print('· нет art_src/store/cover.png — обложка пропущена')

    for lang in LANGS:
        d = os.path.join(SRC, 'screens', lang)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if os.path.splitext(f)[1].lower() not in EXTS:
                continue
            im = Image.open(os.path.join(d, f)).convert('RGB')
            kind = 'portrait' if im.height > im.width else 'landscape'
            W, H = SHOTS[kind]
            if abs((im.width / im.height) / (W / H) - 1) > 0.03:
                warns.append(f'screens/{lang}/{f}: пропорции {im.width}×{im.height} не {W}:{H} — пропущен (не растягиваю)')
                continue
            if im.width < W * 0.66:
                warns.append(f'screens/{lang}/{f}: {im.width}×{im.height} — маловато, будет мыльно')
            os.makedirs(os.path.join(OUT, lang, 'screens'), exist_ok=True)
            name = os.path.splitext(f)[0] + '.png'
            cover_crop(im, (W, H)).save(os.path.join(OUT, lang, 'screens', name), optimize=True)
            print(f'✓ store/{lang}/screens/{name} ({W}×{H})')
    for w in warns:
        print('⚠', w)


if __name__ == '__main__':
    main()
