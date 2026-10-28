extends Resource
class_name GameState
## Состояние одного забега («семь ночей»).

const BASE_ACTION: ActionData = preload("res://data/actions/strike.tres")
const RPS_CAP: float = 0.85
## Комбо (пункт 2.1): попадания подряд без промаха и без раны. С этих ступеней — бонус урона (+25% / +50%).
## Баланс потом пойдёт через remote flags (пункт 4.11).
const COMBO_TIERS: Array[int] = [5, 10]
const COMBO_BONUS: Array[float] = [0.25, 0.5]
## Раны (пункт 2.5): трещина на меловом круге за каждые потерянные WOUND_STEP здоровья (сколько трещин — столько ран).
const WOUND_STEP: float = 0.5
const MAX_WOUNDS: int = 12
## Ближе этого (рад) две трещины не встают — иначе сольются, и раны не сосчитать (~54 px по черте).
const WOUND_GAP: float = 0.22

@export var health: float = 3.0
@export var max_health: float = 3.0:
    set(value):
        var diff: float = value - max_health
        max_health = value
        if diff > 0.0:
            health += diff
## Пустые склянки для Печати.
@export var jars: int = 2
@export var free_rerolls: float = 0.0
@export var free_snacks: float = 0.0
@export var first_hit_bonus: float = 0.0
@export var bonus_damage: float = 0.0
@export var nullified_hits: float = 0.0
@export var dodge_damage: float = 0.0
@export var cash: int = 0
@export var items: Array[ItemData] = []
## Углы трещин на круге (рад, 0..TAU) в порядке нанесения. Число держит sync_wounds(): = wound_count().
@export var wounds: Array[float] = []

@export var rounds_won: int = 0
@export var enemies_killed: int = 0
@export var spirits_caught: int = 0
@export var damage_dealt: int = 0
@export var money_earned: int = 0
## Лучшее комбо за забег (статистика финала и рекорд в сейве).
@export var best_combo: int = 0
## Ударов «Идеально» за забег (2.2).
@export var perfect_hits: int = 0
@export var revived: bool = false
@export var endless: bool = false
## Последний бой был с боссом (для «Воскреснуть»).
var last_fight_boss: bool = false

## Оборотов искры в секунду.
var rps: float:
    get:
        var t: float = enemies_killed / 18.0
        var r: float = clampf(lerpf(0.33, 0.5, t), 0.33, 0.5) + lerpf(0.0, 0.1, t)
        return minf(r, RPS_CAP)

var actions: Array[ActionData]:
    get:
        var out: Array[ActionData] = [BASE_ACTION]
        for item in items:
            if item.action:
                out.append(item.action)
        return out

var night: int:
    get:
        return rounds_won + 1

## Ступень комбо: 0 — без бонуса, 1 — с COMBO_TIERS[0] попаданий, 2 — с COMBO_TIERS[1]…
static func combo_tier(combo: int) -> int:
    var tier: int = 0
    for i in COMBO_TIERS.size():
        if combo >= COMBO_TIERS[i]:
            tier = i + 1
    return tier

## Бонус урона от комбо (0.25 = +25%).
static func combo_bonus(combo: int) -> float:
    var tier: int = combo_tier(combo)
    return 0.0 if tier == 0 else COMBO_BONUS[tier - 1]

# ---------- раны (2.5) ----------
## Сколько трещин должно быть на круге при текущем здоровье.
func wound_count() -> int:
    return clampi(roundi((max_health - health) / WOUND_STEP), 0, MAX_WOUNDS)

## Рана там, где атака прорвала круг (angle < 0 — место не важно). Звать сразу после того, как убавили health.
func add_wound(angle: float = -1.0) -> void:
    if wounds.size() < wound_count():
        wounds.append(free_wound_angle(angle))
    sync_wounds()

## Подогнать трещины под здоровье: подлечился — последние затягиваются; ранен «без места» — трещина в свободном углу.
func sync_wounds() -> void:
    var want: int = wound_count()
    while wounds.size() > want:
        wounds.pop_back()
    while wounds.size() < want:
        wounds.append(free_wound_angle())

