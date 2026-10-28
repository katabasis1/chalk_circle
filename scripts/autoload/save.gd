extends Node
## Мета-прогресс, настройки и сохранённый забег.
## Локально (user://) пишем сразу при каждом изменении — это дёшево.
## В облако Яндекса (player.setData) — пачкой, не чаще раза в CLOUD_INTERVAL секунд (у SDK есть лимиты частоты),
## и немедленно по flush(): конец забега, покупка, сворачивание вкладки.
## Слияние облако/локально (merge): рекорды и коллекции — «лучшее из двух», настройки и валюта — из более свежей записи (поле "t"),
## сохранённый забег — по полю "run_t" (чтобы закончившийся забег не «воскресал» из старого облака).

signal changed

const PATH: String = "user://chalk_circle.save"
const VERSION: int = 2
const CLOUD_INTERVAL: float = 10.0

const DEFAULTS: Dictionary = {
    "v": VERSION,
    "t": 0,
    "best_night": 0,
    "best_endless": 0,
    "best_combo": 0,
    "runs": 0,
    "wins": 0,
    "bestiary": [],
    "caught": {},
    "sound": true,
    "music": true,
    "vibration": true,
    "quality": "high",
    "tutorial": false,
    "seal_hint": false,
    "wax": 0,
    "unlocks": [],
    "run": {},
    "run_t": 0,
}
## Монотонные счётчики: при слиянии берём максимум.
const MAX_KEYS: Array[String] = ["best_night", "best_endless", "best_combo", "runs", "wins"]
## Множества: при слиянии объединяем.
const UNION_KEYS: Array[String] = ["bestiary", "unlocks"]
## «Сделано хоть раз»: логическое ИЛИ.
const OR_KEYS: Array[String] = ["tutorial", "seal_hint"]

var data: Dictionary = {}
var _cloud_dirty: bool = false
var _cloud_cooldown: float = 0.0

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    data = DEFAULTS.duplicate(true)
    load_local()

func _process(delta: float) -> void:
    if _cloud_cooldown > 0.0:
        _cloud_cooldown -= delta / maxf(Engine.time_scale, 0.01)
    if _cloud_dirty and _cloud_cooldown <= 0.0:
        _push_cloud(false)

# ---------- запись ----------
## Зафиксировать изменения: локально сразу, в облако — отложенно (или сразу, если flush_now).
func save(flush_now: bool = false) -> void:
    data["t"] = int(Platform.now_unix())
    _write_local()
    _cloud_dirty = true
    if flush_now:
        flush()
    changed.emit()

## Отправить отложенное в облако прямо сейчас (вкладку закрывают, конец забега, покупка).
func flush() -> void:
    if _cloud_dirty:
        _push_cloud(true)

func _push_cloud(urgent: bool) -> void:
    _cloud_dirty = false
    _cloud_cooldown = CLOUD_INTERVAL
    Platform.save_cloud(data, urgent)

func _write_local() -> void:
    var f: FileAccess = FileAccess.open(PATH, FileAccess.WRITE)
    if f:
        f.store_string(JSON.stringify(data))

func load_local() -> void:
    if not FileAccess.file_exists(PATH):
        return
    var f: FileAccess = FileAccess.open(PATH, FileAccess.READ)
    if f == null:
        return
    var parsed: Variant = JSON.parse_string(f.get_as_text())
    if parsed is Dictionary:
        data = _migrate(parsed)

# ---------- миграция и слияние ----------
## Привести любые сохранённые данные (старой версии, из облака, после JSON с float вместо int) к текущей схеме.
func _migrate(src: Dictionary) -> Dictionary:
    var out: Dictionary = DEFAULTS.duplicate(true)
    for k in src:
        var key: String = str(k)
        if out.has(key):
            out[key] = _coerce(out[key], src[k])
        else:
            # Ключи из более новой версии игры не теряем.
            out[key] = src[k]
    if int(src.get("v", 1)) < 2:
        var caught: Dictionary = out["caught"]
        for id in out["bestiary"]:
            if not caught.has(id):
                caught[id] = 1
    out["v"] = VERSION
    return out

