extends CPUParticles2D
## Одноразовый сноп искр. tint задаёт цвет до добавления в дерево.

@export var tint: Color = Color.WHITE

func _ready() -> void:
    color = tint
    emitting = true
    finished.connect(queue_free)
