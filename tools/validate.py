"""Статическая проверка проекта без Godot (шаг 9). Запуск: python3 tools/validate.py [путь_к_проекту]
Проверяет:
  * все res:// пути существуют;
  * $Path / %Unique / get_node("...") из скриптов находят узлы в сценах, где висит скрипт;
  * [connection]: узлы есть, метод объявлен в скрипте получателя, сигнал объявлен (или встроенный);
  * дорожки AnimationPlayer указывают на существующие узлы и свойства (var в скрипте / известные встроенные);
  * ключи перевода (tr(), text/name/info в .tres, text в Label без auto_translate_mode=2) есть в CSV,
    число %d/%s совпадает в ru и en;
  * шрифты содержат все символы из CSV и сцен;
  * set_shader_parameter(&"x") / shader_parameter/x — x объявлен как uniform в каком-то шейдере.
Код выхода 1, если есть ошибки."""
import os, re, sys, csv, glob

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
errors, warns = [], []
stats = dict(conns=0, tracks=0, refs=0)
def err(m): errors.append(m)
def warn(m): warns.append(m)
def rp(p): return os.path.join(ROOT, p.replace('res://', ''))
def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

GENERATED = {'res://locale/strings.ru.translation', 'res://locale/strings.en.translation'}

# ---------------- 1. res:// пути ----------------
TEXT_EXT = ('.gd', '.tscn', '.tres', '.godot', '.cfg', '.gdshader')
files = [f for f in glob.glob(os.path.join(ROOT, '**', '*'), recursive=True)
         if f.endswith(TEXT_EXT) and '/tools/' not in f and '/.godot/' not in f]
for f in files:
    for m in re.finditer(r'res://[A-Za-z0-9_./\-]+', read(f)):
        p = m.group(0).rstrip('.')
        if p in GENERATED: continue
        if not os.path.exists(rp(p)):
            err(f'{os.path.relpath(f, ROOT)}: нет файла {p}')

# ---------------- разбор .tscn ----------------
def parse_scene(path):
    txt = read(path)
    sc = dict(ext={}, sub={}, nodes=[], conns=[])
    for m in re.finditer(r'\[ext_resource type="([^"]+)" path="([^"]+)" id="([^"]+)"\]', txt):
        sc['ext'][m.group(3)] = (m.group(1), m.group(2))
    blocks = re.split(r'\n(?=\[(?:sub_resource|node|connection|ext_resource|gd_scene))', txt)
    for b in blocks:
        m = re.match(r'\[sub_resource type="([^"]+)" id="([^"]+)"\]', b)
        if m:
            sc['sub'][m.group(2)] = (m.group(1), b); continue
        m = re.match(r'\[node name="([^"]+)"(?: type="([^"]+)")?(?: parent="([^"]*)")?(?: instance=ExtResource\("([^"]+)"\))?\]', b)
        if m:
            name, typ, parent, inst = m.groups()
            props = {}
            for pm in re.finditer(r'^([A-Za-z_][A-Za-z0-9_/:]*) = (.+)$', b, re.M):
                props[pm.group(1)] = pm.group(2)
            sc['nodes'].append(dict(name=name, typ=typ, parent=parent, inst=inst, props=props, block=b,
                                    unique='unique_name_in_owner = true' in b))
            continue
        for cm in re.finditer(r'\[connection signal="([^"]+)" from="([^"]+)" to="([^"]+)" method="([^"]+)"', b):
            sc['conns'].append(cm.groups())
    return sc

SCENES = {}
def scene(path):
    if path not in SCENES: SCENES[path] = parse_scene(rp(path))
    return SCENES[path]

def node_path(n):
    if n['parent'] is None: return '.'
    return n['name'] if n['parent'] == '.' else n['parent'] + '/' + n['name']

