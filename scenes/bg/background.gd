extends CanvasLayer
class_name Background
## Фон: болото, туман, тонировка под настроение экрана.

## Порядок как в Main.State: MENU, FIGHT, SHOP, BOSS, END, VICTORY.
const TINTS: Array[Color] = [
    Color(0.02, 0.05, 0.08, 0.15),
    Color(0.22, 0.02, 0.05, 0.22),
    Color(0.35, 0.18, 0.04, 0.18),
    Color(0.35, 0.0, 0.02, 0.42),
    Color(0.0, 0.0, 0.0, 0.5),
    Color(0.45, 0.32, 0.12, 0.12),
]
const FOG: Array[Color] = [
    Color(0.55, 0.66, 0.62),
    Color(0.6, 0.55, 0.55),
    Color(0.7, 0.6, 0.45),
    Color(0.6, 0.25, 0.28),
    Color(0.4, 0.4, 0.42),
    Color(0.85, 0.75, 0.6),
]

@onready var tint: ColorRect = $Tint
@onready var fog: ColorRect = $Fog

func set_mood(state: int) -> void:
    var i: int = clampi(state, 0, TINTS.size() - 1)
    var tw: Tween = create_tween().set_parallel()
    tw.tween_property(tint, "color", TINTS[i], 0.6)
    var mat: ShaderMaterial = fog.material as ShaderMaterial
    var from: Color = mat.get_shader_parameter(&"fog_color")
    tw.tween_method(func(c: Color) -> void: mat.set_shader_parameter(&"fog_color", c), from, FOG[i], 0.6)
