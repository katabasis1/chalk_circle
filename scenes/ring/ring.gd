extends Node2D
class_name Ring
## Меловой круг: искра бежит по черте, на черте появляются секции. Одна кнопка — «тап».

signal pressed(section: Section)
signal expired(section: Section)
signal missed(angle: float)
## Замах (2.4): атака нечисти появилась на круге контуром и заряжается — нечисти пора замахиваться.
signal telegraph_started(section: Section)
## Заряд кончился, атака вспыхнула и стала настоящей секцией.
signal telegraph_armed(section: Section)
## Атаку убрали, пока она заряжалась (отбили, бой кончился) — замах сорвался.
signal telegraph_cancelled(section: Section)

const SECTION_SCENE: PackedScene = preload("res://scenes/ring/section.tscn")
const BURST_SCENE: PackedScene = preload("res://scenes/fx/burst.tscn")
const CHIPS_SCENE: PackedScene = preload("res://scenes/fx/chips.tscn")
const RADIUS: float = 246.0
const MAX_SECTIONS: int = 4
const BASE_RPS: float = 0.33
## Замах (2.4): сколько секунд атака нечисти заряжается на базовой скорости искры.
## Быстрее искра — короче замах (до 70%), в ярости Печати — ещё короче.
const TELEGRAPH_TIME: float = 0.5
const TELEGRAPH_MIN_SHARE: float = 0.7
const TELEGRAPH_FRENZY: float = 0.65
const CHALK: Color = Color("efe6d2")
const GOLD: Color = Color("ffd25a")
## Раны (2.5): столько трещин понимает шейдер (chalk_ring.gdshader, MAX_CRACKS). Больше GameState.MAX_WOUNDS —
## чтобы залечивающиеся трещины не вытесняли свежие.
const MAX_CRACKS: int = 16
## Трещина раскрывается за CRACK_OPEN с, залечивается (золото, разрыв стягивается) за CRACK_HEAL с.
const CRACK_OPEN: float = 0.22
const CRACK_HEAL: float = 0.75

## Неподвижные секции интерфейса (меню, лавка, финал).
@export var ui: Array[ActionData] = []
## Скорость растёт с убитой нечистью (в бою). В меню/лавке — постоянная.
@export var scaling_rps: bool = false
@export var enemy_color: Color = Color("e0283c")
## Атаки нечисти сначала заряжаются (2.4). Включено на круге боя (fight.tscn).
@export var telegraph: bool = false
## Раны (2.5): трещины на черте по GameState.wounds — круг и есть здоровье. Включено на круге боя и лавки.
@export var wounds: bool = false

var player_actions: Array[ActionData] = []
var enemy_actions: Array[ActionData] = []
var player_i: int = 0
var enemy_i: int = 0
var next_is_enemy: Array[bool] = [false, true]
var next_is_enemy_i: int = 0
var bonus_rps: float = 0.0
var reversed: bool = false
var blind: bool = false
## Нечисть в ярости (пока горит Печать) — атаки чаще.
var frenzy: bool = false
var stopped: bool = false
var _pulse: float = 0.0
## Трещина на черте: угол, раскрытие 0..1, вспышка раны (гаснет), прогресс лечения (-1 — не лечится).
class Crack:
    var angle: float = 0.0
    var open: float = 0.0
    var hot: float = 0.0
    var heal: float = -1.0

## Трещины на черте, включая залечивающиеся (они в конце пути, heal >= 0).
var _cracks: Array[Crack] = []
var _danger: float = 0.0
var _beat: float = 0.0
## Счётчики для дымового теста: трещин раскрылось / залечено на этом круге.
var cracks_opened: int = 0
var cracks_healed: int = 0

@onready var pivot: Node2D = $Pivot
@onready var spark: Node2D = %Spark
@onready var spark_shaker: Shaker = %SparkShaker
@onready var trail: CPUParticles2D = %Trail
@onready var sections_root: Node2D = $Sections
@onready var fx_root: Node2D = $Fx
@onready var action_timer: Timer = $ActionTimer
@onready var pause_timer: Timer = $PauseTimer
@onready var miss_buffer: Timer = $MissBuffer
@onready var chalk: ColorRect = $Chalk
@onready var runes: Sprite2D = $Runes

