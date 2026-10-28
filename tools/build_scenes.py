"""Генерирует все .tscn проекта (узлы, анимации, связи сигналов). Запуск: python3 tools/build_scenes.py
После генерации сцены — обычные .tscn: правьте их в редакторе (генератор можно больше не запускать)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ART = 'res://assets/art/'; SH = 'res://assets/shaders/'; UI = 'res://assets/ui/'
GLOW = ART + 'glow.png'; NOISE = ART + 'noise.png'
RING_Y = 210.0
ONE = V2(1, 1)
def P(rel): return os.path.join(ROOT, rel)
def add_mat(d): return d.sub('CanvasItemMaterial', {'blend_mode': 1}, hint='add')
def shader_mat(d, shader, params, local=False):
    p = {}
    if local: p['resource_local_to_scene'] = True
    p['shader'] = d.ext('Shader', SH + shader)
    for k, v in params.items(): p['shader_parameter/' + k] = v
    return d.sub('ShaderMaterial', p, hint='mat')
def label(d, ls, extra=None, dynamic=False):
    p = {'label_settings': d.ext('LabelSettings', UI + ls + '.tres'), 'horizontal_alignment': 1, 'vertical_alignment': 1}
    if dynamic: p['auto_translate_mode'] = 2
    if extra: p.update(extra)
    return p
def shaker(d, parent, name='Shaker', unique=False, **props):
    p = {'script': d.ext('Script', 'res://scripts/shaker.gd')}; p.update(props)
    d.node(name, 'Node', parent, p, unique=unique)
def typed_array(d, script_path, items):
    return Raw(f'Array[{d.ext("Script", script_path).s}]([' + ', '.join(i.s for i in items) + '])')
def candles(d, parent='.', dim=1.0):
    scene = d.ext('PackedScene', 'res://scenes/fx/candle.tscn')
    d.node('Candles', 'Node2D', parent, {'position': V2(0, RING_Y), 'modulate': C(dim, dim, dim, 1)})
    for i, a in enumerate([30, 150, 210, 330]):
        r = math.radians(a)
        d.node(f'Candle{i+1}', None, 'Candles', {'position': V2(round(322 * math.cos(r), 1), round(322 * math.sin(r), 1))}, instance=scene)

def particles(d, **kw):
    base = {'texture': d.ext('Texture2D', GLOW), 'material': add_mat(d)}
    base.update(kw); return base

# ======================= section =======================
d = Doc()
mat = shader_mat(d, 'arc.gdshader', {'center': 0.0, 'arc_size': 0.6, 'grow': 0.0, 'r_in': 0.7, 'r_out': 0.84, 'noise_tex': d.ext('Texture2D', NOISE)}, local=True)
anims = {
 'RESET': animation(d, 'RESET', 0.001, [track_value('.:grow', [0], [0.0]), track_value('.:flash', [0], [0.0]), track_value('.:fade', [0], [1.0]),
                                         track_value('.:scale', [0], [ONE]), track_value('Tooltip:modulate', [0], [C(1,1,1,1)]), track_value('Tooltip:scale', [0], [ONE]),
                                         track_value('.:warn', [0], [0.0])]),
 'in': animation(d, 'in', 0.22, [track_value('.:grow', [0, 0.22], [0.0, 1.0], [0.4, 1]), track_value('.:scale', [0, 0.22], [V2(0.9, 0.9), ONE], [0.4, 1]),
                                  track_value('Tooltip:modulate', [0, 0.15], [C(1,1,1,0), C(1,1,1,1)]),
                                  track_value('Tooltip:scale', [0, 0.12, 0.22], [V2(0.6, 0.6), V2(1.12, 1.12), ONE])]),
 'press': animation(d, 'press', 0.32, [track_value('.:flash', [0, 0.3], [1.0, 0.0]), track_value('.:scale', [0, 0.32], [ONE, V2(1.14, 1.14)], [0.4, 1]),
                                        track_value('.:fade', [0, 0.08, 0.32], [1.0, 1.0, 0.0]), track_value('Tooltip:scale', [0, 0.2], [V2(1.35, 1.35), ONE]),
                                        track_value('Tooltip:modulate', [0.1, 0.32], [C(1,1,1,1), C(1,1,1,0)])]),
 'expire': animation(d, 'expire', 0.35, [track_value('.:fade', [0, 0.35], [1.0, 0.0]), track_value('.:scale', [0, 0.35], [ONE, V2(0.92, 0.92)]),
                                          track_value('Tooltip:modulate', [0, 0.3], [C(1,1,1,1), C(1,1,1,0)])]),
 # Замах нечисти (2.4): «charge» — секция проступает контуром (заливку по ходу заряда крутит section.gd),
 # подпись полупрозрачная; «arm» — заряд кончился: вспышка, толчок, подпись в полную силу.
 'charge': animation(d, 'charge', 0.2, [track_value('.:warn', [0], [1.0]), track_value('.:grow', [0], [1.0]), track_value('.:flash', [0], [0.0]),
                                         track_value('.:scale', [0, 0.2], [V2(0.94, 0.94), ONE], [0.4, 1]),
                                         track_value('Tooltip:modulate', [0, 0.2], [C(1,1,1,0), C(1,1,1,0.5)]),
                                         track_value('Tooltip:scale', [0, 0.2], [V2(0.8, 0.8), ONE], [0.4, 1])]),
 'arm': animation(d, 'arm', 0.26, [track_value('.:warn', [0, 0.05], [1.0, 0.0]), track_value('.:grow', [0], [1.0]), track_value('.:flash', [0, 0.26], [0.9, 0.0]),
                                   track_value('.:scale', [0, 0.26], [V2(1.12, 1.12), ONE], [0.4, 1]),
                                   track_value('Tooltip:modulate', [0, 0.08], [C(1,1,1,0.5), C(1,1,1,1)]),
                                   track_value('Tooltip:scale', [0, 0.1, 0.26], [ONE, V2(1.25, 1.25), ONE])]),
}
d.node('Section', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/ring/section.gd')})
d.node('Arc', 'ColorRect', '.', rect(-320, -320, 320, 320, {'mouse_filter': 2, 'material': mat}))
SEAL_S = art_scale('seal', 0.55)
d.node('Icon', 'Sprite2D', '.', {'visible': False, 'texture': d.ext('Texture2D', art('seal')), 'scale': V2(SEAL_S, SEAL_S)})
d.node('Tooltip', 'Node2D', '.')
d.node('Label', 'Label', 'Tooltip', label(d, 'ls_section', rect(0, 0, 10, 10), dynamic=True), unique=True)
anim_player(d, '.', anims)
d.save(P('scenes/ring/section.tscn'))

# ======================= burst =======================
d = Doc()
d.node('Burst', 'CPUParticles2D', None, particles(d, **{
    'script': d.ext('Script', 'res://scenes/fx/burst.gd'), 'emitting': False, 'amount': 22, 'lifetime': 0.55, 'one_shot': True, 'explosiveness': 0.95,
    'emission_shape': 1, 'emission_sphere_radius': 10.0, 'spread': 180.0, 'gravity': V2(0, 520), 'initial_velocity_min': 180.0, 'initial_velocity_max': 460.0,
    'damping_min': 200.0, 'damping_max': 420.0, 'scale_amount_min': 0.08, 'scale_amount_max': 0.22,
    'scale_amount_curve': curve(d, [(0, 1), (1, 0)]), 'color_ramp': gradient(d, [(0, (1, 1, 1, 1)), (0.6, (1, 1, 1, 0.8)), (1, (1, 1, 1, 0))])}))
d.save(P('scenes/fx/burst.tscn'))

# ======================= chips (2.5) =======================
# Сколы мела при ране: куски черты (обычное смешивание — мел непрозрачный), пыль и угольки из щели.
# Узел смотрит +X внутрь круга (поворот задаёт ring.gd), частицы летят в мировых координатах.
d = Doc()
d.node('Chips', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/fx/chips.gd')})
d.node('Shards', 'CPUParticles2D', '.', {'texture': d.ext('Texture2D', art('fx_chip')), 'emitting': False, 'amount': 9, 'lifetime': 0.8,
       'one_shot': True, 'explosiveness': 1.0, 'local_coords': False, 'emission_shape': 1, 'emission_sphere_radius': 8.0, 'spread': 55.0,
       'gravity': V2(0, 900), 'initial_velocity_min': 150.0, 'initial_velocity_max': 380.0, 'damping_min': 60.0, 'damping_max': 140.0,
       'angle_min': -180.0, 'angle_max': 180.0, 'angular_velocity_min': -720.0, 'angular_velocity_max': 720.0,
       'scale_amount_min': art_scale('fx_chip', 0.25), 'scale_amount_max': art_scale('fx_chip', 0.6),
       'color_ramp': gradient(d, [(0, (1, 1, 1, 1)), (0.7, (1, 1, 1, 0.9)), (1, (1, 1, 1, 0))])})
d.node('Dust', 'CPUParticles2D', '.', {'texture': d.ext('Texture2D', GLOW), 'emitting': False, 'amount': 16, 'lifetime': 0.65, 'one_shot': True,
       'explosiveness': 0.9, 'local_coords': False, 'emission_shape': 1, 'emission_sphere_radius': 10.0, 'spread': 80.0, 'gravity': V2(0, 60),
       'initial_velocity_min': 40.0, 'initial_velocity_max': 150.0, 'damping_min': 120.0, 'damping_max': 220.0,
       'scale_amount_min': 0.12, 'scale_amount_max': 0.3, 'scale_amount_curve': curve(d, [(0, 0.5), (1, 1)]),
       'color_ramp': gradient(d, [(0, (0.95, 0.92, 0.85, 0.55)), (1, (0.95, 0.92, 0.85, 0))])})
d.node('Embers', 'CPUParticles2D', '.', particles(d, emitting=False, amount=10, lifetime=0.45, one_shot=True, explosiveness=1.0, local_coords=False,
       emission_shape=1, emission_sphere_radius=4.0, spread=70.0, gravity=V2(0, 300), initial_velocity_min=120.0, initial_velocity_max=320.0,
       damping_min=150.0, damping_max=300.0, scale_amount_min=0.05, scale_amount_max=0.12, scale_amount_curve=curve(d, [(0, 1), (1, 0)]),
       color_ramp=gradient(d, [(0, (1, 0.85, 0.5, 1)), (0.4, (1, 0.35, 0.1, 0.9)), (1, (0.6, 0.05, 0.05, 0))])))
d.save(P('scenes/fx/chips.tscn'))

# ======================= bolt (2.3) =======================
# Меловой снаряд: голова (два glow-спрайта, вытянуты по ходу полёта) + хвост Line2D (точки ведёт bolt.gd) + крошки мела.
d = Doc()
d.node('Bolt', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/fx/bolt.gd')})
d.node('Trail', 'Line2D', '.', {'material': add_mat(d), 'width': 16.0, 'width_curve': curve(d, [(0, 0), (1, 1)]),
       'gradient': gradient(d, [(0, (1, 1, 1, 0)), (0.6, (1, 1, 1, 0.55)), (1, (1, 1, 1, 1))]), 'joint_mode': 2, 'end_cap_mode': 2}, unique=True)
d.node('Dust', 'CPUParticles2D', '.', particles(d, emitting=False, amount=24, lifetime=0.4, local_coords=False, emission_shape=1,
       emission_sphere_radius=6.0, spread=180.0, gravity=V2(0, 380), initial_velocity_min=20.0, initial_velocity_max=90.0,
       scale_amount_min=0.05, scale_amount_max=0.12, scale_amount_curve=curve(d, [(0, 1), (1, 0)]),
       color_ramp=gradient(d, [(0, (1, 1, 1, 0.9)), (1, (1, 1, 1, 0))])), unique=True)
d.node('Glow', 'Sprite2D', '.', {'material': add_mat(d), 'scale': V2(0.95, 0.5), 'texture': d.ext('Texture2D', GLOW)}, unique=True)
d.node('Core', 'Sprite2D', '.', {'material': add_mat(d), 'scale': V2(0.42, 0.22), 'texture': d.ext('Texture2D', GLOW)}, unique=True)
d.save(P('scenes/fx/bolt.tscn'))

# ======================= coin (2.6) =======================
# Монетка награды: летит в слое HUD из павшей нечисти в счётчик денег (coin.gd). Ореол + искры следом + сама монета.
COIN_S = art_scale('coin', 0.6)
d = Doc()
d.node('Coin', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/fx/coin.gd')})
d.node('Trail', 'CPUParticles2D', '.', particles(d, amount=14, lifetime=0.35, local_coords=False, emission_shape=1, emission_sphere_radius=5.0,
       spread=180.0, gravity=V2(0, 160), initial_velocity_min=10.0, initial_velocity_max=45.0, scale_amount_min=0.05, scale_amount_max=0.12,
       scale_amount_curve=curve(d, [(0, 1), (1, 0)]), color_ramp=gradient(d, [(0, (1, 0.9, 0.55, 0.9)), (1, (1, 0.55, 0.15, 0))])))
d.node('Glow', 'Sprite2D', '.', {'material': add_mat(d), 'modulate': C(1, 0.82, 0.35, 0.5), 'scale': V2(0.5, 0.5), 'texture': d.ext('Texture2D', GLOW)}, unique=True)
d.node('Body', 'Sprite2D', '.', {'texture': d.ext('Texture2D', art('coin')), 'scale': V2(COIN_S, COIN_S)}, unique=True)
d.save(P('scenes/fx/coin.tscn'))

# ======================= candle =======================
d = Doc()
fl = {
 'flicker': animation(d, 'flicker', 1.7, [
    track_value('Glow:scale', [0, 0.4, 0.75, 1.2, 1.7], [V2(2.2, 2.2), V2(2.5, 2.5), V2(2.0, 2.0), V2(2.4, 2.4), V2(2.2, 2.2)]),
    track_value('Flame:scale', [0, 0.3, 0.7, 1.1, 1.7], [V2(0.3, 0.3), V2(0.27, 0.35), V2(0.33, 0.27), V2(0.29, 0.33), V2(0.3, 0.3)]),
    track_value('Glow:self_modulate', [0, 0.5, 0.9, 1.7], [C(1,1,1,1), C(1,1,1,0.7), C(1,1,1,1), C(1,1,1,1)])], loop=True)}
d.node('Candle', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/fx/candle.gd')})
d.node('Glow', 'Sprite2D', '.', {'material': add_mat(d), 'position': V2(0, -50), 'scale': V2(2.2, 2.2), 'modulate': C(1, 0.55, 0.2, 0.45), 'texture': d.ext('Texture2D', GLOW)})
CS = art_scale('candle', 0.55)
d.node('Body', 'Sprite2D', '.', {'texture': d.ext('Texture2D', art('candle')), 'scale': V2(CS, CS)})
d.node('Flame', 'Sprite2D', '.', {'position': V2(0, -48), 'scale': V2(0.3, 0.3), 'texture': d.ext('Texture2D', ART + 'ember.svg')})
anim_player(d, '.', fl, autoplay='flicker')
d.save(P('scenes/fx/candle.tscn'))

# ======================= ring =======================
d = Doc()
d.node('Ring', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/ring/ring.gd')})
d.node('InnerGlow', 'Sprite2D', '.', {'material': add_mat(d), 'modulate': C(0.55, 0.08, 0.1, 0.35), 'scale': V2(4.6, 4.6), 'texture': d.ext('Texture2D', GLOW)})
d.node('Runes', 'Sprite2D', '.', {'modulate': C(1, 0.85, 0.7, 0.2), 'scale': V2(art_scale('ring_ornament', 0.64), art_scale('ring_ornament', 0.64)), 'texture': d.ext('Texture2D', art('ring_ornament'))})
d.node('Chalk', 'ColorRect', '.', rect(-320, -320, 320, 320, {'mouse_filter': 2, 'material': shader_mat(d, 'chalk_ring.gdshader',
       {'noise_tex': d.ext('Texture2D', NOISE), 'radius': 0.769, 'width': 0.03, 'pulse': 0.0}, local=True)}))
d.node('Sections', 'Node2D', '.')
d.node('Pivot', 'Node2D', '.')
d.node('Needle', 'Line2D', 'Pivot', {'points': Raw('PackedVector2Array(30, 0, 222, 0)'), 'width': 3.0, 'default_color': C(1, 0.85, 0.6, 0.22), 'begin_cap_mode': 2, 'end_cap_mode': 2})
d.node('Spark', 'Node2D', 'Pivot', {'position': V2(246, 0)}, unique=True)
shaker(d, 'Pivot/Spark', 'SparkShaker', unique=True)
d.node('Trail', 'CPUParticles2D', 'Pivot/Spark', particles(d, **{'amount': 40, 'lifetime': 0.5, 'local_coords': False, 'emission_shape': 1, 'emission_sphere_radius': 4.0,
       'spread': 180.0, 'gravity': V2(0, -60), 'initial_velocity_min': 10.0, 'initial_velocity_max': 40.0, 'scale_amount_min': 0.1, 'scale_amount_max': 0.22,
       'scale_amount_curve': curve(d, [(0, 1), (1, 0)]),
       'color_ramp': gradient(d, [(0, (1, 0.85, 0.5, 1)), (0.45, (1, 0.35, 0.1, 0.8)), (1, (0.6, 0.05, 0.05, 0))])}), unique=True)
d.node('Glow', 'Sprite2D', 'Pivot/Spark', {'material': add_mat(d), 'modulate': C(1, 0.62, 0.25, 0.9), 'scale': V2(0.85, 0.85), 'texture': d.ext('Texture2D', GLOW)})
d.node('Core', 'Sprite2D', 'Pivot/Spark', {'scale': V2(0.5, 0.5), 'texture': d.ext('Texture2D', ART + 'ember.svg')})
d.node('Hot', 'Sprite2D', 'Pivot/Spark', {'material': add_mat(d), 'modulate': C(1, 1, 0.9, 1), 'scale': V2(0.25, 0.25), 'texture': d.ext('Texture2D', GLOW)})
d.node('Fx', 'Node2D', '.')
d.node('ActionTimer', 'Timer', '.', {'one_shot': True})
d.node('PauseTimer', 'Timer', '.', {'one_shot': True})
d.node('MissBuffer', 'Timer', '.', {'wait_time': 0.12, 'one_shot': True})
d.save(P('scenes/ring/ring.tscn'))

# ======================= pop =======================
d = Doc()
LP = V2(-320, -80)
pa = {
 'RESET': animation(d, 'RESET', 0.001, [track_value('.:scale', [0], [ONE]), track_value('Label:position', [0], [LP]), track_value('Label:modulate', [0], [C(1,1,1,1)])]),
 'pop': animation(d, 'pop', 0.85, [track_value('.:scale', [0, 0.08, 0.16, 0.85], [V2(0.2, 0.2), V2(1.25, 1.25), ONE, V2(0.9, 0.9)]),
                                   track_value('Label:position', [0, 0.85], [LP, V2(-320, -140)], [0.5, 1]),
                                   track_value('Label:modulate', [0, 0.55, 0.85], [C(1,1,1,1), C(1,1,1,1), C(1,1,1,0)])]),
 'pop_big': animation(d, 'pop_big', 1.2, [track_value('.:scale', [0, 0.1, 0.2, 0.3, 1.2], [V2(0.1, 0.1), V2(1.6, 1.6), V2(0.95, 0.95), V2(1.05, 1.05), ONE]),
                                          track_value('Label:position', [0, 1.2], [LP, V2(-320, -120)], [0.5, 1]),
                                          track_value('Label:modulate', [0, 0.85, 1.2], [C(1,1,1,1), C(1,1,1,1), C(1,1,1,0)])]),
}
d.node('Pop', 'Node2D', None, {'z_index': 10, 'script': d.ext('Script', 'res://scenes/fx/pop.gd')})
d.node('Label', 'Label', '.', label(d, 'ls_pop', rect(-320, -80, 320, 80, {'pivot_offset': V2(320, 80)}), dynamic=True), unique=True)
anim_player(d, '.', pa)
d.save(P('scenes/fx/pop.tscn'))

# ======================= wipe =======================
d = Doc()
wa = {
 'RESET': animation(d, 'RESET', 0.001, [track_value('.:progress', [0], [0.0])]),
 'cover': animation(d, 'cover', 0.42, [track_value('.:progress', [0, 0.42], [0.0, 1.0], [2.0, 1])]),
 'reveal': animation(d, 'reveal', 1.45, [track_value('Title:modulate', [0, 0.12, 0.8, 1.0], [C(1,1,1,0), C(1,1,1,1), C(1,1,1,1), C(1,1,1,0)]),
                                         track_value('Title:scale', [0, 0.18, 1.0], [V2(1.5, 1.5), ONE, V2(0.94, 0.94)], [0.4, 1, 1]),
                                         track_value('.:progress', [0, 0.85, 1.45], [1.0, 1.0, 2.0], [1, 0.5, 1])]),
}
d.node('Wipe', 'CanvasLayer', None, {'layer': 9, 'script': d.ext('Script', 'res://scenes/fx/wipe.gd')})
d.node('Rect', 'ColorRect', '.', full_rect({'visible': False, 'material': shader_mat(d, 'wipe.gdshader', {'noise_tex': d.ext('Texture2D', NOISE), 'progress': 0.0})}))
d.node('Title', 'Label', '.', label(d, 'ls_wipe', full_rect({'modulate': C(1, 1, 1, 0), 'mouse_filter': 2, 'autowrap_mode': 3,
       'material': shader_mat(d, 'title.gdshader', {'jitter': 1.6})}), dynamic=True), unique=True)
anim_player(d, '.', wa)
d.save(P('scenes/fx/wipe.tscn'))

# ======================= background =======================
d = Doc()
d.node('Background', 'CanvasLayer', None, {'layer': -10, 'script': d.ext('Script', 'res://scenes/bg/background.gd')})
d.node('Sky', 'TextureRect', '.', full_rect({'mouse_filter': 2, 'texture': d.ext('Texture2D', art('bg_fight')), 'expand_mode': 1, 'stretch_mode': 6}))
d.node('Fog', 'ColorRect', '.', full_rect({'mouse_filter': 2, 'material': shader_mat(d, 'fog.gdshader',
       {'noise_tex': d.ext('Texture2D', NOISE), 'fog_color': C(0.55, 0.66, 0.62, 1), 'density': 0.42, 'speed': 0.015})}))
d.node('Tint', 'ColorRect', '.', full_rect({'mouse_filter': 2, 'color': C(0.02, 0.05, 0.08, 0.15)}))
d.save(P('scenes/bg/background.tscn'))

# ======================= hud =======================
d = Doc()
d.node('Hud', 'CanvasLayer', None, {'layer': 5, 'script': d.ext('Script', 'res://scenes/hud/hud.gd')})
d.node('Root', 'Control', '.', full_rect({'mouse_filter': 2}))
d.node('Vitals', 'Control', 'Root', full_rect({'mouse_filter': 2}), unique=True)
d.node('TopBar', 'HBoxContainer', 'Root/Vitals', {'anchors_preset': 10, 'anchor_right': 1.0, 'offset_left': 22.0, 'offset_top': 16.0, 'offset_right': -22.0,
       'offset_bottom': 80.0, 'grow_horizontal': 2, 'mouse_filter': 2, 'theme_override_constants/separation': 10})
def icon(name, tex, size=54, unique=False):
    d.node(name, 'TextureRect', 'Root/Vitals/TopBar', {'custom_minimum_size': V2(size, size), 'mouse_filter': 2, 'texture': d.ext('Texture2D', art(tex)),
           'expand_mode': 1, 'stretch_mode': 5}, unique=unique)
def hud_label(name, text, minw):
    d.node(name, 'Label', 'Root/Vitals/TopBar', label(d, 'ls_hud', {'custom_minimum_size': V2(minw, 0), 'text': text, 'horizontal_alignment': 0}, dynamic=True), unique=True)
icon('Heart', 'heart', unique=True); hud_label('HealthLabel', '3.0', 76)
icon('JarIcon', 'jar_hud', 50); hud_label('JarsLabel', '2', 40)
d.node('Spacer', 'Control', 'Root/Vitals/TopBar', {'mouse_filter': 2, 'size_flags_horizontal': 3})
icon('CoinIcon', 'coin', 48, unique=True); hud_label('CashLabel', '0', 90)
d.node('NightLabel', 'Label', 'Root/Vitals', label(d, 'ls_hud_small', {'anchors_preset': 5, 'anchor_left': 0.5, 'anchor_right': 0.5, 'offset_left': -200.0,
       'offset_top': 84.0, 'offset_right': 200.0, 'offset_bottom': 120.0, 'grow_horizontal': 2}, dynamic=True), unique=True)
d.node('SoundButton', 'Button', 'Root', {'anchors_preset': 2, 'anchor_top': 1.0, 'anchor_bottom': 1.0, 'offset_left': 12.0, 'offset_top': -58.0, 'offset_right': 232.0,
       'offset_bottom': -10.0, 'grow_vertical': 0, 'focus_mode': 0, 'theme_override_colors/font_color': C(0.85, 0.82, 0.76, 0.7),
       'theme_override_font_sizes/font_size': 22, 'text': 'HUD_SOUND_ON', 'flat': True, 'alignment': 0, 'auto_translate_mode': 2}, unique=True)
# Монетки награды (2.6) летят поверх панели — узел последним.
d.node('Coins', 'Node2D', '.', unique=True)
d.conn('pressed', 'Root/SoundButton', '.', '_on_sound_button_pressed')
d.save(P('scenes/hud/hud.tscn'))

# ======================= enemy =======================
d = Doc()
SQ = 'Body/Squash'
ea = {
 'RESET': animation(d, 'RESET', 0.001, [track_value('.:flash', [0], [0.0]), track_value('.:dissolve', [0], [0.0]), track_value('.:swirl', [0], [0.0]),
     track_value('.:eye_glow', [0], [1.4]), track_value(SQ + ':scale', [0], [ONE]), track_value(SQ + ':position', [0], [V2(0, 0)]),
     track_value(SQ + ':rotation', [0], [0.0]), track_value('Aura:self_modulate', [0], [C(1,1,1,1)]), track_value('Shadow:self_modulate', [0], [C(1,1,1,1)]),
     track_value('.:eye_flash', [0], [0.0])]),
 'appear': animation(d, 'appear', 0.8, [track_value('.:dissolve', [0, 0.7], [1.0, 0.0], [0.5, 1]), track_value('.:flash', [0, 0.4], [0.8, 0.0]),
     track_value(SQ + ':scale', [0, 0.35, 0.6], [V2(0.6, 1.5), V2(1.12, 0.9), ONE]), track_value(SQ + ':position', [0, 0.4], [V2(0, 80), V2(0, 0)], [0.4, 1]),
     track_value('Aura:self_modulate', [0, 0.6], [C(1,1,1,0), C(1,1,1,1)]), track_value('Shadow:self_modulate', [0, 0.6], [C(1,1,1,0), C(1,1,1,1)])]),
 # Поза «в покое» держится и дорожками положения/наклона/глаз: calm() плавно (blend) возвращает сюда из замаха.
 'idle': animation(d, 'idle', 2.4, [track_value(SQ + ':scale', [0, 1.2, 2.4], [ONE, V2(1.025, 0.975), ONE]),
     track_value('Aura:self_modulate', [0, 1.2, 2.4], [C(1,1,1,0.8), C(1,1,1,1), C(1,1,1,0.8)]),
     track_value(SQ + ':position', [0], [V2(0, 0)]), track_value(SQ + ':rotation', [0], [0.0]),
     track_value('.:eye_glow', [0], [1.4]), track_value('.:eye_flash', [0], [0.0])], loop=True),
 # Удар может прервать замах — поэтому и тут сбрасываем положение, свечение ауры и блики (глаза жмурятся).
 'hurt': animation(d, 'hurt', 0.32, [track_value('.:flash', [0, 0.25], [1.0, 0.0]), track_value(SQ + ':scale', [0, 0.12, 0.32], [V2(0.82, 1.18), V2(1.08, 0.94), ONE]),
     track_value(SQ + ':rotation', [0, 0.12, 0.32], [0.09, -0.04, 0.0]), track_value(SQ + ':position', [0, 0.32], [V2(0, 10), V2(0, 0)]),
     track_value('.:eye_glow', [0, 0.1, 0.32], [0.6, 0.6, 1.4]), track_value('.:eye_flash', [0], [0.0]),
     track_value('Aura:self_modulate', [0, 0.32], [C(1,1,1,1), C(1,1,1,0.9)])]),
 'attack': animation(d, 'attack', 0.5, [track_value(SQ + ':scale', [0, 0.12, 0.22, 0.5], [ONE, V2(0.9, 1.1), V2(1.3, 1.25), ONE]),
     track_value(SQ + ':position', [0, 0.12, 0.22, 0.5], [V2(0, 0), V2(0, -20), V2(0, 40), V2(0, 0)]), track_value('.:eye_glow', [0, 0.22, 0.5], [1.4, 4.0, 1.4]),
     track_value(SQ + ':rotation', [0, 0.22, 0.5], [0.0, 0.03, 0.0]), track_value('.:eye_flash', [0, 0.22, 0.5], [0.0, 0.5, 0.0]),
     track_value('Aura:self_modulate', [0, 0.22, 0.5], [C(1,1,1,1), C(1.5,1.5,1.5,1), C(1,1,1,1)])]),
 # Замах (2.4): длина = Enemy.WINDUP_LEN, скорость подгоняет windup(). Отклоняется назад и вверх, тянется,
 # глаза разгораются и в конце вспыхивают бликами; поза держится до cast()/calm().
 'windup': animation(d, 'windup', 0.5, [track_value(SQ + ':scale', [0, 0.3, 0.5], [ONE, V2(0.93, 1.09), V2(0.91, 1.12)], [0.5, 1, 1]),
     track_value(SQ + ':position', [0, 0.3, 0.5], [V2(0, 0), V2(0, -22), V2(0, -28)], [0.5, 1, 1]),
     track_value(SQ + ':rotation', [0, 0.3, 0.5], [0.0, -0.06, -0.07], [0.5, 1, 1]),
     track_value('.:eye_glow', [0, 0.35, 0.5], [1.4, 2.6, 4.5]), track_value('.:eye_flash', [0, 0.28, 0.4, 0.5], [0.0, 0.15, 1.0, 0.75]),
     track_value('Aura:self_modulate', [0, 0.5], [C(1,1,1,1), C(1.7,1.6,1.6,1)])]),
 # Атака сорвалась на круг: рывок вперёд из позы замаха, блики гаснут.
 'cast': animation(d, 'cast', 0.4, [track_value(SQ + ':scale', [0, 0.07, 0.4], [V2(0.91, 1.12), V2(1.22, 0.88), ONE], [1, 0.5, 1]),
     track_value(SQ + ':position', [0, 0.07, 0.4], [V2(0, -28), V2(0, 36), V2(0, 0)], [1, 0.5, 1]),
     track_value(SQ + ':rotation', [0, 0.07, 0.4], [-0.07, 0.03, 0.0]),
     track_value('.:eye_glow', [0, 0.07, 0.4], [4.5, 5.0, 1.4]), track_value('.:eye_flash', [0, 0.07, 0.4], [0.75, 1.0, 0.0]),
     track_value('Aura:self_modulate', [0, 0.4], [C(1.7,1.6,1.6,1), C(1,1,1,1)])]),
 'die': animation(d, 'die', 1.0, [track_value('.:flash', [0, 0.2], [1.0, 0.2]), track_value('.:dissolve', [0.1, 1.0], [0.0, 1.0]),
     track_value('.:eye_flash', [0, 0.15], [1.0, 0.0]), track_value('.:eye_glow', [0, 0.5], [3.0, 0.0]),
     track_value(SQ + ':scale', [0, 0.15, 1.0], [ONE, V2(1.15, 0.9), V2(1.05, 1.1)]), track_value('Aura:self_modulate', [0, 0.9], [C(1,1,1,1), C(1,1,1,0)]),
     track_value('Shadow:self_modulate', [0, 0.9], [C(1,1,1,1), C(1,1,1,0)])]),
 'seal': animation(d, 'seal', 1.0, [track_value('.:swirl', [0, 0.9], [0.0, 1.0]), track_value('.:flash', [0, 0.9], [0.0, 0.7]),
     track_value(SQ + ':scale', [0, 0.2, 0.95], [ONE, V2(1.1, 1.1), V2(0.05, 0.05)], [1, 2.0, 1]),
     track_value(SQ + ':position', [0, 0.2, 0.95], [V2(0, 0), V2(0, -30), V2(0, 510)], [1, 2.0, 1]),
     track_value('Aura:self_modulate', [0, 0.8], [C(1,1,1,1), C(1,1,1,0)]), track_value('Shadow:self_modulate', [0, 0.6], [C(1,1,1,1), C(1,1,1,0)]),
     track_value(SQ + ':rotation', [0, 0.2], [0.0, 0.0]), track_value('.:eye_flash', [0, 0.2], [0.6, 0.0])]),
}
d.node('Enemy', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/enemy/enemy.gd')})
d.node('Shadow', 'Sprite2D', '.', {'modulate': C(0, 0, 0, 0.65), 'position': V2(0, 205), 'scale': V2(3.4, 0.7), 'texture': d.ext('Texture2D', GLOW)})
d.node('Aura', 'Sprite2D', '.', {'material': add_mat(d), 'scale': V2(5.5, 5.5), 'texture': d.ext('Texture2D', GLOW)}, unique=True)
d.node('Body', 'Node2D', '.')
shaker(d, 'Body', 'BodyShaker', unique=True, float_amount=6.0, float_x=3.0)
d.node('Squash', 'Node2D', 'Body')
d.node('Sprite', 'Sprite2D', 'Body/Squash', {'material': shader_mat(d, 'creature.gdshader', {'noise_tex': d.ext('Texture2D', NOISE), 'flash': 0.0,
       'dissolve': 0.0, 'swirl': 0.0, 'eye_glow': 1.4}, local=True)}, unique=True)
fade = gradient(d, [(0, (1, 1, 1, 1)), (0.7, (1, 1, 1, 0.7)), (1, (1, 1, 1, 0))])
shrink = curve(d, [(0, 1), (1, 0)])
d.node('HitBurst', 'CPUParticles2D', '.', particles(d, emitting=False, amount=26, lifetime=0.6, one_shot=True, explosiveness=1.0, emission_shape=1,
       emission_sphere_radius=60.0, spread=180.0, gravity=V2(0, 600), initial_velocity_min=200.0, initial_velocity_max=520.0, damping_min=300.0,
       damping_max=500.0, scale_amount_min=0.1, scale_amount_max=0.25, scale_amount_curve=shrink, color_ramp=fade), unique=True)
d.node('DeathBurst', 'CPUParticles2D', '.', particles(d, emitting=False, amount=70, lifetime=1.3, one_shot=True, explosiveness=0.85, emission_shape=1,
       emission_sphere_radius=140.0, direction=V2(0, -1), spread=60.0, gravity=V2(0, -260), initial_velocity_min=60.0, initial_velocity_max=240.0,
       scale_amount_min=0.08, scale_amount_max=0.22, scale_amount_curve=shrink, color_ramp=fade), unique=True)
d.node('SealBurst', 'CPUParticles2D', '.', particles(d, emitting=False, amount=60, lifetime=0.9, one_shot=True, explosiveness=0.6, emission_shape=2,
       emission_sphere_radius=220.0, gravity=V2(0, 0), radial_accel_min=-900.0, radial_accel_max=-600.0, scale_amount_min=0.1, scale_amount_max=0.2,
       scale_amount_curve=shrink, color=C(1, 0.82, 0.35, 1), color_ramp=fade), unique=True)
anim_player(d, '.', ea)
d.save(P('scenes/enemy/enemy.tscn'))

# ======================= hp_bar (2.7) =======================
# Дуга здоровья нечисти вокруг числа: след («призрак», светлый мел) под красной дугой, крошки с её концов.
# Обе дуги — arc.gdshader от верха круга (center −π/2); arc_size ведёт hp_bar.gd. Крошки летят в мировых координатах,
# узел смотрит +X вдоль срезанного куска (поворот задаёт hp_bar.gd).
d = Doc()
noise = d.ext('Texture2D', NOISE)
d.node('HpBar', 'Control', None, rect(-150, -150, 150, 150, {'mouse_filter': 2, 'script': d.ext('Script', 'res://scenes/fight/hp_bar.gd')}))
d.node('Ghost', 'ColorRect', '.', full_rect({'mouse_filter': 2, 'material': shader_mat(d, 'arc.gdshader', {'center': -1.5708,
       'arc_size': 6.2832, 'grow': 1.0, 'r_in': 0.86, 'r_out': 0.96, 'color': HEX('#f3e6cc'), 'glow_color': HEX('#fff3d6'), 'alpha': 0.85, 'glow_amount': 0.3,
       'noise_tex': noise}, local=True)}))
d.node('Arc', 'ColorRect', '.', full_rect({'mouse_filter': 2, 'material': shader_mat(d, 'arc.gdshader', {'center': -1.5708,
       'arc_size': 6.2832, 'grow': 1.0, 'r_in': 0.86, 'r_out': 0.96, 'color': HEX('#e0283c'), 'glow_color': HEX('#ff6a5a'), 'hot': 0.3,
       'noise_tex': noise}, local=True)}))
for name in ('CrumbsLeft', 'CrumbsRight'):
    d.node(name, 'CPUParticles2D', '.', {'texture': d.ext('Texture2D', art('fx_chip')), 'emitting': False, 'amount': 6, 'lifetime': 0.6,
           'one_shot': True, 'explosiveness': 1.0, 'local_coords': False, 'emission_shape': 1, 'emission_sphere_radius': 6.0, 'spread': 30.0,
           'gravity': V2(0, 700), 'initial_velocity_min': 60.0, 'initial_velocity_max': 170.0, 'damping_min': 40.0, 'damping_max': 90.0,
           'angle_min': -180.0, 'angle_max': 180.0, 'angular_velocity_min': -540.0, 'angular_velocity_max': 540.0,
           'scale_amount_min': art_scale('fx_chip', 0.15), 'scale_amount_max': art_scale('fx_chip', 0.35),
           'color_ramp': gradient(d, [(0, (1, 0.8, 0.75, 1)), (0.35, (0.88, 0.16, 0.24, 0.95)), (1, (0.5, 0.05, 0.1, 0))])})
d.save(P('scenes/fight/hp_bar.tscn'))

# ======================= fight =======================
d = Doc()
d.node('Fight', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/fight/fight.gd')})
candles(d)
d.node('EnemySlot', 'Node2D', '.', {'position': V2(0, -300), 'metadata/layout': 'top'})
d.node('Ring', None, '.', {'position': V2(0, RING_Y), 'scaling_rps': True, 'telegraph': True, 'wounds': True},
       instance=d.ext('PackedScene', 'res://scenes/ring/ring.tscn'))
d.node('Center', 'Node2D', '.', {'position': V2(0, RING_Y)})
noise = d.ext('Texture2D', NOISE)
# Дуга здоровья с «призраком» (2.7) — своя сцена: красная дуга, светлый след под ней, крошки с концов.
d.node('HpBar', None, 'Center', {}, instance=d.ext('PackedScene', 'res://scenes/fight/hp_bar.tscn'), unique=True)
d.node('SealMark', 'ColorRect', 'Center', rect(-150, -150, 150, 150, {'mouse_filter': 2, 'material': shader_mat(d, 'arc.gdshader', {'center': -1.5708,
       'arc_size': 1.885, 'grow': 1.0, 'r_in': 0.975, 'r_out': 1.0, 'color': HEX('#ffd25a'), 'glow_color': HEX('#fff1b0'), 'alpha': 0.9, 'noise_tex': noise}, local=True)}), unique=True)
d.node('NameLabel', 'Label', 'Center', label(d, 'ls_center_name', rect(-200, -100, 200, -60), dynamic=True), unique=True)
d.node('HpLabel', 'Label', 'Center', label(d, 'ls_center_hp', rect(-150, -60, 150, 50), dynamic=True), unique=True)
# Комбо (2.1): счётчик под числом здоровья и бонус урона под ним — внутри дуги здоровья (внутренний радиус ≈129).
d.node('ComboLabel', 'Label', 'Center', label(d, 'ls_combo', rect(-130, 44, 130, 88), dynamic=True), unique=True)
d.node('ComboBonus', 'Label', 'Center', label(d, 'ls_combo_small', rect(-90, 84, 90, 110), dynamic=True), unique=True)
# Снаряды ударов (2.3): летят в мировых координатах, поэтому раскладке (Layout) безразлично, куда сдвинут узел.
d.node('Bolts', 'Node2D', '.')
d.node('Pops', 'Node2D', '.', {'position': V2(0, RING_Y)})
d.node('Hint', 'Label', '.', label(d, 'ls_small', rect(-350, 560, 350, 630, {'text': 'HINT_TAP', 'autowrap_mode': 3})), unique=True)
d.node('BlindTimer', 'Timer', '.', {'one_shot': True})
d.node('HeartbeatTimer', 'Timer', '.', {'wait_time': 0.85, 'autostart': True})
d.conn('pressed', 'Ring', '.', '_on_ring_pressed')
d.conn('expired', 'Ring', '.', '_on_ring_expired')
d.conn('missed', 'Ring', '.', '_on_ring_missed')
d.conn('telegraph_started', 'Ring', '.', '_on_ring_telegraph_started')
d.conn('telegraph_armed', 'Ring', '.', '_on_ring_telegraph_armed')
d.conn('telegraph_cancelled', 'Ring', '.', '_on_ring_telegraph_cancelled')
d.conn('timeout', 'BlindTimer', '.', '_on_blind_timer_timeout')
d.conn('timeout', 'HeartbeatTimer', '.', '_on_heartbeat_timer_timeout')
d.save(P('scenes/fight/fight.tscn'))

# ======================= shop =======================
d = Doc()
A_SCRIPT = 'res://scripts/data/action_data.gd'
_dk = art_ratio('domovoy_idle', 0.95)  # PNG Домового может быть другого размера, чем SVG
def DV(x, y): return V2(round(x * _dk, 4), round(y * _dk, 4))
sa = {
 'RESET': animation(d, 'RESET', 0.001, [track_value('Sprite:scale', [0], [DV(0.95, 0.95)]), track_value('Sprite:rotation', [0], [0.0])]),
 'idle': animation(d, 'idle', 2.6, [track_value('Sprite:scale', [0, 1.3, 2.6], [DV(0.95, 0.95), DV(0.97, 0.93), DV(0.95, 0.95)])], loop=True),
 'smile': animation(d, 'smile', 0.45, [track_value('Sprite:scale', [0, 0.1, 0.25, 0.45], [DV(0.95, 0.95), DV(1.1, 0.82), DV(0.9, 1.05), DV(0.95, 0.95)]),
                                       track_value('Sprite:rotation', [0, 0.1, 0.25, 0.45], [0.0, -0.08, 0.05, 0.0])]),
}
d.node('Shop', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/shop/shop.gd')})
candles(d)
d.node('Domovoy', 'Node2D', '.', {'position': V2(0, -320), 'metadata/layout': 'top'})
d.node('Glow', 'Sprite2D', 'Domovoy', {'material': add_mat(d), 'modulate': C(1, 0.6, 0.25, 0.35), 'scale': V2(4.5, 4.5), 'texture': d.ext('Texture2D', GLOW)})
d.node('Sprite', 'Sprite2D', 'Domovoy', {'scale': DV(0.95, 0.95), 'texture': d.ext('Texture2D', art('domovoy_idle'))})
shaker(d, 'Domovoy', float_amount=5.0)
anim_player(d, 'Domovoy', sa)
d.node('Greeting', 'Label', '.', label(d, 'ls_small', rect(-340, -112, 340, -72, {'text': 'SHOP_GREETING', 'metadata/layout': 'top'})))
d.node('Ring', None, '.', {'position': V2(0, RING_Y), 'wounds': True, 'ui': typed_array(d, A_SCRIPT, [d.ext('Resource', 'res://data/actions/ui/done.tres')])},
       instance=d.ext('PackedScene', 'res://scenes/ring/ring.tscn'))
d.node('Card', 'Control', '.', rect(-160, RING_Y - 130, 160, RING_Y + 130, {'pivot_offset': V2(160, 130), 'mouse_filter': 2}), unique=True)
shaker(d, 'Card', 'CardShaker', unique=True)
d.node('ItemContents', 'VBoxContainer', 'Card', full_rect({'mouse_filter': 2, 'alignment': 1, 'theme_override_constants/separation': 2}), unique=True)
d.node('ItemIcon', 'TextureRect', 'Card/ItemContents', {'custom_minimum_size': V2(0, 76), 'mouse_filter': 2, 'expand_mode': 1, 'stretch_mode': 5}, unique=True)
d.node('ItemType', 'Label', 'Card/ItemContents', label(d, 'ls_small', dynamic=True), unique=True)
d.node('ItemTitle', 'Label', 'Card/ItemContents', label(d, 'ls_card_title', {'autowrap_mode': 3}, dynamic=True), unique=True)
d.node('ItemInfo', 'Label', 'Card/ItemContents', label(d, 'ls_body', {'autowrap_mode': 3}, dynamic=True), unique=True)
d.node('SoldOut', 'Label', 'Card', label(d, 'ls_pop_small', full_rect({'modulate': C(1, 0.35, 0.35, 1), 'mouse_filter': 2, 'text': 'SHOP_SOLD_OUT',
       'vertical_alignment': 2})), unique=True)
d.node('Pops', 'Node2D', '.', {'position': V2(0, RING_Y)})
d.conn('pressed', 'Ring', '.', '_on_ring_pressed')
d.save(P('scenes/shop/shop.tscn'))

# ======================= menu =======================
d = Doc()
d.node('Menu', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/menu/menu.gd')})
candles(d)
d.node('Title', 'Label', '.', label(d, 'ls_title', rect(-360, -610, 360, -370, {'metadata/layout': 'top', 'text': 'MENU_TITLE', 'material': shader_mat(d, 'title.gdshader', {'jitter': 1.6})})))
d.node('Subtitle', 'Label', '.', label(d, 'ls_body', rect(-340, -370, 340, -325, {'metadata/layout': 'top', 'text': 'MENU_SUB', 'modulate': C(1, 1, 1, 0.75)})))
d.node('Ring', None, '.', {'position': V2(0, RING_Y)}, instance=d.ext('PackedScene', 'res://scenes/ring/ring.tscn'))
d.node('Reader', 'Node2D', '.', {'position': V2(0, RING_Y - 10)}, unique=True)
d.node('Glow', 'Sprite2D', 'Reader', {'material': add_mat(d), 'modulate': C(1, 0.55, 0.2, 0.4), 'scale': V2(3.6, 3.6), 'texture': d.ext('Texture2D', GLOW)})
RS = art_scale('reader_idle', 1.2)
d.node('Sprite', 'Sprite2D', 'Reader', {'scale': V2(RS, RS), 'texture': d.ext('Texture2D', art('reader_idle'))})
shaker(d, 'Reader', float_amount=6.0)
d.node('Bestiary', 'Control', '.', rect(-170, RING_Y - 150, 170, RING_Y + 150, {'mouse_filter': 2}), unique=True)
d.node('CaughtLabel', 'Label', 'Bestiary', label(d, 'ls_small', rect(0, 0, 340, 34), dynamic=True), unique=True)
d.node('Slots', 'GridContainer', 'Bestiary', rect(0, 38, 340, 300, {'mouse_filter': 2, 'columns': 3, 'theme_override_constants/h_separation': 6,
       'theme_override_constants/v_separation': 4}), unique=True)
for nid in ['moshkara', 'svecheed', 'sheptuha', 'motanka', 'podpolnik']:
    d.node(nid, 'VBoxContainer', 'Bestiary/Slots', {'mouse_filter': 2, 'size_flags_horizontal': 3})
    d.node('Icon', 'TextureRect', f'Bestiary/Slots/{nid}', {'custom_minimum_size': V2(96, 86), 'mouse_filter': 2, 'texture': d.ext('Texture2D', art(f'{nid}_jar')),
           'expand_mode': 1, 'stretch_mode': 5})
    d.node('Name', 'Label', f'Bestiary/Slots/{nid}', label(d, 'ls_small', {'theme_override_font_sizes/font_size': 18}, dynamic=True))
d.node('BestLabel', 'Label', '.', label(d, 'ls_body', rect(-340, 572, 340, 620), dynamic=True), unique=True)
d.conn('pressed', 'Ring', '.', '_on_ring_pressed')
d.save(P('scenes/menu/menu.tscn'))

# ======================= end =======================
d = Doc()
d.node('End', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/end/end.gd')})
candles(d, dim=0.6)
d.node('Title', 'Label', '.', label(d, 'ls_title', rect(-360, -580, 360, -430, {'metadata/layout': 'top', 'material': shader_mat(d, 'title.gdshader', {'jitter': 2.2})}), dynamic=True), unique=True)
d.node('Subtitle', 'Label', '.', label(d, 'ls_body', rect(-340, -430, 340, -340, {'autowrap_mode': 3, 'metadata/layout': 'top'}), dynamic=True), unique=True)
d.node('Ring', None, '.', {'position': V2(0, RING_Y)}, instance=d.ext('PackedScene', 'res://scenes/ring/ring.tscn'))
d.node('Stats', 'Label', '.', label(d, 'ls_body', rect(-190, RING_Y - 140, 190, RING_Y + 140), dynamic=True), unique=True)
d.conn('pressed', 'Ring', '.', '_on_ring_pressed')
d.save(P('scenes/end/end.tscn'))

# ======================= main =======================
d = Doc()
d.node('Main', 'Node2D', None, {'script': d.ext('Script', 'res://scenes/main/main.gd')})
d.node('Background', None, '.', instance=d.ext('PackedScene', 'res://scenes/bg/background.tscn'))
d.node('World', 'Node2D', '.')
d.node('Camera2D', 'Camera2D', 'World')
shaker(d, 'World/Camera2D')
d.node('Embers', 'CPUParticles2D', 'World', particles(d, amount=36, lifetime=7.0, preprocess=7.0, position=V2(0, 700), emission_shape=3,
       emission_rect_extents=V2(1000, 120), direction=V2(0, -1), spread=25.0, gravity=V2(0, 0), initial_velocity_min=40.0, initial_velocity_max=110.0,
       scale_amount_min=0.05, scale_amount_max=0.14, scale_amount_curve=curve(d, [(0, 0), (0.15, 1), (1, 0)]),
       color_ramp=gradient(d, [(0, (1, 0.6, 0.25, 0)), (0.2, (1, 0.55, 0.2, 0.8)), (1, (0.8, 0.1, 0.05, 0))])))
d.node('Scenes', 'Node2D', 'World')
d.node('Hud', None, '.', instance=d.ext('PackedScene', 'res://scenes/hud/hud.tscn'))
d.node('Wipe', None, '.', instance=d.ext('PackedScene', 'res://scenes/fx/wipe.tscn'))
d.node('Post', 'CanvasLayer', '.', {'layer': 10})
d.node('Rect', 'ColorRect', 'Post', full_rect({'mouse_filter': 2, 'material': shader_mat(d, 'post.gdshader', {'noise_tex': d.ext('Texture2D', NOISE)})}))
d.save(P('scenes/main/main.tscn'))
print('scenes ok')
