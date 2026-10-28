extends Node2D
class_name Section
## Секция на меловом круге. Сужается («догорает»), подсвечивается под искрой, лопается при нажатии.
## Замах (2.4): атака нечисти может сначала «заряжаться» (charge_time > 0): пунктирный контур, не нажимается
## и не догорает; потом вспыхивает (armed) и становится обычной секцией.

signal pressed
signal expired
## Заряд кончился — секция вспыхнула и теперь настоящая (2.4).
signal armed
## Секцию убрали, пока она заряжалась (отбили, конец боя) — замах сорвался (2.4).
signal fizzled

const TOOLTIP_R: float = 300.0
const HIT_SLACK: float = 0.05
## «Идеально» (2.2): искра не дальше чем в ~60 мс пути от центра…
const PERFECT_TIME: float = 0.06
## …и не дальше половины полуширины секции (иначе на больших секциях было бы слишком легко).
const PERFECT_SHARE: float = 0.5
const CHALK: Color = Color("efe6d2")
const CHALK_GLOW: Color = Color("ffcf8a")
const GOLD: Color = Color("ffd25a")
const GOLD_GLOW: Color = Color("fff1b0")

@export var data: ActionData
@export var center: float = 0.0:
    set(value):
        center = value
        if is_node_ready():
            _update_center()

var color: Color = CHALK
## Текущая ширина (доля оборота).
var size: float = 0.1
var hover: bool = false
var dead: bool = false
var label_override: String = ""
## «Идеально» (2.2): нажата точно по центру. Ставит Ring прямо перед press().
var perfect: bool = false
var ring: Ring
## Замах (2.4): сколько секунд секция заряжается перед появлением. Ставит Ring до add_child.
var charge_time: float = 0.0
var charging: bool = false

# Анимируемые свойства (AnimationPlayer → шейдер).
var grow: float = 0.0:
    set(value):
        grow = value
        _set_param(&"grow", value)
var flash: float = 0.0:
    set(value):
        flash = value
        _set_param(&"flash", value)
var warn: float = 0.0:
    set(value):
        warn = value
        _set_param(&"warn", value)
var fade: float = 1.0

var _mat: ShaderMaterial
var _active: float = 0.0
var _t: float = 0.0
var _charge_t: float = 0.0
var _icon_scale: float = 0.55  ## базовый масштаб иконки Печати из сцены (PNG нейросети может быть другого размера)

@onready var arc: ColorRect = $Arc
@onready var tooltip: Node2D = $Tooltip
@onready var label: Label = %Label
@onready var icon: Sprite2D = $Icon
@onready var anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    _mat = arc.material as ShaderMaterial
    _icon_scale = icon.scale.x
    size = data.actual_size
    var glow: Color = color.lightened(0.25)
    match data.kind:
        ActionData.Kind.PLAYER, ActionData.Kind.UI:
            glow = CHALK_GLOW
        ActionData.Kind.SEAL:
            glow = GOLD_GLOW
    _mat.set_shader_parameter(&"color", color)
    _mat.set_shader_parameter(&"glow_color", glow)
    _mat.set_shader_parameter(&"hot", 1.0 if data.kind == ActionData.Kind.ENEMY else (0.4 if data.kind == ActionData.Kind.SEAL else 0.0))
    _mat.set_shader_parameter(&"arc_size", TAU * size)
    _mat.set_shader_parameter(&"grow", grow)
    _mat.set_shader_parameter(&"flash", flash)
    _mat.set_shader_parameter(&"alpha", fade)
    _mat.set_shader_parameter(&"warn", warn)
    _mat.set_shader_parameter(&"charge", 0.0)
    label.modulate = color if data.kind != ActionData.Kind.UI else Color.WHITE
    icon.visible = data.kind == ActionData.Kind.SEAL
    set_text(label_override if label_override != "" else tr(data.text))
    charging = charge_time > 0.0
    anim.play(&"charge" if charging else &"in")

func set_text(t: String) -> void:
    label.text = t
    tooltip.visible = t != ""
    _update_center()