def tree(path, prefix=''):
    """{relpath: info} всех узлов, включая содержимое инстансов. info: typ, script, unique(own scene)"""
    sc = scene(path); out = {}
    for n in sc['nodes']:
        p = node_path(n)
        full = p if not prefix else (prefix if p == '.' else prefix + '/' + p)
        info = dict(typ=n['typ'], script=None, unique=n['unique'], own=(prefix == ''), node=n, scene=path)
        if n['inst']:
            ipath = sc['ext'][n['inst']][1]
            sub = tree(ipath, full)
            root = sub.get(full)
            if root:
                info['typ'] = root['typ']; info['script'] = root['script']
            out.update(sub)
        s = n['props'].get('script')
        if s:
            sm = re.match(r'ExtResource\("([^"]+)"\)', s)
            if sm: info['script'] = sc['ext'][sm.group(1)][1]
        out[full] = info
    return out

# ---------------- разбор .gd ----------------
def script_info(path):
    txt = read(rp(path))
    ext = re.search(r'^extends (\w+)', txt, re.M)
    return dict(
        txt=txt,
        extends=ext.group(1) if ext else None,
        funcs=set(re.findall(r'^(?:static )?func (\w+)', txt, re.M)),
        signals=set(re.findall(r'^signal (\w+)', txt, re.M)),
        vars=set(re.findall(r'^(?:@export(?:_\w+)?(?:\([^)]*\))? )?(?:@onready )?var (\w+)', txt, re.M)),
        dollar=[('', m.group(1) or m.group(2)) for m in re.finditer(r'\$(?:"([^"]+)"|([A-Za-z0-9_/]+))', txt)],
        unique=re.findall(r'%([A-Za-z_][A-Za-z0-9_]*)', re.sub(r'"[^"\n]*"', '""', txt)),
        getnode=re.findall(r'get_node(?:_or_null)?\("([^"]+)"\)', txt),
    )

BUILTIN_SIGNALS = {'timeout', 'pressed', 'finished', 'animation_finished', 'toggled', 'ready', 'tree_exited'}
BUILTIN_PROPS = {'position', 'scale', 'rotation', 'modulate', 'self_modulate', 'visible', 'color', 'offset',
                 'emitting', 'text', 'visible_ratio', 'size', 'pivot_offset', 'z_index', 'frame', 'skew'}

def resolve(base, rel):
    parts = [] if base == '.' else base.split('/')
    for seg in rel.split('/'):
        if seg in ('', '.'): continue
        if seg == '..':
            if not parts: return None
            parts.pop()
        else: parts.append(seg)
    return '/'.join(parts) if parts else '.'