var rps: float:
    get:
        return (Globals.game_state.rps if scaling_rps else BASE_RPS) + bonus_rps

var action_time: float:
    get:
        var k: float = Globals.game_state.enemies_killed / 9.0
        return clampf(lerpf(0.7, 0.4, k), 0.4, 0.7) / Globals.game_state.rps

func _ready() -> void:
    shuffle()
    set_ui(ui)
    action_timer.start(action_time)
    if wounds:
        # Старые раны (с прошлой ночи, из чекпоинта) уже на черте — без анимации.
        _sync_cracks(false)
        _update_cracks(0.0)

func set_ui(actions: Array[ActionData]) -> void:
    ui = actions
    for s in live_sections():
        s.die(false)
    for a in ui:
        add_section(a)

func shuffle() -> void:
    player_actions = player_actions.duplicate()
    player_actions.shuffle()
    enemy_actions = enemy_actions.duplicate()
    enemy_actions.shuffle()
    player_i = 0
    enemy_i = 0
    next_is_enemy_i = 0

func live_sections() -> Array[Section]:
    var out: Array[Section] = []
    for c in sections_root.get_children():
        var s: Section = c as Section
        if s and not s.dead:
            out.append(s)
    return out

func _process(delta: float) -> void:
    if not stopped and pause_timer.is_stopped():
        var dir: float = -1.0 if reversed else 1.0
        pivot.rotation = fposmod(pivot.rotation + rps * TAU * delta * dir, TAU)
    if not stopped and not player_actions.is_empty() and action_timer.is_stopped() and live_sections().size() < MAX_SECTIONS:
        add_next_combat_action()
        action_timer.start(action_time * (0.55 if frenzy else 1.0))
    var target: Vector2 = Vector2.ZERO if blind else Vector2.ONE
    spark.scale = spark.scale.lerp(target, 1.0 - exp(-14.0 * delta))
    trail.emitting = not blind
    var ang: float = pivot.rotation
    for s in live_sections():
        s.hover = s.contains(ang)
    _pulse = move_toward(_pulse, 0.0, delta * 2.5)
    (chalk.material as ShaderMaterial).set_shader_parameter(&"pulse", _pulse)
    if wounds:
        _sync_cracks(true)
        _update_cracks(delta)
    runes.rotation -= delta * 0.06 * (rps / BASE_RPS) * (-1.0 if reversed else 1.0)

func _unhandled_input(event: InputEvent) -> void:
    if stopped or Globals.input_locked:
        return
    if not event.is_action_pressed(&"tap", false):
        return
    get_viewport().set_input_as_handled()
    tap()

func tap() -> void:
    if not pause_timer.is_stopped():
        return
    spark.scale = Vector2(1.7, 0.6)
    var ang: float = pivot.rotation
    var best: Section = null
    var best_d: float = 0.0
    for s in live_sections():
        var d: float = s.hit_distance(ang)
        if d < 0.0 and (best == null or d < best_d):
            best = s
            best_d = d
    if best:
        best.perfect = best.is_perfect(ang)
        if best.perfect:
            spark.scale = Vector2(2.3, 0.45)
        miss_buffer.start()
        _pulse = 1.0
        _burst(best.center, GOLD if best.perfect else best.color)
        best.press()
    elif miss_buffer.is_stopped():
        missed.emit(ang)
        pause_timer.start(maxf(0.3 * BASE_RPS / Globals.game_state.rps, 0.1))
        spark_shaker.shake(10.0, 0.2)
        Audio.sfx(&"miss", -3.0)

func add_next_combat_action() -> void:
    next_is_enemy_i = (next_is_enemy_i + 1) % next_is_enemy.size()
    if next_is_enemy_i == 0:
        next_is_enemy.shuffle()
    if next_is_enemy[next_is_enemy_i] and not enemy_actions.is_empty():
        add_enemy_action()
    else:
        player_i = (player_i + 1) % player_actions.size()
        add_section(player_actions[player_i])

## null — атак у нечисти нет (первая за ночь) или круг переполнен.
func add_enemy_action() -> Section:
    if enemy_actions.is_empty() or live_sections().size() >= MAX_SECTIONS + 1:
        return null
    enemy_i = (enemy_i + 1) % enemy_actions.size()
    return add_section(enemy_actions[enemy_i], telegraph_time())

