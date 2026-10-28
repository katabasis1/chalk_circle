extends Node2D
## Свеча у круга: мерцание из AnimationPlayer, каждая со своим сдвигом фазы.

@onready var anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    anim.speed_scale = randf_range(0.8, 1.25)
    anim.seek(randf() * 1.7, true)
