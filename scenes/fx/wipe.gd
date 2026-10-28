extends CanvasLayer
class_name Wipe
## Чернильная клякса между экранами: cover() → covered, reveal(title) → done.

signal covered
signal done

var progress: float = 0.0:
    set(value):
        progress = value
        if is_node_ready():
            (rect.material as ShaderMaterial).set_shader_parameter(&"progress", value)
            rect.visible = value > 0.001 and value < 1.999

@onready var rect: ColorRect = $Rect
@onready var title: Label = %Title
@onready var anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    progress = 0.0
    title.modulate.a = 0.0

func cover() -> void:
    title.modulate.a = 0.0
    anim.play(&"cover")
    await anim.animation_finished
    covered.emit()

func reveal(text: String) -> void:
    title.text = text
    title.pivot_offset = title.size * 0.5
    anim.play(&"reveal")
    await anim.animation_finished
    progress = 0.0
    done.emit()
