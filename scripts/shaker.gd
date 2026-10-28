extends Node
class_name Shaker
## Тряска и плавное «парение» родителя (Node2D, Control или Camera2D).

@export var float_amount: float = 0.0
@export var float_rate: float = 0.35
@export var float_x: float = 0.0

var _time: float = 0.0
var _amount: float = 0.0
var _left: float = 0.0
var _origin: Vector2
var _parent: Node

func _ready() -> void:
    _parent = get_parent()
    _time = randf() * 10.0
    if _parent is Camera2D:
        _origin = (_parent as Camera2D).offset
    elif _parent is Node2D:
        _origin = (_parent as Node2D).position
    elif _parent is Control:
        _origin = (_parent as Control).position

func _process(delta: float) -> void:
    _time += delta
    var off: Vector2 = Vector2(
        float_x * sin(TAU * _time * float_rate * 0.5),
        float_amount * sin(TAU * _time * float_rate + PI / 4.0))
    if _left > 0.0:
        var k: float = _left / maxf(_left + delta, 0.0001)
        off += Vector2(randf_range(-_amount, _amount), randf_range(-_amount, _amount)) * k
        _left = maxf(_left - delta, 0.0)
        if _left <= 0.0:
            _amount = 0.0
    _apply(off)

func _apply(off: Vector2) -> void:
    if not is_instance_valid(_parent):
        return
    if _parent is Camera2D:
        (_parent as Camera2D).offset = _origin + off
    elif _parent is Node2D:
        (_parent as Node2D).position = _origin + off
    elif _parent is Control:
        (_parent as Control).position = _origin + off

func shake(amount: float, time: float) -> void:
    _amount = maxf(_amount, amount)
    _left = maxf(_left, time)

func reset() -> void:
    _amount = 0.0
    _left = 0.0

## Обновить «ноль» (если родителя передвинули).
func rebase() -> void:
    _ready()
