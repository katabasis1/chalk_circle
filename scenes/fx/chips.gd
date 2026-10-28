extends Node2D
## Сколы мела (2.5): куски черты, пыль и угольки из места раны. Одноразово; ring.gd ставит узел на черту
## и поворачивает +X внутрь круга.

func _ready() -> void:
    for c in get_children():
        (c as CPUParticles2D).emitting = true
    ($Shards as CPUParticles2D).finished.connect(queue_free)