## Ближайший к wish угол не теснее WOUND_GAP к другим трещинам; wish < 0 — самый свободный угол.
func free_wound_angle(wish: float = -1.0) -> float:
    if wish >= 0.0:
        wish = fposmod(wish, TAU)
        for step in 15:
            var off: float = WOUND_GAP * ceilf(step * 0.5) * (1.0 if step % 2 == 0 else -1.0)
            var a: float = fposmod(wish + off, TAU)
            if _wound_room(a) >= WOUND_GAP:
                return a
    var best: float = randf() * TAU
    var best_room: float = _wound_room(best)
    var base: float = randf() * TAU
    for i in 24:
        var a: float = fposmod(base + TAU * i / 24.0, TAU)
        var room: float = _wound_room(a)
        if room > best_room:
            best = a
            best_room = room
    return best

## Расстояние (рад) от угла до ближайшей трещины.
func _wound_room(a: float) -> float:
    var room: float = PI
    for w in wounds:
        room = minf(room, absf(angle_difference(a, w)))
    return room

# ---------- сохранение забега ----------
## Поля, которые пишутся в чекпоинт забега (Save.save_run). Новые @export-поля забега добавляй сюда
## (числа и флаги; массивы — items, wounds — пишутся отдельно в to_dict/from_dict).
const SAVE_FIELDS: Array[String] = ["max_health", "health", "jars", "free_rerolls", "free_snacks", "first_hit_bonus",
    "bonus_damage", "nullified_hits", "dodge_damage", "cash", "rounds_won", "enemies_killed", "spirits_caught",
    "damage_dealt", "money_earned", "best_combo", "perfect_hits", "revived", "endless", "last_fight_boss"]

func to_dict() -> Dictionary:
    var d: Dictionary = {}
    for f in SAVE_FIELDS:
        d[f] = get(f)
    var list: Array = []
    for item in items:
        var e: Dictionary = {"id": str(item.id), "lvl": item.level}
        if item.action:
            # Улучшения меняют параметры действия (action_stat), «Медный грош» растёт прямо в бою (damage).
            var act: Dictionary = {"damage": item.action.damage}
            if item.action_stat != "":
                act[item.action_stat] = item.action.get(item.action_stat)
            e["act"] = act
        list.append(e)
    d["items"] = list
    d["wounds"] = Array(wounds)
    return d

static func from_dict(d: Dictionary) -> GameState:
    var gs: GameState = GameState.new()
    # Сеттер max_health прибавляет разницу к health — поэтому сначала он, а health перезапишем ниже.
    gs.max_health = float(d.get("max_health", gs.max_health))
    for f in SAVE_FIELDS:
        if f == "max_health" or not d.has(f) or d[f] == null:
            continue
        var cur: Variant = gs.get(f)
        match typeof(cur):
            TYPE_INT:
                gs.set(f, int(d[f]))
            TYPE_FLOAT:
                gs.set(f, float(d[f]))
            TYPE_BOOL:
                gs.set(f, bool(d[f]))
    var list: Variant = d.get("items", [])
    if list is Array:
        for e in list:
            if not (e is Dictionary):
                continue
            var base: ItemData = Registry.item(StringName(str(e.get("id", ""))))
            if base == null:
                continue
            var inst: ItemData = base.make_instance()
            inst.level = maxi(1, int(e.get("lvl", 1)))
            var act: Variant = e.get("act", {})
            if inst.action and act is Dictionary:
                for k in act:
                    var key: String = str(k)
                    var was: Variant = inst.action.get(key)
                    if was is int:
                        inst.action.set(key, int(act[k]))
                    elif was is float:
                        inst.action.set(key, float(act[k]))
            gs.items.append(inst)
    var w: Variant = d.get("wounds", [])
    if w is Array:
        for a in w:
            if a is float or a is int:
                gs.wounds.append(fposmod(float(a), TAU))
    gs.sync_wounds()
    return gs
