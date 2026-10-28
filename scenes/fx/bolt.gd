extends Node2D
class_name Bolt
## Меловой снаряд (2.3): удар летит от секции на круге к нечисти по дуге и на месте шлёт landed.
## Точка цели (Enemy.hit_point) пересчитывается каждый кадр — нечисть парит и трясётся.
## Хвост — Line2D: точки копятся в мировых координатах и каждый кадр переводятся в локальные (голова вертится).
## Так хвост плавный при любой скорости, в отличие от частиц.

signal landed

## Скорость (px/с) и пределы времени полёта: удар должен «долететь», но не тормозить бой.
const SPEED: float = 3200.0
const MIN_TIME: float = 0.12
const MAX_TIME: float = 0.22
## Длина хвоста (точек) и сколько точек добавлять за кадр (по кривой — без изломов).
const TRAIL_POINTS: int = 22
const TRAIL_STEPS: int = 3

@export var tint: Color = Color("efe6d2")
## Крупный удар (≥15 урона или «Идеально»): толще и ярче.
@export var heavy: bool = false

## Откуда (мировые координаты) и в кого. Задать до add_child.
var from: Vector2 = Vector2.ZERO
var target: Enemy
## Обогнуть круг радиуса avoid_r вокруг avoid (центр круга с числом здоровья); 0 — лететь как есть.
var avoid: Vector2 = Vector2.ZERO
var avoid_r: float = 0.0

var _to: Vector2 = Vector2.ZERO
var _bend: Vector2 = Vector2.ZERO
var _time: float = 0.15
var _t: float = 0.0
var _k: float = 0.0
var _done: bool = false
var _linger: float = 0.0
var _pts: PackedVector2Array = PackedVector2Array()

@onready var trail: Line2D = %Trail
@onready var dust: CPUParticles2D = %Dust
@onready var glow: Sprite2D = %Glow
@onready var core: Sprite2D = %Core

func _ready() -> void:
    global_position = from
    _to = _target_point()
    var dist: float = from.distance_to(_to)
    _time = clampf(dist / SPEED, MIN_TIME, MAX_TIME)
    # Дуга: контрольная точка кривой сбоку от прямой. Гнём в сторону от avoid и так, чтобы вершина
    # дуги (половина изгиба от середины хорды) обошла круг avoid_r — снаряд не перечёркивает число здоровья.
    var side: Vector2 = (_to - from).orthogonal().normalized()
    var bend_len: float = dist * randf_range(0.16, 0.3)
    var side_k: float = 1.0 if randf() < 0.5 else -1.0
    if avoid_r > 0.0:
        var off: float = ((from + _to) * 0.5 - avoid).dot(side)
        if absf(off) > 1.0:
            side_k = signf(off)
        bend_len = maxf(bend_len, 2.0 * (avoid_r - absf(off)))
    _bend = side * bend_len * side_k
    var k: float = 1.4 if heavy else 1.0
    glow.modulate = Color(tint, 0.9)
    glow.scale *= k
    core.scale *= k
    trail.modulate = tint
    trail.width *= k
    _pts.append(from)
    _sync_trail()
    dust.color = tint
    dust.emitting = true
    _linger = dust.lifetime

func _process(delta: float) -> void:
    if _done:
        _fade(delta)
        return
    if is_instance_valid(target):
        _to = _target_point()
    var prev: float = _k
    _t = minf(_t + delta / _time, 1.0)
    _k = ease(_t, 1.5)  # разгон к цели: удар «впечатывается»
    for i in range(1, TRAIL_STEPS + 1):
        _pts.append(_curve(lerpf(prev, _k, float(i) / TRAIL_STEPS)))
    if _pts.size() > TRAIL_POINTS:
        _pts = _pts.slice(_pts.size() - TRAIL_POINTS)
    var p: Vector2 = _curve(_k)
    var vel: Vector2 = p - global_position
    if vel.length_squared() > 0.01:
        rotation = vel.angle()
    global_position = p
    _sync_trail()
    if _t >= 1.0:
        _land()

func _sync_trail() -> void:
    trail.points = trail.get_global_transform().affine_inverse() * _pts

func _curve(k: float) -> Vector2:
    var mid: Vector2 = (from + _to) * 0.5 + _bend
    return from.lerp(mid, k).lerp(mid.lerp(_to, k), k)

func _target_point() -> Vector2:
    return target.hit_point() if is_instance_valid(target) else _to

func _land() -> void:
    _done = true
    glow.visible = false
    core.visible = false
    dust.emitting = false
    landed.emit()

## После попадания хвост втягивается в точку удара и гаснет, крошки мела досыпаются.
func _fade(delta: float) -> void:
    if _pts.size() > 1:
        _pts = _pts.slice(mini(2, _pts.size() - 1))
        _sync_trail()
    trail.modulate.a = move_toward(trail.modulate.a, 0.0, delta * 6.0)
    _linger -= delta
    if _linger <= 0.0:
        queue_free()
