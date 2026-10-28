"""Мини-библиотека для записи .tscn/.tres (Godot 4, format=3). Используется build_*.py.
Сцены после генерации — обычные .tscn: открываются и правятся в редакторе Godot."""
import os

def fmt(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int,)): return str(v)
    if isinstance(v, float):
        s = repr(round(v, 6))
        return s
    if isinstance(v, Raw): return v.s
    if isinstance(v, str): return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, (list, tuple)): return '[' + ', '.join(fmt(x) for x in v) + ']'
    raise TypeError(v)

class Raw:
    def __init__(self, s): self.s = s
    def __repr__(self): return self.s

def V2(x, y): return Raw(f'Vector2({fmt(float(x))}, {fmt(float(y))})')
def C(r, g, b, a=1.0): return Raw(f'Color({fmt(float(r))}, {fmt(float(g))}, {fmt(float(b))}, {fmt(float(a))})')
def HEX(h, a=1.0):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16)/255 for i in (0, 2, 4))
    return C(round(r, 4), round(g, 4), round(b, 4), a)
def SN(s): return Raw(f'&"{s}"')
def NP(s): return Raw(f'NodePath("{s}")')
def PF(*xs): return Raw('PackedFloat32Array(' + ', '.join(fmt(float(x)) for x in xs) + ')')

class Doc:
    def __init__(self, kind='scene', res_type='Resource', script_class=None):
        self.kind = kind; self.res_type = res_type; self.script_class = script_class
        self.exts = []; self.ext_ids = {}; self.subs = []; self.nodes = []; self.conns = []
        self.res_props = None; self._n = 0
    def ext(self, typ, path):
        key = (typ, path)
        if key not in self.ext_ids:
            i = str(len(self.exts) + 1); self.ext_ids[key] = i; self.exts.append((typ, path, i))
        return Raw(f'ExtResource("{self.ext_ids[key]}")')
    def sub(self, typ, props, hint='r'):
        self._n += 1; i = f'{typ}_{hint}{self._n}'
        self.subs.append((typ, i, props)); return Raw(f'SubResource("{i}")')
    def node(self, name, typ=None, parent=None, props=None, instance=None, unique=False):
        self.nodes.append(dict(name=name, typ=typ, parent=parent, props=props or {}, instance=instance, unique=unique))
        return name
    def conn(self, signal, frm, to, method):
        self.conns.append((signal, frm, to, method))
    def text(self):
        out = []
        if self.kind == 'scene':
            out.append('[gd_scene format=3]\n')
        else:
            sc = f' script_class="{self.script_class}"' if self.script_class else ''
            out.append(f'[gd_resource type="{self.res_type}"{sc} format=3]\n')
        for typ, path, i in self.exts:
            out.append(f'[ext_resource type="{typ}" path="{path}" id="{i}"]')
        if self.exts: out.append('')
        for typ, i, props in self.subs:
            out.append(f'[sub_resource type="{typ}" id="{i}"]')
            for k, v in props.items(): out.append(f'{k} = {fmt(v)}')
            out.append('')
        if self.kind == 'scene':
            for n in self.nodes:
                head = f'[node name="{n["name"]}"'
                if n['typ'] and not n['instance']: head += f' type="{n["typ"]}"'
                if n['parent'] is not None: head += f' parent="{n["parent"]}"'
                if n['instance']: head += f' instance={n["instance"].s}'
                out.append(head + ']')
                if n['unique']: out.append('unique_name_in_owner = true')
                for k, v in n['props'].items(): out.append(f'{k} = {fmt(v)}')
                out.append('')
            for s, f, t, m in self.conns:
                out.append(f'[connection signal="{s}" from="{f}" to="{t}" method="{m}"]')
            if self.conns: out.append('')
        else:
            out.append('[resource]')
            for k, v in (self.res_props or {}).items(): out.append(f'{k} = {fmt(v)}')
            out.append('')
        return '\n'.join(out)
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(self.text())

# ---------- анимации ----------
def track_value(path, times, values, trans=None, update=0, interp=1):
    return dict(type='value', path=path, times=times, values=values, trans=trans or [1.0]*len(times), update=update, interp=interp)
def track_method(path, times, calls):
    return dict(type='method', path=path, times=times, calls=calls)

def animation(doc, name, length, tracks, loop=False):
    p = {'resource_name': name, 'length': float(length)}
    if loop: p['loop_mode'] = 1
    for i, t in enumerate(tracks):
        b = f'tracks/{i}/'
        p[b+'type'] = t['type']; p[b+'imported'] = False; p[b+'enabled'] = True
        p[b+'path'] = NP(t['path']); p[b+'interp'] = t.get('interp', 1); p[b+'loop_wrap'] = True
        if t['type'] == 'value':
            vals = ', '.join(fmt(v) for v in t['values'])
            p[b+'keys'] = Raw('{\n"times": ' + PF(*t['times']).s + ',\n"transitions": ' + PF(*t['trans']).s +
                              f',\n"update": {t["update"]},\n"values": [{vals}]\n}}')
        else:
            calls = ', '.join('{\n"args": [' + ', '.join(fmt(a) for a in args) + f'],\n"method": &"{m}"\n}}' for m, args in t['calls'])
            p[b+'keys'] = Raw('{\n"times": ' + PF(*t['times']).s + ',\n"transitions": ' + PF(*([1.0]*len(t['times']))).s + f',\n"values": [{calls}]\n}}')
    return doc.sub('Animation', p, hint=name.replace(' ', '_') + '_')

def anim_player(doc, parent, anims, autoplay=None, name='AnimationPlayer'):
    """anims: dict name -> SubResource"""
    lib = doc.sub('AnimationLibrary', {'_data': Raw('{\n' + ',\n'.join(f'&"{k}": {v.s}' for k, v in anims.items()) + '\n}')}, hint='lib')
    props = {'libraries': Raw('{\n&"": ' + lib.s + '\n}')}
    if autoplay: props['autoplay'] = SN(autoplay)
    doc.node(name, 'AnimationPlayer', parent, props)

def full_rect(extra=None):
    d = {'anchors_preset': 15, 'anchor_right': 1.0, 'anchor_bottom': 1.0, 'grow_horizontal': 2, 'grow_vertical': 2}
    if extra: d.update(extra)
    return d

def rect(l, t, r, b, extra=None):
    d = {'offset_left': float(l), 'offset_top': float(t), 'offset_right': float(r), 'offset_bottom': float(b)}
    if extra: d.update(extra)
    return d

def curve(doc, pts):
    data = []
    for x, y in pts: data += [V2(x, y), 0.0, 0.0, 0, 0]
    return doc.sub('Curve', {'_data': data, 'point_count': len(pts)}, hint='curve')

def gradient(doc, stops):
    offs = PF(*[o for o, _ in stops])
    cols = Raw('PackedColorArray(' + ', '.join(f'{c[0]}, {c[1]}, {c[2]}, {c[3]}' for _, c in stops) + ')')
    return doc.sub('Gradient', {'offsets': offs, 'colors': cols}, hint='grad')

# Арт нейросети: PNG из assets/art/gen, если импортирован (tools/import_art.py), иначе SVG-заглушка.
from artlib import art, art_scale, art_ratio, has_art  # noqa: E402,F401