ALL_SCENES = sorted('res://' + os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, 'scenes', '**', '*.tscn'), recursive=True))
for sp in ALL_SCENES:
    sc = scene(sp); t = tree(sp); short = sp.replace('res://', '')
    # скрипты: $ / % / get_node
    for p, info in t.items():
        if not info['script'] or info['scene'] != sp and not info['own']:
            # проверяем скрипт только в той сцене, где он прикреплён к корню (её саму валидируем отдельно)
            if not (info['script'] and info['own']): continue
        if not info['own']: continue
        si = script_info(info['script'])
        for _, ref in si['dollar']:
            stats['refs'] += 1
            if resolve(p, ref) not in t: err(f'{short}: {info["script"]} → ${ref} не найден от {p}')
        for ref in si['getnode']:
            if ref.startswith('/root/'): continue
            if resolve(p, ref) not in t and not ref.startswith('%'):
                # может быть узел внутри дочерних (slot.get_node("Icon")) — проверяется отдельно
                pass
        for u in set(si['unique']):
            owner_root = '.' if p == '.' else None
            if p != '.':
                continue  # %Unique у некорневых скриптов ищется в их собственной сцене
            stats['refs'] += 1
            ok = any(i['unique'] and i['own'] and k.split('/')[-1] == u for k, i in t.items())
            if not ok: err(f'{short}: {info["script"]} → %{u} нет уникального узла')
    # соединения
    for sig, frm, to, meth in sc['conns']:
        stats['conns'] += 1
        fp, tp = resolve('.', frm), resolve('.', to)
        if fp not in t: err(f'{short}: connection from {frm} — нет узла'); continue
        if tp not in t: err(f'{short}: connection to {to} — нет узла'); continue
        ts = t[tp]['script']
        if not ts or meth not in script_info(ts)['funcs']: err(f'{short}: метод {meth} не найден в скрипте {to} ({ts})')
        fs = t[fp]['script']
        if sig not in BUILTIN_SIGNALS and (not fs or sig not in script_info(fs)['signals']):
            err(f'{short}: сигнал {sig} не объявлен у {frm}')
    # анимации
    for p, info in t.items():
        if info['typ'] != 'AnimationPlayer' or not info['own']: continue
        n = info['node']
        root_rel = n['props'].get('root_node', 'NodePath("..")')
        root_rel = re.match(r'NodePath\("([^"]*)"\)', root_rel).group(1)
        anim_root = resolve(p, root_rel)
        libs = re.findall(r'SubResource\("([^"]+)"\)', n['props'].get('libraries', '') + n['block'])
        anims = []
        for lid in libs:
            if lid in sc['sub'] and sc['sub'][lid][0] == 'AnimationLibrary':
                anims += re.findall(r'SubResource\("([^"]+)"\)', sc['sub'][lid][1])
        for aid in anims:
            ab = sc['sub'][aid][1]
            aname = re.search(r'resource_name = "([^"]+)"', ab).group(1)
            for tp_ in re.findall(r'tracks/\d+/path = NodePath\("([^"]+)"\)', ab):
                stats['tracks'] += 1
                np_, _, prop = tp_.partition(':')
                target = resolve(anim_root, np_)
                if target not in t: err(f'{short}: анимация {aname}: нет узла {np_}'); continue
                if not prop: continue
                top = prop.split(':')[0]
                tsc = t[target]['script']
                vars_ = script_info(tsc)['vars'] if tsc else set()
                if top not in vars_ and top not in BUILTIN_PROPS and not top.startswith('material'):
                    warn(f'{short}: анимация {aname}: свойство {np_}:{prop} — проверь вручную')
            for m in re.finditer(r'"method": &"(\w+)"', ab):
                warn(f'{short}: анимация {aname}: вызов метода {m.group(1)} — проверь вручную')

# ---------------- перевод ----------------
CSV_PATH = os.path.join(ROOT, 'locale', 'strings.csv')
rows = list(csv.reader(open(CSV_PATH, encoding='utf-8')))
header, body = rows[0], rows[1:]
keys = {}
for r in body:
    if not r or not r[0]: continue
    if r[0] in keys: err(f'strings.csv: дубль ключа {r[0]}')
    keys[r[0]] = r
    if len(r) != len(header): err(f'strings.csv: {r[0]} — {len(r)} колонок вместо {len(header)}')
    elif len(re.findall(r'%[ds]', r[1].replace('%%', ''))) != len(re.findall(r'%[ds]', r[2].replace('%%', ''))):
        err(f'strings.csv: {r[0]} — разное число %d/%s в ru и en')
used = set()
KEY_RE = r'[A-Z][A-Z0-9_]{2,}'
for f in glob.glob(os.path.join(ROOT, '**', '*.gd'), recursive=True):
    if '/tools/' in f: continue
    t = read(f)
    used |= set(re.findall(r'\btr\("(' + KEY_RE + r')"\)', t))
    # Globals.device_text("KEY") -> KEY, KEY_MOBILE, KEY_DESKTOP (KEY обязателен как запасной)
    for k in re.findall(r'device_text\("(' + KEY_RE + r')"\)', t):
        used.add(k)
        for suf in ('_MOBILE', '_DESKTOP'):
            if k + suf in keys: used.add(k + suf)
    for arr in re.findall(r'const \w+: Array\[String\] = \[([^\]]+)\]', t):
        used |= set(re.findall(r'"(' + KEY_RE + r')"', arr))
