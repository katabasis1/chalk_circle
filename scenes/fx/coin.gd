extends Node2D
class_name FlyCoin
## Монетка награды (2.6): вылетает из павшей нечисти веером, миг висит и по дуге летит в счётчик денег.
## Живёт в слое HUD (координаты холста — экран без камеры). Цель — Control (иконка монеты): её центр
## читаем каждый кадр, так что поворот экрана на лету не уводит монетку мимо.

signal arrived

## Разлёт веером (с), потом пауза (задаёт launch — монетки уходят по очереди), потом полёт в счётчик с разгоном.
const BURST_TIME: float = 0.28
const FLY_TIME: float = 0.5
## Насколько дуга полёта уходит вбок (доля расстояния).
const BEND: float = 0.3
## Монетка вертится: то плашмя, то ребром (оборотов в секунду).
const SPIN: float = 2.2

var _from: Vector2 = Vector2.ZERO
var _burst: Vector2 = Vector2.ZERO
var _fly_from: Vector2 = Vector2.ZERO
var _target: Control
var _last_to: Vector2 = Vector2.ZERO
var _delay: float = 0.0
var _bend: float = 0.0
var _spin0: float = 0.0
var _t: float = 0.0
var _flying: bool = false
var _done: bool = false
var _body_scale: Vector2 = Vector2.ONE

@onready var body: Sprite2D = %Body
@onready var glow: Sprite2D = %Glow

## from — откуда (холст), burst — куда разлететься (смещение от from), target — иконка счётчика,
## delay — сколько повисеть после разлёта перед полётом.
func launch(from: Vector2, burst: Vector2, target: Control, delay: float) -> void:
    _from = from
    _burst = from + burst
    _target = target
    _delay = delay
    _bend = randf_range(-1.0, 1.0)
    _spin0 = randf() * TAU
    position = from
    _target_point()

## Сразу в счётчик (панель спряталась — сменился экран): засчитать без полёта и исчезнуть.
func land() -> void:
    if _done:
        return
    _done = true
    arrived.emit()
    queue_free()

func _ready() -> void:
    _body_scale = body.scale
    scale = Vector2.ONE * 0.4

func _target_point() -> Vector2:
    if is_instance_valid(_target):
        _last_to = _target.get_global_rect().get_center()
    return _last_to

func _process(delta: float) -> void:
    if _done:
        return
    _t += delta
    # Плашмя ↔ ребром: ширина по |cos|, на ребре монетка темнее.
    var c: float = absf(cos(_spin0 + TAU * SPIN * _t))
    body.scale = Vector2(_body_scale.x * maxf(c, 0.12), _body_scale.y)
    body.modulate = Color.WHITE.darkened(0.35 * (1.0 - c))
    if _t < BURST_TIME:
        var k: float = 1.0 - pow(1.0 - _t / BURST_TIME, 3.0)
        position = _from.lerp(_burst, k)
        scale = Vector2.ONE * lerpf(0.4, 1.0, k)
        return
    var ft: float = _t - BURST_TIME - _delay
    if ft < 0.0:
        position = _burst + Vector2(0.0, 3.0 * sin(_t * 9.0 + _spin0))
        scale = Vector2.ONE
        return
    if not _flying:
        _flying = true
        _fly_from = position
    var k: float = minf(ft / FLY_TIME, 1.0)
    # Разгон к счётчику: медленно отрывается, быстро влетает.
    var e: float = k * k * (1.6 - 0.6 * k)
    var to: Vector2 = _target_point()
    var side: Vector2 = (to - _fly_from).orthogonal().normalized()
    var ctrl: Vector2 = (_fly_from + to) * 0.5 + side * _bend * _fly_from.distance_to(to) * BEND
    position = _fly_from.lerp(ctrl, e).lerp(ctrl.lerp(to, e), e)
    scale = Vector2.ONE * lerpf(1.0, 0.7, e)
    glow.modulate.a = lerpf(0.5, 0.9, e)
    if k >= 1.0:
        _done = true
        arrived.emit()
        queue_free()
