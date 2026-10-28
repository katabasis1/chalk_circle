extends Node2D
## Всплывающая надпись (урон, «Печать!», «Мимо»). Анимация — в pop.tscn.

const LS_NORMAL: LabelSettings = preload("res://assets/ui/ls_pop.tres")
const LS_SMALL: LabelSettings = preload("res://assets/ui/ls_pop_small.tres")
const LS_BIG: LabelSettings = preload("res://assets/ui/ls_pop_big.tres")

@export var text: String = ""
@export var small: bool = false
@export var big: bool = false

@onready var label: Label = %Label
@onready var anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    label.text = text
    label.label_settings = LS_BIG if big else (LS_SMALL if small else LS_NORMAL)
    rotation = randf_range(-0.12, 0.12)
    position += Vector2(randf_range(-10.0, 10.0), randf_range(-6.0, 6.0))
    anim.play(&"pop_big" if big else &"pop")
    await anim.animation_finished
    queue_free()