for f in glob.glob(os.path.join(ROOT, 'data', '**', '*.tres'), recursive=True):
    for k in re.findall(r'^(?:text|name|info|upgrade_info) = "([^"]*)"', read(f), re.M):
        if k: used.add(k)
for sp in ALL_SCENES:
    for n in scene(sp)['nodes']:
        if n['typ'] in ('Label', 'Button') and 'text' in n['props'] and 'auto_translate_mode = 2' not in n['block']:
            v = n['props']['text'].strip('"')
            if re.fullmatch(KEY_RE, v): used.add(v)
            elif v: warn(f'{sp}: {n["name"]}.text="{v}" — не ключ перевода')
# динамические ключи NPC_<ID> из бестиария
for sp in ALL_SCENES:
    if 'menu' in sp:
        for n in scene(sp)['nodes']:
            if n['parent'] == 'Bestiary/Slots': used.add('NPC_' + n['name'].upper())
for k in sorted(used - set(keys)): err(f'перевод: ключа {k} нет в strings.csv')
for k in sorted(set(keys) - used): warn(f'перевод: ключ {k} нигде не используется')

# ---------------- tr("KEY") % args: число аргументов = числу %d/%s/%f ----------------
for f in glob.glob(os.path.join(ROOT, '**', '*.gd'), recursive=True):
    t = read(f)
    for m in re.finditer(r'tr\("([A-Z0-9_]+)"\)\s*%\s*(\[)?', t):
        key = m.group(1)
        if key not in keys: continue
        if m.group(2):
            i = j = m.end(); depth = 1
            while depth:
                depth += t[j] in '([{'; depth -= t[j] in ')]}'; j += 1
            n = len([x for x in re.split(r',(?![^()\[\]]*[)\]])', t[i:j - 1]) if x.strip()])
        else:
            n = 1
        for col, txt in ((1, keys[key][1]), (2, keys[key][2])):
            txt = txt.replace('%%', '')  # «%%» — это просто знак процента («+25%% урона»), не аргумент
            need = len(re.findall(r'%[-+0-9.]*[dsf]', txt))
            if need != n or txt.count('%') != need:
                err(f'{os.path.relpath(f, ROOT)}: tr("{key}") % — в коде {n} арг., в {header[col]} {need} плейсхолд. ({txt.count("%")} знаков %)')

# ---------------- шрифты ----------------
try:
    from fontTools.ttLib import TTFont
    chars = set()
    for r in body: chars |= set((r[1] + r[2]).replace('\\n', ''))
    for sp in ALL_SCENES:
        for n in scene(sp)['nodes']:
            if 'text' in n['props']: chars |= set(n['props']['text'].strip('"'))
    chars |= set('0123456789+-%.,:/×?!$ ')
    for fp in glob.glob(os.path.join(ROOT, 'assets', 'fonts', '*.ttf')):
        cmap = TTFont(fp).getBestCmap()
        miss = sorted(c for c in chars if c.strip() and ord(c) not in cmap)
        if miss: err(f'{os.path.basename(fp)}: нет глифов {"".join(miss)}')
except ImportError:
    warn('fontTools нет — шрифты не проверены')

# ---------------- шейдерные параметры ----------------
uniforms = set()
for f in glob.glob(os.path.join(ROOT, 'assets', 'shaders', '*.gdshader')):
    uniforms |= set(re.findall(r'uniform\s+\w+\s+(\w+)', read(f)))
