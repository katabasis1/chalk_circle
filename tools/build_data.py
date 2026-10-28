"""Генерирует data/*.tres, assets/ui/*.tres (LabelSettings, Theme) и locale/strings.csv.
Запуск из корня проекта: python3 tools/build_data.py"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
A_SCRIPT = 'res://scripts/data/action_data.gd'
I_SCRIPT = 'res://scripts/data/item_data.gd'
N_SCRIPT = 'res://scripts/data/npc_data.gd'
PLAYER, ENEMY, SEAL, UI = 0, 1, 2, 3
SMALL, MEDIUM, LARGE = 0, 1, 2
FOREVER, LONG, NORMAL, SHORT, FLASH = 0, 1, 2, 3, 4
SPELL, CHARM, SPIRIT = 0, 1, 2

def P(rel): return os.path.join(ROOT, rel)

def action_props(doc, a):
    d = {'script': doc.ext('Script', A_SCRIPT)}
    d.update(a); return d

def write_action(rel, a):
    doc = Doc('res', script_class='ActionData')
    doc.res_props = action_props(doc, a)
    doc.save(P(rel))

def write_item(rel, item, action=None):
    doc = Doc('res', script_class='ItemData')
    props = {'script': doc.ext('Script', I_SCRIPT)}
    if action is not None:
        act = doc.sub('Resource', action_props(doc, action), hint='act')
    for k, v in item.items():
        if k == 'icon':
            if v: props[k] = doc.ext('Texture2D', v)
        else: props[k] = v
    if action is not None: props['action'] = act
    doc.res_props = props
    doc.save(P(rel))

# ---------- действия ----------
write_action('data/actions/strike.tres', dict(text='ACT_STRIKE', kind=PLAYER, size=MEDIUM, lifetime=NORMAL, damage=5.0))
write_action('data/actions/seal.tres', dict(text='ACT_SEAL', kind=SEAL, size=SMALL, lifetime=SHORT))
ui = {
    'play': dict(text='UI_PLAY', size=LARGE, fixed_location=0.25),
    'bestiary': dict(text='UI_BESTIARY', size=MEDIUM, fixed_location=0.75),
    'buy': dict(text='SHOP_BUY', size=LARGE, fixed_location=0.51),
    'snack': dict(text='SHOP_SNACK', size=MEDIUM, fixed_location=0.88),
    'reroll': dict(text='SHOP_REROLL', size=MEDIUM, fixed_location=0.05),
    'done': dict(text='SHOP_DONE', size=MEDIUM, fixed_location=0.25),
    'again': dict(text='UI_AGAIN', size=LARGE, fixed_location=0.25),
    'menu': dict(text='UI_MENU', size=MEDIUM, fixed_location=0.5),
    'endless': dict(text='UI_ENDLESS', size=MEDIUM, fixed_location=0.75),
    'revive': dict(text='UI_REVIVE', size=MEDIUM, fixed_location=0.75),
    'continue': dict(text='UI_CONTINUE', size=LARGE, fixed_location=0.25),
    'new_run': dict(text='UI_NEW_RUN', size=MEDIUM, fixed_location=0.02),
}
for k, a in ui.items():
    a = dict(a); a.update(kind=UI, lifetime=FOREVER)
    write_action(f'data/actions/ui/{k}.tres', a)

# ---------- товары Домового ----------
# Иконки: art('<id>') — PNG нейросети из assets/art/gen, если импортирован, иначе SVG-заглушка (или None — без иконки).
items = [
    ('begone', dict(name='IT_BEGONE', type=SPELL, icon=art('begone'), action_stat='damage', action_gain=10.0), dict(text='IT_BEGONE', damage=15.0)),
    ('blood', dict(name='IT_BLOOD', type=SPELL, icon=art('blood'), action_stat='damage', action_gain=40.0), dict(text='IT_BLOOD', damage=40.0, hurt_on_press=True)),
    ('salt', dict(name='IT_SALT', type=SPELL, icon=art('salt'), action_stat='damage_per_enemy_attack', action_gain=10.0), dict(text='IT_SALT', parry=True, damage_per_enemy_attack=10.0)),
    ('copper', dict(name='IT_COPPER', type=SPELL, icon=art('copper'), action_stat='damage_gain', action_gain=1.0), dict(text='IT_COPPER', damage=1.0, damage_gain=1.0)),
    ('horseshoe', dict(name='IT_HORSESHOE', type=CHARM, icon=art('horseshoe'), global_stat='first_hit_bonus', global_gain=0.5), None),
    ('wormwood', dict(name='IT_WORMWOOD', type=CHARM, icon=art('wormwood'), global_stat='dodge_damage', global_gain=2.0), None),
    ('nail', dict(name='IT_NAIL', type=CHARM, icon=art('nail'), global_stat='bonus_damage', global_gain=1.0), None),
    ('rowan', dict(name='IT_ROWAN', type=CHARM, icon=art('rowan'), global_stat='nullified_hits', global_gain=1.0), None),
    ('purse', dict(name='IT_PURSE', type=CHARM, icon=art('purse'), global_stat='free_rerolls', global_gain=1.0), None),
    ('gingerbread', dict(name='IT_GINGER', type=CHARM, icon=art('ginger'), global_stat='free_snacks', global_gain=1.0), None),
    ('jar', dict(name='IT_JAR', type=CHARM, icon=art('jar'), global_stat='jars', global_gain=1.0), None),
    ('wax', dict(name='IT_WAX', type=CHARM, icon=art('wax'), global_stat='max_health', global_gain=1.0), None),
]
for iid, it, act in items:
    it = dict(it); key = it['name']
    it = {'id': SN(iid), 'name': key, 'info': key + '_INFO', 'upgrade_info': key + '_UP', **{k: v for k, v in it.items() if k != 'name'}}
    if act: act = dict(act); act.setdefault('kind', PLAYER); act.setdefault('lifetime', NORMAL)
    write_item(f'data/items/{iid}.tres', it, act)

# ---------- духи (Печать) ----------
spirits = {
    'swarm': ('SP_SWARM', 'moshkara', 'repeats', 2.0, dict(damage=3.0, repeats=2.0)),
    'light': ('SP_LIGHT', 'svecheed', 'next_attack_bonus', 0.5, dict(next_attack_bonus=1.0)),
    'whisper': ('SP_WHISPER', 'sheptuha', 'percent_enemy_hp_damage', 0.05, dict(percent_enemy_hp_damage=0.25)),
    'thread': ('SP_THREAD', 'motanka', 'damage', 15.0, dict(damage=20.0, reverse=True)),
    'grip': ('SP_GRIP', 'podpolnik', 'damage', 5.0, dict(damage=5.0, fatal_money=50)),
}
for sid, (key, npc, stat, gain, act) in spirits.items():
    a = dict(text=key, kind=PLAYER, lifetime=NORMAL, size=MEDIUM); a.update(act)
    write_item(f'data/spirits/{sid}.tres', {'id': SN('spirit_' + sid), 'name': key, 'info': key + '_INFO', 'upgrade_info': key + '_UP',
              'type': SPIRIT, 'icon': art(npc + '_jar'), 'price': 120, 'action_stat': stat, 'action_gain': gain}, a)

# ---------- нечисть ----------
def atk(text, **kw):
    d = dict(text=text, kind=ENEMY, size=MEDIUM, lifetime=SHORT, hurt_on_expire=True); d.update(kw); return d
npcs = {
    'moshkara': ('NPC_MOSHKARA', 'moshkara_idle', '#a6d23a', 'swarm', [atk('ATK_BITE'), atk('ATK_SWARM', move_speed=0.5)], 9.0),
    'svecheed': ('NPC_SVECHEED', 'svecheed_idle', '#ff8a2a', 'light', [atk('ATK_SINGE'), atk('ATK_SNUFF', blind=0.4)], 5.0),
    'sheptuha': ('NPC_SHEPTUHA', 'sheptuha_idle', '#b768ff', 'whisper', [atk('ATK_CURSE'), atk('ATK_WHISPER', speedup=0.05)], 7.0),
    'motanka': ('NPC_MOTANKA', 'motanka_idle', '#e0283c', 'thread', [atk('ATK_PRICK'), atk('ATK_TWIST', reverse=True)], 4.0),
    'podpolnik': ('NPC_PODPOLNIK', 'podpolnik_idle', '#38d6b0', 'grip', [atk('ATK_SCRATCH'), atk('ATK_GRAB', teleport=True)], 3.0),
}
# Глаза (2.4): где вспыхивают блики, когда нечисть замахивается. Для SVG-заглушек — пиксели из tools/gen_art.py
# (glow_eye/зрачки): ((холст), [(x, y)…], радиус блика). Для PNG нейросети точки другие — art_src/eyes.json:
# {"moshkara_idle": {"eyes": [[0.40, 0.43], [0.60, 0.43]], "size": 0.018}} (доли картинки). Нет записи — без бликов.
EYES_SVG = {
    'moshkara_idle': ((512, 512), [(206, 220), (306, 220)], 9),
    'svecheed_idle': ((512, 512), [(234, 186), (278, 186)], 7),
    'sheptuha_idle': ((512, 512), [(238, 168)], 8),  # второй глаз зашит
    'motanka_idle': ((512, 512), [(256, 140)], 12),  # глаз нет — вспыхивает крест на лице
    'podpolnik_idle': ((512, 512), [(226, 340), (286, 340)], 8),
    'hozyaika_idle': ((600, 600), [(284, 126), (316, 126)], 6),
}
EYES_PNG = os.path.join(ROOT, 'art_src', 'eyes.json')
def eyes_for(tex):
    """(список (u, v), радиус в долях высоты) или ([], None)."""
    if has_art(tex):
        if os.path.exists(EYES_PNG):
            import json
            with open(EYES_PNG, encoding='utf-8') as f:
                e = json.load(f).get(tex)
            if e:
                return [tuple(map(float, p)) for p in e['eyes']][:2], float(e.get('size', 0.016))
        print(f'  ! {tex}: PNG без разметки глаз (art_src/eyes.json) — при замахе без бликов')
        return [], None
    if tex not in EYES_SVG:
        return [], None
    (w, h), pts, r = EYES_SVG[tex]
    return [(x / w, y / h) for x, y in pts], max(r / h, 0.012)
def PV2(pts): return Raw('PackedVector2Array(' + ', '.join(f'{fmt(round(u, 4))}, {fmt(round(v, 4))}' for u, v in pts) + ')')

def write_npc(nid, name, tex, color, spirit, actions, float_amount, boss=False, scale=0.85):
    doc = Doc('res', script_class='NpcData')
    props = {'script': doc.ext('Script', N_SCRIPT), 'id': SN(nid), 'name': name, 'texture': doc.ext('Texture2D', art(tex)),
             'color': HEX(color), 'sprite_scale': art_scale(tex, scale), 'float_amount': float_amount, 'boss': boss}
    eyes, eye_size = eyes_for(tex)
    if eyes:
        props['eyes'] = PV2(eyes)
        props['eye_size'] = round(eye_size, 4)
    subs = [doc.sub('Resource', action_props(doc, a), hint='atk') for a in actions]
    props['actions'] = Raw(f'Array[{doc.ext("Script", A_SCRIPT).s}]([' + ', '.join(x.s for x in subs) + '])')
    if spirit: props['spirit'] = doc.ext('Resource', f'res://data/spirits/{spirit}.tres')
    doc.res_props = props
    doc.save(P(f'data/npcs/{nid}.tres'))
for nid, (name, tex, color, spirit, acts, fl) in npcs.items():
    write_npc(nid, name, tex, color, spirit, acts, fl)
U = 'ATK_UNKNOWN'
write_npc('hozyaika', 'NPC_HOZYAIKA', 'hozyaika_idle', '#ff1f3d', None,
          [atk(U, move_speed=0.5), atk(U, blind=0.4), atk(U, speedup=0.05), atk(U, reverse=True), atk(U, teleport=True)], 6.0, boss=True, scale=0.78)

# ---------- стили надписей ----------
TITLE = 'res://assets/fonts/Title.ttf'; BODY = 'res://assets/fonts/Body.ttf'
def ls(name, font, size, outline=0, ocol=(0.02, 0.01, 0.02, 1), shadow=0, scol=(0, 0, 0, 0.6), soff=(0, 4), color=(1, 1, 1, 1)):
    doc = Doc('res', res_type='LabelSettings')
    p = {'font': doc.ext('FontFile', font), 'font_size': size, 'font_color': C(*color)}
    if outline: p['outline_size'] = outline; p['outline_color'] = C(*ocol)
    if shadow: p['shadow_size'] = shadow; p['shadow_color'] = C(*scol); p['shadow_offset'] = V2(*soff)
    doc.res_props = p; doc.save(P(f'assets/ui/{name}.tres'))
ls('ls_section', BODY, 26, outline=9)
ls('ls_pop', TITLE, 62, outline=12, shadow=8, scol=(0.4, 0, 0.05, 0.6))
ls('ls_pop_small', BODY, 32, outline=9)
ls('ls_pop_big', TITLE, 96, outline=16, shadow=12, scol=(0.5, 0.02, 0.05, 0.7), soff=(0, 6))
ls('ls_title', TITLE, 112, outline=0, shadow=24, scol=(0.75, 0.04, 0.06, 0.55), soff=(0, 0), color=(0.95, 0.92, 0.86, 1))
ls('ls_wipe', TITLE, 92, outline=0, shadow=20, scol=(0.7, 0.03, 0.05, 0.6), soff=(0, 0), color=(0.95, 0.92, 0.86, 1))
ls('ls_hud', TITLE, 40, outline=9)
ls('ls_hud_small', BODY, 26, outline=7, color=(0.85, 0.82, 0.76, 1))
ls('ls_center_hp', TITLE, 88, outline=10, shadow=10, scol=(0.5, 0.0, 0.05, 0.5), soff=(0, 0))
ls('ls_center_name', BODY, 28, outline=7)
ls('ls_combo', TITLE, 40, outline=8, shadow=10, scol=(1.0, 0.55, 0.1, 0.45), soff=(0, 0))
ls('ls_combo_small', BODY, 22, outline=6)
ls('ls_card_title', TITLE, 44, outline=8, color=(1, 0.93, 0.78, 1))
ls('ls_body', BODY, 26, outline=6, color=(0.9, 0.87, 0.8, 1))
ls('ls_small', BODY, 22, outline=6, color=(0.78, 0.74, 0.68, 1))

doc = Doc('res', res_type='Theme')
doc.res_props = {'default_font': doc.ext('FontFile', BODY), 'default_font_size': 26}
doc.save(P('assets/ui/theme.tres'))
print('data ok')
