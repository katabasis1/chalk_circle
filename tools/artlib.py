"""art() / art_scale() для генераторов сцен и данных (build_scenes.py, build_data.py).

art('moshkara_idle')        → 'res://assets/art/gen/moshkara_idle.png', если картинка импортирована,
                              иначе SVG-заглушка из реестра ('res://assets/art/enemy_moshkara.svg'),
                              иначе None (новый ассет без заглушки).
art_scale('moshkara_idle', 0.85) → масштаб, при котором PNG занимает ту же «коробку», что заглушка при 0.85.
                              Для заглушки возвращает base без изменений.
has_art('bg_fight_wide')    → True, если картинка импортирована.
Манифест импорта: tools/art_manifest.json (пишет tools/import_art.py)."""
import json, os, re
from art_registry import BY_ID

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MANIFEST = os.path.join(ROOT, 'tools', 'art_manifest.json')
GEN = 'res://assets/art/gen/'
ART = 'res://assets/art/'
_cache = {}


def manifest():
    if 'm' not in _cache:
        m = {}
        if os.path.exists(MANIFEST):
            with open(MANIFEST, encoding='utf-8') as f:
                m = json.load(f).get('assets', {})
        # только то, что реально лежит на диске
        _cache['m'] = {k: v for k, v in m.items() if os.path.exists(os.path.join(ROOT, 'assets/art/gen', v['file']))}
    return _cache['m']


def _asset(aid):
    if aid not in BY_ID:
        raise KeyError(f'art(): «{aid}» нет в tools/art_registry.py')
    return BY_ID[aid]


def has_art(aid):
    _asset(aid)
    return aid in manifest()


def art(aid, fallback=True):
    a = _asset(aid)
    m = manifest()
    if aid in m:
        return GEN + m[aid]['file']
    if fallback and a.fallback:
        return ART + a.fallback
    return None


def svg_size(name):
    with open(os.path.join(ROOT, 'assets/art', name), encoding='utf-8') as f:
        head = f.read(4096)
    tag = re.search(r'<svg[^>]*>', head).group(0)
    w = re.search(r'\bwidth="([\d.]+)', tag); h = re.search(r'\bheight="([\d.]+)', tag)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', tag)
    return float(vb.group(1)), float(vb.group(2))


def art_scale(aid, base=1.0):
    """Масштаб Sprite2D: PNG вписывается в коробку SVG-заглушки (svg_w*base × svg_h*base) с долей fill."""
    a = _asset(aid)
    m = manifest()
    if aid not in m:
        return base
    pw, ph = m[aid]['w'], m[aid]['h']
    if not a.fallback:
        return base
    sw, sh = svg_size(a.fallback)
    return round(base * min(sw / pw, sh / ph) * a.fill, 4)


def art_ratio(aid, base=1.0):
    """Во сколько раз art_scale отличается от base — чтобы домножать дорожки анимаций Sprite:scale."""
    return art_scale(aid, base) / base if base else 1.0