func _process(delta: float) -> void:
    if dead:
        _set_param(&"alpha", fade)
        return
    _t += delta
    if data.move_speed != 0.0:
        var dir: float = -1.0 if (ring and ring.reversed) else 1.0
        center = center - data.move_speed * delta * dir
    if charging:
        _charge_t += delta
        _set_param(&"charge", clampf(_charge_t / charge_time, 0.0, 1.0))
        _set_param(&"alpha", fade)
        if _charge_t >= charge_time:
            _arm()
        return
    var rate: float = shrink_rate()
    if rate > 0.0:
        size = maxf(size - rate * delta, 0.0)
        _set_param(&"arc_size", TAU * size)
        if size <= 0.0:
            expired.emit()
            die(false)
            return
    var a: float = fade
    if data.kind == ActionData.Kind.ENEMY and rate > 0.0 and size / data.actual_size < 0.35:
        a *= 0.6 + 0.4 * sin(_t * 38.0)
    _set_param(&"alpha", a)
    _active = move_toward(_active, 1.0 if hover else 0.0, delta * 10.0)
    _set_param(&"active", _active)
    _set_param(&"perfect_zone", perfect_tolerance())
    if icon.visible:
        icon.rotation += delta * 1.5
        icon.scale = Vector2.ONE * _icon_scale * (1.0 + 0.11 * sin(_t * 9.0)) * grow

func shrink_rate() -> float:
    if data.lifetime == ActionData.Lifetime.FOREVER:
        return 0.0
    return Globals.game_state.rps * data.actual_size / data.actual_lifetime

## Заряд кончился: секция вспыхивает (анимация «arm») и с этого кадра нажимается и догорает.
func _arm() -> void:
    charging = false
    _set_param(&"charge", 1.0)
    anim.play(&"arm")
    armed.emit()

## <0 — искра внутри секции (чем меньше, тем ближе к центру). Заряжающаяся секция (2.4) не задевается никогда.
func hit_distance(angle: float) -> float:
    if charging:
        return TAU
    return absf(angle_difference(angle, center)) - (0.5 * size * TAU + HIT_SLACK)

## «Идеально» бывает только у боевых секций (свой заговор и атака нечисти).
func can_be_perfect() -> bool:
    return data.kind == ActionData.Kind.PLAYER or data.kind == ActionData.Kind.ENEMY

## Полуширина зоны «Идеально» (рад): путь искры за PERFECT_TIME, но не больше PERFECT_SHARE половины секции.
## На быстрой искре окно по времени то же, на маленькой/догорающей секции — уже.
func perfect_tolerance() -> float:
    if ring == null or charging or not can_be_perfect():
        return 0.0
    return minf(ring.rps * TAU * PERFECT_TIME, 0.5 * size * TAU * PERFECT_SHARE)

func is_perfect(angle: float) -> bool:
    var tol: float = perfect_tolerance()
    return tol > 0.0 and absf(angle_difference(angle, center)) <= tol

func contains(angle: float) -> bool:
    return not dead and hit_distance(angle) < 0.0

func press() -> void:
    if dead:
        return
    # Сначала помечаем секцию мёртвой (die() синхронно ставит dead и запускает анимацию),
    # и только потом сообщаем о нажатии: обработчик может тут же вернуть такую же секцию на круг
    # (кнопки лавки/меню), и find_section() не должен находить уже нажатую.
    die(true)
    pressed.emit()

func die(by_press: bool = false) -> void:
    if dead:
        return
    dead = true
    hover = false
    if charging:
        charging = false
        fizzled.emit()
    anim.play(&"press" if by_press else &"expire")
    await anim.animation_finished
    queue_free()

func _set_param(param: StringName, value: Variant) -> void:
    if _mat:
        _mat.set_shader_parameter(param, value)

func _update_center() -> void:
    if not is_node_ready():
        return
    _set_param(&"center", center)
    var dir: Vector2 = Vector2.RIGHT.rotated(center)
    icon.position = dir * Ring.RADIUS
    if not tooltip.visible:
        return
    var ls: Vector2 = label.get_minimum_size()
    label.size = ls
    label.position = -ls * 0.5
    var r: float = TOOLTIP_R + 0.5 * ls.x * absf(dir.x) + 0.5 * ls.y * absf(dir.y)
    tooltip.position = dir * r
    # Не даём подписи вылезти за край экрана (узкий портрет).
    var inv: Transform2D = get_viewport().get_canvas_transform().affine_inverse()
    var vr: Rect2 = get_viewport().get_visible_rect()
    var tl: Vector2 = inv * vr.position
    var br: Vector2 = inv * vr.end
    var g: Vector2 = tooltip.global_position
    var hw: float = ls.x * 0.5 * global_scale.x + 14.0
    if br.x - tl.x > hw * 2.0:
        g.x = clampf(g.x, tl.x + hw, br.x - hw)
    tooltip.global_position = g