## Сколько заряжается атака нечисти прямо сейчас (0 — замаха нет, секция сразу настоящая).
func telegraph_time() -> float:
    if not telegraph:
        return 0.0
    var t: float = TELEGRAPH_TIME * clampf(BASE_RPS / maxf(rps, 0.01), TELEGRAPH_MIN_SHARE, 1.0)
    return t * (TELEGRAPH_FRENZY if frenzy else 1.0)

## Сколько атак сейчас заряжается (замах ещё идёт).
func charging_count() -> int:
    var n: int = 0
    for s in live_sections():
        if s.charging:
            n += 1
    return n

## charge > 0 — секция сначала заряжается столько секунд (2.4).
func add_section(action: ActionData, charge: float = 0.0) -> Section:
    var center: float
    if action.fixed_location >= 0.0:
        center = action.fixed_location * TAU
    else:
        center = _find_spot(action.actual_size, 0.0, 1.0, false)
    return _spawn(action, center, charge)

## Секция впереди искры (доля оборота от min_turn до max_turn по ходу вращения).
func add_section_ahead(action: ActionData, min_turn: float, max_turn: float) -> Section:
    return _spawn(action, _find_spot(action.actual_size, min_turn, max_turn, true))

func _spawn(action: ActionData, center: float, charge: float = 0.0) -> Section:
    var s: Section = SECTION_SCENE.instantiate()
    s.data = action
    s.ring = self
    s.color = _color_for(action)
    s.center = center
    s.charge_time = charge
    s.pressed.connect(func() -> void: pressed.emit(s))
    s.expired.connect(func() -> void: expired.emit(s))
    if charge > 0.0:
        s.armed.connect(_on_section_armed.bind(s))
        s.fizzled.connect(func() -> void: telegraph_cancelled.emit(s))
    sections_root.add_child(s)
    if charge > 0.0:
        telegraph_started.emit(s)
    return s

func _on_section_armed(s: Section) -> void:
    _burst(s.center, s.color)
    _pulse = maxf(_pulse, 0.6)
    telegraph_armed.emit(s)

func _color_for(action: ActionData) -> Color:
    match action.kind:
        ActionData.Kind.ENEMY:
            return enemy_color
        ActionData.Kind.SEAL:
            return GOLD
    return CHALK

func _find_spot(size: float, min_turn: float, max_turn: float, ahead: bool) -> float:
    var options: Array[float] = []
    var dir: float = -1.0 if reversed else 1.0
    for i in 100:
        if ahead:
            options.append(pivot.rotation + dir * TAU * lerpf(min_turn, max_turn, i / 99.0))
        else:
            options.append(TAU * i / 100.0)
    options.shuffle()
    var live: Array[Section] = live_sections()
    for o in options:
        var ok: bool = true
        for other in live:
            if absf(angle_difference(o, other.center)) < 0.5 * (size + other.size) * TAU + 0.05:
                ok = false
                break
        if ok:
            return o
    push_warning("Ring: no free spot for section")
    return options[0]

func _burst(angle: float, color: Color) -> void:
    var b: Node2D = BURST_SCENE.instantiate()
    b.position = Vector2.RIGHT.rotated(angle) * RADIUS
    b.set(&"tint", color)
    fx_root.add_child(b)

func clear() -> void:
    for s in live_sections():
        s.die(false)

## Снять все боевые действия (между врагами).
func stop_combat() -> void:
    player_actions = []
    enemy_actions = []
    bonus_rps = 0.0
    frenzy = false
    clear()

func teleport(amount: float) -> void:
    pivot.rotation = fposmod(pivot.rotation + TAU * amount, TAU)
    _burst(pivot.rotation, GOLD)

func find_section(action: ActionData) -> Section:
    for s in live_sections():
        if s.data == action:
            return s
    return null

func remove_section(action: ActionData) -> void:
    for s in live_sections():
        if s.data == action:
            s.die(false)

func add_section_if_not_exist(action: ActionData) -> Section:
    var s: Section = find_section(action)
    if s:
        return s
    return add_section(action)

func spark_angle() -> float:
    return pivot.rotation