static func _coerce(default: Variant, v: Variant) -> Variant:
    if v == null:
        return default
    match typeof(default):
        TYPE_INT:
            return int(v) if (v is float or v is int or v is String) else default
        TYPE_FLOAT:
            return float(v) if (v is float or v is int or v is String) else default
        TYPE_BOOL:
            return bool(v) if (v is bool or v is float or v is int) else default
        TYPE_STRING:
            return str(v)
        TYPE_ARRAY:
            var a: Array = []
            if v is Array:
                for x in v:
                    a.append(str(x))
            return a
        TYPE_DICTIONARY:
            return (v as Dictionary).duplicate(true) if v is Dictionary else (default as Dictionary).duplicate(true)
    return v

## Слить с данными из облака Яндекса. Если облако отстаёт — отправим ему результат.
func merge(other_raw: Dictionary) -> void:
    var other: Dictionary = _migrate(other_raw)
    var newer: bool = int(other["t"]) > int(data["t"])
    var out: Dictionary = (other if newer else data).duplicate(true)
    for k in MAX_KEYS:
        out[k] = maxi(int(data[k]), int(other[k]))
    for k in UNION_KEYS:
        var a: Array = (data[k] as Array).duplicate()
        for x in other[k]:
            if not a.has(x):
                a.append(x)
        out[k] = a
    for k in OR_KEYS:
        out[k] = bool(data[k]) or bool(other[k])
    var c: Dictionary = (data["caught"] as Dictionary).duplicate()
    var oc: Dictionary = other["caught"]
    for id in oc:
        c[id] = maxi(int(c.get(id, 0)), int(oc[id]))
    out["caught"] = c
    if int(other["run_t"]) > int(data["run_t"]):
        out["run"] = (other["run"] as Dictionary).duplicate(true)
    else:
        out["run"] = (data["run"] as Dictionary).duplicate(true)
    out["run_t"] = maxi(int(data["run_t"]), int(other["run_t"]))
    data = out
    _write_local()
    if JSON.stringify(data) != JSON.stringify(other):
        _cloud_dirty = true
    changed.emit()

# ---------- бестиарий ----------
func has_spirit(id: StringName) -> bool:
    return (data["bestiary"] as Array).has(str(id))

func caught_count(id: StringName) -> int:
    return int((data["caught"] as Dictionary).get(str(id), 0))

## Отметить поимку духа. Возвращает true, если этот дух пойман впервые.
func add_spirit(id: StringName) -> bool:
    var key: String = str(id)
    var caught: Dictionary = data["caught"]
    caught[key] = int(caught.get(key, 0)) + 1
    var first: bool = not has_spirit(id)
    if first:
        (data["bestiary"] as Array).append(key)
    save()
    return first

# ---------- забег ----------
func has_run() -> bool:
    return not (data.get("run", {}) as Dictionary).is_empty()

func get_run() -> Dictionary:
    return data.get("run", {})

## Чекпоинт забега (начало ночи / лавки): если вкладку закроют, продолжим отсюда.
func save_run(run: Dictionary) -> void:
    data["run"] = run
    data["run_t"] = int(Platform.now_unix())
    save()

func clear_run() -> void:
    data["run"] = {}
    data["run_t"] = int(Platform.now_unix())
    save(true)

## Конец забега (смерть или рассвет): рекорды, счётчики, сброс сохранённого забега. Сразу в облако.
## count_run = false — повторная смерть после «Воскреснуть» (забег уже засчитан).
func finish_run(nights: int, victory: bool, endless: bool, count_run: bool = true, best_combo: int = 0) -> void:
    data["run"] = {}
    data["best_combo"] = maxi(int(data["best_combo"]), best_combo)
    data["run_t"] = int(Platform.now_unix())
    if count_run and not endless:
        data["runs"] = int(data["runs"]) + 1
    if victory and not endless:
        data["wins"] = int(data["wins"]) + 1
    if endless:
        data["best_endless"] = maxi(int(data["best_endless"]), nights)
    data["best_night"] = maxi(int(data["best_night"]), nights)
    save(true)

## Совместимость со старым кодом.
func record_night(n: int) -> void:
    if n > int(data["best_night"]):
        data["best_night"] = n
        save()

# ---------- флаги и настройки ----------
func get_flag(key: String, fallback: Variant = null) -> Variant:
    return data.get(key, DEFAULTS.get(key, fallback))

func set_flag(key: String, value: Variant) -> void:
    var cur: Variant = data.get(key)
    if typeof(cur) == typeof(value) and cur == value:
        return
    data[key] = value
    save()