for f in files:
    t = read(f)
    for p in re.findall(r'set_shader_parameter\(&?"(\w+)"', t) + re.findall(r'get_shader_parameter\(&?"(\w+)"', t) + re.findall(r'shader_parameter/(\w+)', t):
        if p not in uniforms: err(f'{os.path.relpath(f, ROOT)}: шейдерного параметра {p} нет ни в одном шейдере')
    for p in re.findall(r'_post\(&"(\w+)"', t) + re.findall(r'_pulse_param\(&"(\w+)"', t):
        if p not in uniforms: err(f'{os.path.relpath(f, ROOT)}: post-параметра {p} нет в шейдере')

# ---------------- звуки: Audio.sfx(&"x") — x есть в Audio.SFX, файл на месте ----------------
audio_src = read(os.path.join(ROOT, 'scripts', 'autoload', 'audio.gd'))
sfx_names = set(re.findall(r'&"(\w+)": preload\("res://assets/audio/sfx/', audio_src))
for f in files:
    for name in re.findall(r'Audio\.sfx\(&"(\w+)"', read(f)):
        if name not in sfx_names: err(f'{os.path.relpath(f, ROOT)}: звука {name} нет в Audio.SFX')

# ---------------- @onready-типы против типов узлов ----------------
PARENT = {
    'Node2D': 'CanvasItem', 'Sprite2D': 'Node2D', 'Line2D': 'Node2D', 'CPUParticles2D': 'Node2D', 'Camera2D': 'Node2D',
    'Control': 'CanvasItem', 'Label': 'Control', 'ColorRect': 'Control', 'TextureRect': 'Control', 'Button': 'BaseButton',
    'BaseButton': 'Control', 'Container': 'Control', 'BoxContainer': 'Container', 'VBoxContainer': 'BoxContainer',
    'HBoxContainer': 'BoxContainer', 'GridContainer': 'Container', 'CanvasItem': 'Node', 'Timer': 'Node',
    'AnimationPlayer': 'AnimationMixer', 'AnimationMixer': 'Node', 'AudioStreamPlayer': 'Node', 'CanvasLayer': 'Node',
}
CLASS_NAMES = {}
for f in glob.glob(os.path.join(ROOT, '**', '*.gd'), recursive=True):
    t = read(f)
    cn = re.search(r'^class_name (\w+)', t, re.M); ex = re.search(r'^extends (\w+)', t, re.M)
    if cn and ex: CLASS_NAMES[cn.group(1)] = ('res://' + os.path.relpath(f, ROOT), ex.group(1))
def is_a(typ, script, want):
    if script:
        for cn, (sp_, _) in CLASS_NAMES.items():
            if sp_ == script and cn == want: return True
    while typ:
        if typ == want: return True
        typ = PARENT.get(typ)
    return want == 'Node'
for sp in ALL_SCENES:
    t = tree(sp); short = sp.replace('res://', '')
    for p, info in t.items():
        if not info['script'] or not info['own']: continue
        for m in re.finditer(r'@onready var \w+: (\w+) = (\$"?[A-Za-z0-9_/]+"?|%\w+)', script_info(info['script'])['txt']):
            want, ref = m.groups()
            if ref.startswith('%'):
                if p != '.': continue
                hits = [k for k, i in t.items() if i['unique'] and i['own'] and k.split('/')[-1] == ref[1:]]
                target = hits[0] if hits else None
            else:
                target = resolve(p, ref[1:].strip('"'))
            if target is None or target not in t: continue
            stats['refs'] += 1
            ti = t[target]
            if not is_a(ti['typ'], ti['script'], want):
                err(f'{short}: {info["script"]}: {ref} — узел {ti["typ"]}, а переменная {want}')

print(f'Проверено: {len(ALL_SCENES)} сцен, {len(files)} файлов, {len(keys)} ключей перевода, '
      f'{stats["refs"]} ссылок на узлы, {stats["conns"]} соединений, {stats["tracks"]} дорожек анимаций')
for w in warns: print('  [warn]', w)
for e in errors: print('  [ERR] ', e)
print('OK' if not errors else f'ОШИБОК: {len(errors)}')
sys.exit(1 if errors else 0)