# ---------------- раны (2.5) ----------------
## Сколько трещин сейчас на черте (без залечивающихся). Должно совпадать с GameState.wound_count().
func crack_count() -> int:
    var n: int = 0
    for c in _cracks:
        if c.heal < 0.0:
            n += 1
    return n

## Подогнать трещины под GameState.wounds: новые раскрываются (animate) или сразу открыты, пропавшие — залечиваются.
## Список ран — стек (новые в конец, лечатся с конца), поэтому сверяем общий префикс.
func _sync_cracks(animate: bool) -> void:
    var gs: GameState = Globals.game_state
    gs.sync_wounds()
    var live: Array[Crack] = []
    for c in _cracks:
        if c.heal < 0.0:
            live.append(c)
    var same: int = 0
    while same < live.size() and same < gs.wounds.size() and is_equal_approx(live[same].angle, gs.wounds[same]):
        same += 1
    for i in range(same, live.size()):
        live[i].heal = 0.0
        if animate:
            cracks_healed += 1
            _burst(live[i].angle, GOLD)
            Audio.sfx(&"redraw", -4.0)
    for i in range(same, gs.wounds.size()):
        var c: Crack = Crack.new()
        c.angle = gs.wounds[i]
        c.open = 0.0 if animate else 1.0
        c.hot = 1.0 if animate else 0.0
        _cracks.append(c)
        if animate:
            cracks_opened += 1
            _chips(c.angle)
            Audio.sfx(&"crack", -5.0)

## Анимация трещин и отправка их в шейдер; низкое здоровье — черта краснеет и бьётся, как сердце.
func _update_cracks(delta: float) -> void:
    var angles: PackedFloat32Array = PackedFloat32Array()
    var opens: PackedFloat32Array = PackedFloat32Array()
    var hots: PackedFloat32Array = PackedFloat32Array()
    var heals: PackedFloat32Array = PackedFloat32Array()
    angles.resize(MAX_CRACKS)
    opens.resize(MAX_CRACKS)
    hots.resize(MAX_CRACKS)
    heals.resize(MAX_CRACKS)
    var n: int = 0
    for c in _cracks.duplicate():
        var amount: float
        var glow: float = 0.0
        if c.heal >= 0.0:
            c.heal += delta / CRACK_HEAL
            if c.heal >= 1.0:
                _cracks.erase(c)
                continue
            # Сначала вспыхивает золото, потом разрыв стягивается, золото гаснет последним.
            amount = 1.0 - smoothstep(0.15, 0.85, c.heal)
            glow = sin(PI * c.heal)
        else:
            c.open = minf(c.open + delta / CRACK_OPEN, 1.0)
            # Раскрытие с перехлёстом: черту рвёт чуть шире, чем остаётся.
            amount = (1.0 - pow(1.0 - c.open, 3.0)) * (1.0 + 0.25 * sin(PI * c.open))
        c.hot = move_toward(c.hot, 0.0, delta * 2.2)
        if n < MAX_CRACKS:
            angles[n] = c.angle
            opens[n] = amount
            hots[n] = c.hot
            heals[n] = glow
            n += 1
    var gs: GameState = Globals.game_state
    var target: float = 0.0
    if gs.health <= GameState.WOUND_STEP:
        target = 0.7
    elif gs.health <= 2.0 * GameState.WOUND_STEP:
        target = 0.35
    _danger = move_toward(_danger, target, delta * 1.5)
    _beat += delta
    var mat: ShaderMaterial = chalk.material as ShaderMaterial
    mat.set_shader_parameter(&"danger", _danger * (0.7 + 0.3 * maxf(0.0, sin(_beat * 7.0))))
    mat.set_shader_parameter(&"crack_count", n)
    mat.set_shader_parameter(&"crack_angle", angles)
    mat.set_shader_parameter(&"crack_open", opens)
    mat.set_shader_parameter(&"crack_hot", hots)
    mat.set_shader_parameter(&"crack_heal", heals)

## Сколы: куски мела и пыль из места раны, внутрь круга.
func _chips(angle: float) -> void:
    var c: Node2D = CHIPS_SCENE.instantiate()
    c.position = Vector2.RIGHT.rotated(angle) * RADIUS
    c.rotation = angle + PI
    fx_root.add_child(c)
